import pytest

import dclab
import numpy as np

from dctag import session

from helper import get_clean_data_path


def test_basic():
    path = get_clean_data_path()
    with session.DCTagSession(path, "Peter") as dts:
        assert dts.event_count == 18
        lock_path = dts.path_lock
        assert lock_path.exists()
    assert not lock_path.exists()


def test_session_locked_error():
    path = get_clean_data_path()
    lock_path = path.with_suffix(".dctag")
    lock_path.touch()
    # make sure the session cannot be opened if it is locked
    with pytest.raises(session.SessionLockedError, match=f"{path}"):
        with session.DCTagSession(path, "Peter"):
            pass
    # make sure the lock file is not removed by context manager
    assert lock_path.exists()


def test_flush_with_missing_file_error():
    path = get_clean_data_path()
    # error should be raised on flush and on __exit__
    with pytest.raises(session.SessionWriteError, match=f"{path}"):
        with session.DCTagSession(path, "Peter") as dts:
            dts.set_score("ml_score_abc", 0, True)
            path.unlink()
            with pytest.raises(session.SessionWriteError, match=f"{path}"):
                dts.flush()


def test_get_score_basic():
    path = get_clean_data_path()
    with session.DCTagSession(path, "Peter") as dts:
        dts.set_score("ml_score_abc", 0, True)
        dts.set_score("ml_score_abc", 2, False)
        dts.set_score("ml_score_abc", 1, True)

        assert dts.get_score("ml_score_abc", 0) is True
        assert dts.get_score("ml_score_abc", 1) is True
        assert dts.get_score("ml_score_abc", 2) is False
        assert np.isnan(dts.get_score("ml_score_abc", 3))
        assert np.isnan(dts.get_score("ml_score_ukn", 3))

    # again in new session
    with session.DCTagSession(path, "Peter") as dts:
        assert dts.get_score("ml_score_abc", 0) is True
        assert dts.get_score("ml_score_abc", 1) is True
        assert dts.get_score("ml_score_abc", 2) is False
        assert np.isnan(dts.get_score("ml_score_abc", 3))
        assert np.isnan(dts.get_score("ml_score_ukn", 3))


def test_get_score_linked():
    path = get_clean_data_path()
    with session.DCTagSession(
            path,
            "Peter",
            linked_features=["ml_score_abc", "ml_score_123"]) as dts:
        dts.set_score("ml_score_abc", 0, True)
        dts.set_score("ml_score_abc", 2, False)
        dts.set_score("ml_score_abc", 1, True)
        dts.set_score("ml_score_123", 3, True)
        dts.set_score("ml_score_000", 4, True)
        dts.set_score("ml_score_123", 5, False)

        assert dts.get_score("ml_score_abc", 0) is True
        assert dts.get_score("ml_score_abc", 1) is True
        assert dts.get_score("ml_score_abc", 2) is False
        assert dts.get_score("ml_score_abc", 3) is False
        assert np.isnan(dts.get_score("ml_score_abc", 4))
        assert np.isnan(dts.get_score("ml_score_abc", 5))

        assert dts.get_score("ml_score_123", 0) is False
        assert dts.get_score("ml_score_123", 1) is False
        assert np.isnan(dts.get_score("ml_score_123", 2))
        assert dts.get_score("ml_score_123", 3) is True
        assert np.isnan(dts.get_score("ml_score_123", 4))
        assert dts.get_score("ml_score_123", 5) is False

        assert np.isnan(dts.get_score("ml_score_000", 0))
        assert np.isnan(dts.get_score("ml_score_000", 1))
        assert np.isnan(dts.get_score("ml_score_000", 2))
        assert np.isnan(dts.get_score("ml_score_000", 3))
        assert dts.get_score("ml_score_000", 4) is True
        assert np.isnan(dts.get_score("ml_score_000", 5))

    # again in new session
    with session.DCTagSession(path, "Peter") as dts:
        assert dts.get_score("ml_score_abc", 0) is True
        assert dts.get_score("ml_score_abc", 1) is True
        assert dts.get_score("ml_score_abc", 2) is False
        assert dts.get_score("ml_score_abc", 3) is False
        assert np.isnan(dts.get_score("ml_score_abc", 4))
        assert np.isnan(dts.get_score("ml_score_abc", 5))

        assert dts.get_score("ml_score_123", 0) is False
        assert dts.get_score("ml_score_123", 1) is False
        assert np.isnan(dts.get_score("ml_score_123", 2))
        assert dts.get_score("ml_score_123", 3) is True
        assert np.isnan(dts.get_score("ml_score_123", 4))
        assert dts.get_score("ml_score_123", 5) is False

        assert np.isnan(dts.get_score("ml_score_000", 0))
        assert np.isnan(dts.get_score("ml_score_000", 1))
        assert np.isnan(dts.get_score("ml_score_000", 2))
        assert np.isnan(dts.get_score("ml_score_000", 3))
        assert dts.get_score("ml_score_000", 4) is True
        assert np.isnan(dts.get_score("ml_score_000", 5))


def test_set_score_wrong_feature_error():
    path = get_clean_data_path()
    with session.DCTagSession(path, "Peter") as dts:
        with pytest.raises(ValueError, match="Expected 'ml_score_xxx' featu"):
            dts.set_score("volume", 0, True)
        with pytest.raises(ValueError, match="Expected 'ml_score_xxx' featu"):
            dts.set_score("ml_flore_abc", 0, True)


def test_set_score_lists_and_history():
    path = get_clean_data_path()
    with session.DCTagSession(path, "Peter") as dts:
        dts.set_score("ml_score_abc", 0, True)
        dts.set_score("ml_score_abc", 2, False)
        dts.set_score("ml_score_abc", 1, True)
        dts.set_score("ml_score_abd", 3, True)
        assert dts.scores[0] == ("ml_score_abc", 0, True)
        assert dts.scores[1] == ("ml_score_abc", 2, False)
        assert dts.scores[2] == ("ml_score_abc", 1, True)
        assert dts.scores[3] == ("ml_score_abd", 3, True)
        assert dts.history["ml_score_abc count True"] == 2
        assert dts.history["ml_score_abc count False"] == 1
        assert dts.history["ml_score_abd count True"] == 1

    # now check the data file to see that this worked
    with dclab.new_dataset(path) as ds:
        assert ds["ml_score_abc"][0] == 1
        assert ds["ml_score_abc"][1] == 1
        assert ds["ml_score_abc"][2] == 0
        assert np.all(np.isnan(ds["ml_score_abc"][3:]))
        assert np.isnan(ds["ml_score_abd"][0])
        assert np.isnan(ds["ml_score_abd"][1])
        assert np.isnan(ds["ml_score_abd"][2])
        assert ds["ml_score_abd"][3] == 1
        assert np.all(np.isnan(ds["ml_score_abd"][4:]))

        # now check that the logs were written
        assert "dctag-history" in ds.logs
        dctaglog = "\n".join(ds.logs["dctag-history"])
        assert "ml_score_abc count True: 2" in dctaglog
        assert "for 'Peter'" in dctaglog


def test_set_score_multiple_ratings_for_index():
    path = get_clean_data_path()
    with session.DCTagSession(path, "Peter") as dts:
        dts.set_score("ml_score_abc", 0, True)
        dts.set_score("ml_score_abc", 2, False)
        dts.set_score("ml_score_abc", 0, False)

    with dclab.new_dataset(path) as ds:
        assert ds["ml_score_abc"][0] == 0
        assert np.isnan(ds["ml_score_abc"][1])
        assert ds["ml_score_abc"][2] == 0
        assert np.all(np.isnan(ds["ml_score_abc"][3:]))

        # now check that the logs were written
        assert "dctag-history" in ds.logs
        dctaglog = "\n".join(ds.logs["dctag-history"])
        assert "ml_score_abc count True: 1" in dctaglog
        assert "ml_score_abc count False: 2" in dctaglog


def test_set_score_with_linked_features():
    path = get_clean_data_path()
    linked = ["ml_score_001", "ml_score_002"]
    with session.DCTagSession(path, "Peter", linked_features=linked) as dts:
        dts.set_score("ml_score_001", 0, True)
        dts.set_score("ml_score_ot1", 0, False)

        dts.set_score("ml_score_ot1", 1, True)
        dts.set_score("ml_score_ot2", 1, False)
        dts.set_score("ml_score_002", 1, True)

        dts.set_score("ml_score_001", 2, True)
        dts.set_score("ml_score_002", 2, False)

        dts.set_score("ml_score_002", 3, True)
        dts.set_score("ml_score_001", 3, True)

        dts.set_score("ml_score_ot1", 4, True)
        dts.set_score("ml_score_001", 4, False)

    with dclab.new_dataset(path) as ds:
        assert ds["ml_score_001"][0] == 1
        assert ds["ml_score_002"][0] == 0
        assert ds["ml_score_ot1"][0] == 0
        assert np.isnan(ds["ml_score_ot2"][0])

        assert ds["ml_score_001"][1] == 0
        assert ds["ml_score_002"][1] == 1
        assert ds["ml_score_ot1"][1] == 1
        assert ds["ml_score_ot2"][1] == 0

        assert ds["ml_score_001"][2] == 1
        assert ds["ml_score_002"][2] == 0
        assert np.isnan(ds["ml_score_ot1"][2])
        assert np.isnan(ds["ml_score_ot2"][2])

        assert ds["ml_score_001"][3] == 1
        assert ds["ml_score_002"][3] == 0
        assert np.isnan(ds["ml_score_ot1"][3])
        assert np.isnan(ds["ml_score_ot2"][3])

        assert ds["ml_score_001"][4] == 0
        assert np.isnan(ds["ml_score_002"][4])
        assert ds["ml_score_ot1"][4] == 1
        assert np.isnan(ds["ml_score_ot2"][4])
