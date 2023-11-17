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
    def __init__(self, olduser, *args):
        self.olduser = olduser
        super(DCTagSessionWrongUserError, self).__init__(*args)


class DCTagSession:
    def __init__(self, path, user, linked_features=None, override_user=False):
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
        override_user: bool
            Whether to override the `user` stored in the session.

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
        #: Lock used internally to avoid writing to `history` and `scores`
        #: while saving data in `flush`
        self.score_lock = threading.Lock()
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
        # Whether session info has been written to the dctag-history log
        self._session_info_in_log_up_to_date = False
        # list of linked features (see self.linked_features)
        self._linked_features = []
        # claim this file
        self._claim_path(override_user=override_user)
        #: simple key-value dictionary of the current session history
        self.history = {}
        #: list of (feature, index, score) in the order set by the user
        self.scores = []
        #: scoring features that are linked for labeling
        self.linked_features = linked_features
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
            # make a copy of all available scores in self.scores_cache
            for feat in h5["events"]:
                if feat.startswith("ml_score_") or feat.startswith("userdef"):
                    self.scores_cache[feat] = np.copy(h5["events"][feat])

        # finally, acquire the file system lock
        self.path_lock.touch()
        # keep track of whether we still have an open session
        self._closed = False

    def __bool__(self):
        """Convenience function; allows you to use `if session` case"""
        return not self._closed

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def _claim_path(self, override_user=False):
        """Attribute this file to self.user"""
        with h5py.File(self.path, "a") as h5:
            hw = dclab.RTDCWriter(h5, mode="append")
            h5.require_group("logs")
            dctag_history = "dctag-history"
            if len(h5["logs"].get(dctag_history, ["placeholder"])) == 0:
                # remove empty logs
                del h5["logs"][dctag_history]

            if dctag_history not in h5["logs"]:
                hw.store_log(dctag_history, f"user: {self.user}")
            else:
                # Check whether the user in the file matches us
                h5userstr = h5["logs"][dctag_history][0]
                if isinstance(h5userstr, bytes):
                    h5userstr = h5userstr.decode("utf-8")
                if h5userstr.startswith("user:"):
                    h5user = h5userstr.split(":")[1].strip()
                    if h5user != self.user:
                        if override_user:
                            h5["logs"][dctag_history][0] = f"user: {self.user}"
                            hw.store_log(dctag_history,
                                         f"Session force-claimed from "
                                         f"{h5user} by {self.user}.")
                        else:
                            raise DCTagSessionWrongUserError(
                                h5user,
                                f"Expected user '{self.user}' in "
                                + f"'{self.path}', got '{h5user}'!")
                else:
                    # Something went wrong (maybe lost history).
                    # Reinstate the claim!
                    h5["logs"]["dctag-history"][0] = f"user: {self.user}"

    @property
    def linked_features(self):
        return self._linked_features

    @linked_features.setter
    def linked_features(self, linked_features):
        # Acquire a score_lock, because labeling might go on
        # in another thread, and we want the correct history.
        with self.score_lock:
            linked_features = linked_features or []
            if self._linked_features == linked_features:
                # nothing to do
                pass
            else:
                # write the scores and history now
                self.write_history(clear_history=True)
                self.write_scores(clear_scores=True)
                # make sure the session info is written to the logs
                # in the next call to self.write_history
                self._session_info_in_log_up_to_date = False
                # finally, set the linked features internally
                self._linked_features = sorted(linked_features)

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

    def autocomplete_linked_features(self):
        """Autocomplete False for linked features"""
        with self.score_lock:
            # Create a concatenated array with all current scores
            fscores = np.zeros((self.event_count, len(self.linked_features)),
                               dtype=float)
            for ii, feat in enumerate(self.linked_features):
                fscores[:, ii] = self.require_dict_score_dataset(
                    self.scores_cache, feat)
            # Sanity check
            if np.any(np.nansum(fscores, axis=1) > 1):
                raise ValueError(
                    f"Some of the scores {self.linked_features} in "
                    + f"{self.path} have ambiguous labels! Make sure that "
                    + "always only one of those scores is labeled as True/Yes."
                    )
            # We are safe
            for ii, feat in enumerate(self.linked_features):
                mask_true = self.scores_cache[feat] == 1
                for other_feat in self.linked_features:
                    if other_feat != feat:
                        mask_nan = np.isnan(self.scores_cache[other_feat])
                        idx_new = np.where(
                            np.logical_and(mask_true, mask_nan))[0]
                        for idx in idx_new:
                            self.scores.append((other_feat, idx, False))
                            self.scores_cache[other_feat][idx] = False

    def backup_scores(self, path):
        """Backup current scores in an HDF5 file

        This can be used as a last resort to save score data if
        the original `self.path` has gone away for some reason.
        """
        with h5py.File(path, mode="w") as h5:
            with self.score_lock:
                for feat in self.scores_cache:
                    h5[feat] = self.scores_cache[feat]
                h5.attrs["path_original"] = str(self.path)

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

    def get_scores_true(self, index):
        """Return the feature names that are labeld True for one event

        Parameters
        ----------
        index: int
            Event index (starts at 0)

        Returns
        -------
        features: list of str
            Feature names
        """
        true_features = []
        for feature in self.scores_cache:
            if self.get_score(feature, index) is True:
                true_features.append(feature)
        return sorted(true_features)

    def reset_score(self, feature, index, reset_linked=True):
        """Set the score at `index` to `np.nan`

        Parameters
        ----------
        feature: str
            Name of the machine-learning feature (e.g. "ml_score_buk")
        index: int
            Event index (starts at 0)
        reset_linked: bool
            Also reset all linked features if `feature` in
            `self.linked_features`.
        """
        if reset_linked and feature in self.linked_features:
            # Recurse one level and reset all features
            for feat in self.linked_features:
                self.reset_score(feat, index, reset_linked=False)
        else:
            # Do the actual resetting
            with self.score_lock:
                self.assert_session_open(
                    f"reset the score {feature} at {index}", strict=True)
                # scores list
                self.scores.append((feature, index, np.nan))

                # history list
                # (Note that this count value may be larger than the actual
                # updated number of events of the ml_score, because `feat_list`
                # may have multiple entries with the same index. This is OK).
                key = f"{feature} count reset"
                self.history.setdefault(key, 0)
                self.history[key] += 1

                self.require_dict_score_dataset(self.scores_cache, feature)
                self.scores_cache[feature][index] = np.nan

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
        if (not (feature.startswith("userdef")
                 or (feature.startswith("ml_score_") and
                     len(feature) == len("ml_score_???")))):
            raise ValueError(
                "Expected 'ml_score_xxx' or 'userdef*' feature, "
                + f"got '{feature}'!")
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

            for feat in self.linked_features:
                self.require_dict_score_dataset(self.scores_cache, feat)
            self.require_dict_score_dataset(self.scores_cache, feature)

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
            date = time.strftime("%Y-%m-%d %H:%M:%S")
            with dclab.RTDCWriter(self.path, mode="append") as hw:
                if not self._session_info_in_log_up_to_date:
                    hw.store_log(
                        "dctag-history",
                        ["",
                         f"{date} New session with DCTag {version}",
                         f"{date} Linked features: {self.linked_features}"
                         ])
                for key in sorted(self.history.keys()):
                    hw.store_log("dctag-history",
                                 f"{date} {key}: {self.history[key]}")
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
            with h5py.File(self.path, mode="r+") as h5:
                # make sure that all linked features are available
                for feat in self.linked_features:
                    self.require_h5_score_dataset(h5, feat)
                # populate features
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

    def require_dict_score_dataset(self, ndict, feature):
        """Return dataset in `ndict` for `feature`"""
        # internal score cache
        if feature not in ndict:
            ndict[feature] = np.zeros(self.event_count, dtype=float) * np.nan
        return ndict[feature]

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


def is_dctag_session(path):
    """Return True if `path` has a dctag-history log"""
    with h5py.File(path, "r") as h5:
        return "logs/dctag-history" in h5
