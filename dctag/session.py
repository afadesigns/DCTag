"""Handle DCTag sessions

A session in DCTag is nothing else than an .rtdc file. You
open an .rtdc file and DCTag automatically determines which
machine-learning features have previously been analyzed and
what could possibly happen next.
"""
import threading
import time
import pathlib

import dclab
import h5py
import numpy as np


class SessionLockedError(BaseException):
    """Cannot load the session, because it is locked by another process"""


class SessionWriteError(BaseException):
    """Raised when it is not possible to write to a session"""


class DCTagSession:
    def __init__(self, path, user):
        """Initialize a DCTag session

        Parameters
        ----------
        path: str or pathlib.Path
            Path to an .rtdc file used for labeling
        user: str
            Unique string (e.g. "Bambi") that identifies a user;
            The input file `path` will be bound to that username,
            making it impossible to edit the same .rtdc file using
            a different username.

        Notes
        -----
        Upon initialization this class creates a .dctag file with the
        same file name stem as `path` to indicate that a DCTag session
        is in progress. This can be thought of as a file lock. It is a
        precaution to prevent two people from working on the same file
        at the same time.

        The methods that alter the .rtdc file in this class are
        thread-safe (using `self.score_lock`).

        The design makes sure that the user can still write to the
        original .rtdc file, even if e.g. the original file is on a
        network share that has been remounted during rating.
        """
        self.path = pathlib.Path(path)
        self.path_lock = self.path.with_suffix("dctag")
        self.user = user.strip()
        # determine length of the dataset
        with dclab.new_dataset(self.path) as ds:
            #: Number of events in the dataset
            self.event_count = len(ds)
        #: Lock used internally to avoid writing to `history` and `scores`
        #: while saving data in `flush`
        self.score_lock = threading.Lock()
        #: simple key-value dictionary of the current session history
        self.history = {}
        #: keys are `ml_score_` features and values are tuples of
        #: (index, score).
        self.scores = {}

        if self.path_lock.exists():
            raise SessionLockedError(
                f"Somebody else is currently working on {self.path} or "
                + "DCTag exited unexpectedly in a previous run! Please ask "
                + "Paul to implement session recovery!")

    def __enter__(self):
        return self

    def __exit__(self, tb, e, t, c):
        self.flush()

    def flush(self):
        """Flush all changes made to disk

        You should call this method regularly. It is thread-safe,
        so you may call it in regular intervals using a background
        thread.
        """
        with self.score_lock:
            try:
                self.write_scores(clear_scores=True)
                self.write_history(clear_history=True)
            except BaseException:
                raise SessionWriteError(
                    f"Could not write to session {self.path}!")

    def set_score(self, feature, index, value):
        """Set the feature score of an event in the current dataset

        Parameters
        ----------
        feature: str
            Name of the machine-learning feature (e.g. "ml_score_buk")
        index: int
            Event index (starts at 0)
        value: bool
            Boolean value indicating whether the event
            belongs to the `feature` class

        Notes
        -----
        This method is thread-safe.
        """
        assert feature.startswith("ml_score_")
        assert len(feature) == len("ml_score_???")
        with self.score_lock:
            # scores
            feat_list = self.scores.setdefault(feature, [])
            feat_list.append((index, value))
            # history
            key = f"{feature} count {value}"
            self.history.setdefault(key, 0)
            self.history[key] += 1

    def write_history(self, clear_history=False):
        """Write accomplishments to the history log in `self.path`

        The history log is a human-readable summary of the changes
        made in a session.

        Parameters
        ----------
        clear_history: bool
            Whether to clear `self.history`. Only set to True if you
            have previously acquired `self.score_lock`!

        Notes
        -----
        This method is NOT thread-safe. Use `self.flush` instead!
        """
        if self.history:
            with dclab.RTDCWriter(self.path, mode="append") as hw:
                hw.store_log(
                    time.strftime(
                        f"DCTag history %Y-%m-%d %H:%M:%S for '{self.user}'"))
                for key in sorted(self.history.keys()):
                    hw.store_log(f" {key}: {self.history[key]}")
            if clear_history:
                # clear history
                self.history.clear()

    def write_scores(self, clear_scores=False):
        """Write the machine-learning scores to `self.path`


        Parameters
        ----------
        clear_scores: bool
            Whether to clear `self.scores`. Only set to True if you
            have previously acquired `self.score_lock`!

        Notes
        -----
        This method is NOT thread-safe. Use `self.flush` instead!
        """
        if self.scores:
            with h5py.File(self.path, mode="a") as h5:
                for feat in self.scores:
                    if feat not in h5["events"]:
                        # create a nan-filled dataset for this feature
                        data = np.zeros(self.event_count, dtype=float) * np.nan
                        h5["events"].create_dataset(feat, data=data)
                    for (idx, val) in self.scores[feat]:
                        h5["events"][feat][idx] = val
            if clear_scores:
                self.scores.clear()
