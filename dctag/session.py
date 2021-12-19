"""Handle DCTag sessions

A session in DCTag is nothing else than an .rtdc file. You
open an .rtdc file and DCTag automatically determines which
machine-learning features have previously been analyzed and
what could possibly happen next.
"""
import threading
import time
import pathlib
import warnings

import dclab
import h5py
import numpy as np

from ._version import version


class DCTagSessionClosedWarning(UserWarning):
    pass


class DCTagSessionError(BaseException):
    pass


class DCTagSessionClosedError(DCTagSessionError):
    pass


class DCTagSessionLockedError(DCTagSessionError):
    """Cannot load the session, because it is locked by another process"""


class DCTagSessionWriteError(DCTagSessionError):
    """Raised when it is not possible to write to a session"""


class DCTagSessionWrongUserError(DCTagSessionError):
    """Raised when the session user does not match"""


class DCTagSession:
    def __init__(self, path, user, linked_features=None):
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
        linked_features: list of str
            List for "ml_scores_" features that should be treated as
            linked when writing scores to disk. E.g. if you have the
            linked features 'ml_score_rbc' and 'ml_score_wbc', then
            the followin applies:

            - Setting the score of 'rbc' to True implies that the score
              of 'wbc' is False.
            - However, setting the score of 'rbc' to False, does not
              imply that the score of 'wbc' is True.

            Thus, if you are using this feature for labeling multiple
            scores, make sure to always only set True scores (so the
            other scores get set to False).

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
        #: Session path
        self.path = pathlib.Path(path)
        #: Lock-file for this session
        self.path_lock = self.path.with_suffix(".dctag")
        if self.path_lock.exists():
            raise DCTagSessionLockedError(
                f"Somebody else is currently working on {self.path} or "
                + "DCTag exited unexpectedly in a previous run! Please ask "
                + "Paul to implement session recovery!")
        #: Session user
        self.user = user.strip()
        #: scoring features that are linked for labeling
        self.linked_features = linked_features or []
        # claim this file
        with h5py.File(self.path, "a") as h5:
            if "dctag-history" in h5.require_group("logs"):
                h5userstr = h5["logs"]["dctag-history"][0]
                if isinstance(h5userstr, bytes):
                    h5userstr = h5userstr.decode("utf-8")
                h5user = h5userstr.split(":")[1].strip()
                if h5user != self.user:
                    raise DCTagSessionWrongUserError(
                        f"Expected user '{self.user}' in '{self.path}', but "
                        + f"got '{h5user}'!")
            else:
                with dclab.RTDCWriter(h5) as hw:
                    hw.store_log("dctag-history", f"user: {self.user}")
            # While we are at it, note down the linked features in this
            # particular session.
            with dclab.RTDCWriter(h5) as hw:
                hw.store_log(
                    "dctag-history",
                    [time.strftime("new session at %Y-%m-%d %H:%M:%S"),
                     f"DCTag {version}",
                     f"linked features: {self.linked_features}",
                     ])
        # determine length of the dataset
        with dclab.new_dataset(self.path) as ds:
            #: Number of events in the dataset
            self.event_count = len(ds)
        #: The internal scores cache is a dict with numpy arrays to keep
        #: track of all the scores for internal use only. This is not used
        #: for writing scores to .rtdc files. The scores cache is important
        #: for being able to keep working on a dataset when the underlying
        #: path is temporarily not available.
        self.scores_cache = {}
        with h5py.File(self.path, "a") as h5:
            # initialize advertised scores in the .rtdc file
            for feat in self.linked_features:
                self.require_h5_score_dataset(h5, feat)
            # make a copy of all available scores in self.scores_cache
            for feat in h5["events"]:
                if feat.startswith("ml_score_"):
                    self.scores_cache[feat] = np.copy(h5["events"][feat])
        #: Lock used internally to avoid writing to `history` and `scores`
        #: while saving data in `flush`
        self.score_lock = threading.Lock()
        #: simple key-value dictionary of the current session history
        self.history = {}
        #: list of (feature, index, score) in the order set by the user
        self.scores = []

        # finally, acquire the file system lock
        self.path_lock.touch()
        # keep track of whether we still have an open session
        self._closed = False

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def assert_session_open(self, purpose="perform an undefined task",
                            strict=False):
        """Warn or raise an error if the session is closed

        Parameters
        ----------
        purpose: str
            Describe why you need the session open; used for debugging.
        strict: bool
            Whether to force raising a DCTagSessionClosedError; otherwise
            a DCTagSessionClosedWarning may be raised in situations where
            `self.history` or `self.scores` are empty.
        """
        if self._closed:
            if self.history or self.scores or strict:
                raise DCTagSessionClosedError(
                    "The session has been closed, but there are still data to "
                    + f"be written to '{self.path}'! Cannot {purpose}.",)
            else:
                warnings.warn(
                    "Session has been closed, but you are trying to "
                    + f"{purpose} which requires an open session. Luckily, "
                    + "there is nothing that needs to be written to disk, but "
                    + "you should try to avoid this anyway.",
                    DCTagSessionClosedWarning)

    def close(self):
        """Close this session, flushing everything to `self.path`"""
        self.flush()
        with self.score_lock:
            # call this function in the score_lock context again to
            # be on the safe side.
            self.assert_session_open("close the session")
            self._closed = True
            self.path_lock.unlink(missing_ok=True)

    def flush(self):
        """Flush all changes made to disk

        You should call this method regularly. It is thread-safe,
        so you may call it in regular intervals using a background
        thread.
        """
        with self.score_lock:
            self.assert_session_open("flush the session")
            try:
                self.write_scores(clear_scores=True)
                self.write_history(clear_history=True)
            except BaseException as exc:
                raise DCTagSessionWriteError(
                    f"Could not write to session {self.path}!") from exc

    def get_score(self, feature, index):
        """Return the score of a specific feature at that index

        Parameters
        ----------
        feature: str
            Name of the machine-learning feature (e.g. "ml_score_buk")
        index: int
            Event index (starts at 0)

        Returns
        -------
        score: bool or np.nan
            The score value (nan if not defined)

        Notes
        -----
        This method is thread-safe.
        """
        # We use the score cache for that
        with self.score_lock:
            self.assert_session_open(f"get the score {feature} at {index}")
            if feature not in self.scores_cache:
                value = np.nan
            else:
                value = self.scores_cache[feature][index]
                if not np.isnan(value):
                    value = bool(round(value))
            return value

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
        if (not feature.startswith("ml_score_") or
                len(feature) != len("ml_score_???")):
            raise ValueError(
                f"Expected 'ml_score_xxx' feature, got '{feature}'!")
        with self.score_lock:
            self.assert_session_open(f"set the score {feature} at {index}",
                                     strict=True)
            # scores list
            self.scores.append((feature, index, value))

            # history list
            # (Note that this count value may be larger than the actual
            # updated number of events of the ml_score, because `feat_list`
            # may have multiple entries with the same index. This is OK).
            key = f"{feature} count {value}"
            self.history.setdefault(key, 0)
            self.history[key] += 1

            # internal score cache
            if feature not in self.scores_cache:
                self.scores_cache[feature] \
                    = np.zeros(self.event_count, dtype=float) * np.nan
            self.scores_cache[feature][index] = value
            self.populate_linked_features(
                feature=feature,
                index=index,
                value=value,
                linked_feature_dict=self.scores_cache)

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
                    "dctag-history",
                    time.strftime(
                        f".Update at %Y-%m-%d %H:%M:%S ({self.user})"))
                for key in sorted(self.history.keys()):
                    hw.store_log("dctag-history",
                                 f"..{key}: {self.history[key]}")
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
                for feat, idx, val in self.scores:
                    sc_ds = self.require_h5_score_dataset(h5, feat)
                    sc_ds[idx] = val
                    # Write False to the other linked features
                    self.populate_linked_features(
                        feature=feat,
                        index=idx,
                        value=val,
                        linked_feature_dict=h5["events"])

            if clear_scores:
                self.scores.clear()

    def require_h5_score_dataset(self, h5, feature):
        """Return dataset in the `h5["events"]` group for `feature`"""
        if feature not in h5["events"]:
            # create a nan-filled dataset for this feature
            data = np.zeros(self.event_count, dtype=float) * np.nan
            h5["events"].create_dataset(feature, data=data)
        return h5["events"][feature]

    def populate_linked_features(self, feature, index, value,
                                 linked_feature_dict):
        """Set values in linked_feature_dict to False if value is True

        Notes
        -----
        We assume that all `self.linked_features` are in
        `linked_feature_dict`. This is done during `__init__`.
        """
        if value is True and feature in self.linked_features:
            for feat in self.linked_features:
                if feat != feature:
                    ln_sc_ds = linked_feature_dict[feat]
                    ln_sc_ds[index] = False
