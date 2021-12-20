import pytest

import dclab
import h5py
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


def test_is_dctag_session():
    path = get_clean_data_path()
    assert not session.is_dctag_session(path)
    with session.DCTagSession(path, "Peter"):
        pass
    assert session.is_dctag_session(path)


def test_flush_with_missing_file_error():
    path = get_clean_data_path()
    # error should be raised on flush and on __exit__
    with pytest.raises(session.DCTagSessionWriteError, match=f"{path}"):
        with session.DCTagSession(path, "Peter") as dts:
            dts.set_score("ml_score_abc", 0, True)
            path.unlink()
            with pytest.raises(session.DCTagSessionWriteError,
                               match=f"{path}"):
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


def test_log_basic():
    path = get_clean_data_path()
    with session.DCTagSession(path, "Peter") as dts:
        dts.set_score("ml_score_abc", 0, True)
        dts.set_score("ml_score_abc", 1, True)
        dts.set_score("ml_score_abc", 0, False)

    expected = [
        "user: Peter",
        "",
        "New session with DCTag ",
        "Linked features: []",
        "ml_score_abc count False: 1",
        "ml_score_abc count True: 2",
    ]

    with dclab.new_dataset(path) as ds:
        for line, exp in zip(ds.logs["dctag-history"], expected):
            assert exp in line


def test_log_linked_features():
    path = get_clean_data_path()
    with session.DCTagSession(path, "Peter") as dts:
        dts.set_score("ml_score_abc", 0, True)
        dts.set_score("ml_score_abc", 1, True)
        dts.set_score("ml_score_abc", 0, False)
        dts.linked_features = ["ml_score_abc", "ml_score_456"]
        dts.set_score("ml_score_abc", 2, True)
        dts.set_score("ml_score_456", 3, True)

    expected = [
        "user: Peter",
        "",
        "New session with DCTag ",
        "Linked features: []",
        "ml_score_abc count False: 1",
        "ml_score_abc count True: 2",
        "",
        "New session with DCTag ",
        "Linked features: ['ml_score_456', 'ml_score_abc']",
        "ml_score_456 count True: 1",
        "ml_score_abc count True: 1",
    ]

    with dclab.new_dataset(path) as ds:
        for line, exp in zip(ds.logs["dctag-history"], expected):
            assert exp in line


def test_log_user():
    """At the beginning, onle the user should be written"""
    path = get_clean_data_path()
    with session.DCTagSession(path, "Peter"):
        pass
    with dclab.new_dataset(path) as ds:
        assert "".join(ds.logs["dctag-history"]).strip() == "user: Peter"


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
        assert dctaglog.startswith("user: Peter")


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


def test_set_score_wrong_feature_error():
    path = get_clean_data_path()
    with session.DCTagSession(path, "Peter") as dts:
        with pytest.raises(ValueError, match="Expected 'ml_score_xxx' featu"):
            dts.set_score("volume", 0, True)
        with pytest.raises(ValueError, match="Expected 'ml_score_xxx' featu"):
            dts.set_score("ml_flore_abc", 0, True)


def test_session_backup_scores():
    path = get_clean_data_path()
    linked = ["ml_score_001", "ml_score_002"]
    # We cannot use the context manager, because closing it will raise
    # an exception.
    dts = session.DCTagSession(path, "Peter", linked_features=linked)
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

    # simulate worst-case scenario
    path.unlink()
    assert not path.exists()

    # now create a backup
    backup_path = path.with_name("scores.h5")
    dts.backup_scores(backup_path)

    # now recreate the session by using the same path
    path2 = get_clean_data_path()
    with h5py.File(backup_path) as h5, dclab.RTDCWriter(path2) as hw:
        for feat in h5:
            hw.store_feature(feat, h5[feat])

    # This is the same test as above, only this time from the recreated file
    with dclab.new_dataset(path2) as ds:
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


def test_session_bool():
    path = get_clean_data_path()
    dts = session.DCTagSession(path, "Peter")
    assert dts
    dts.close()
    assert not dts


def test_session_claim_path_missing_history():
    """Handle missing history properly"""
    path = get_clean_data_path()
    with dclab.RTDCWriter(path) as hw:
        hw.store_log("dctag-history", "Nothing")

    with session.DCTagSession(path, "Peter"):
        pass

    with dclab.new_dataset(path) as ds:
        assert ds.logs["dctag-history"][0] == "user: Peter"


def test_session_claim_path_missing_history_empty_log():
    """Handle missing history properly"""
    path = get_clean_data_path()
    with dclab.RTDCWriter(path) as hw:
        hw.store_log("dctag-history", [])

    with session.DCTagSession(path, "Peter"):
        pass

    with dclab.new_dataset(path) as ds:
        assert ds.logs["dctag-history"][0] == "user: Peter"


def test_session_error_closed_flush():
    path = get_clean_data_path()
    dts = session.DCTagSession(path, "Peter")
    dts.set_score("ml_score_001", 10, False)
    # Force this scenario which otherwise could only be triggered maybe
    # via threading.
    dts._closed = True
    with pytest.raises(session.DCTagSessionClosedError,
                       match="flush the session"):
        dts.flush()


def test_session_error_closed_set_score():
    path = get_clean_data_path()
    dts = session.DCTagSession(path, "Peter")
    dts.close()
    with pytest.raises(session.DCTagSessionClosedError,
                       match="set the score"):
        dts.set_score("ml_score_001", 0, True)


def test_session_error_locked():
    path = get_clean_data_path()
    lock_path = path.with_suffix(".dctag")
    lock_path.touch()
    # make sure the session cannot be opened if it is locked
    with pytest.raises(session.DCTagSessionLockedError, match=f"{path}"):
        with session.DCTagSession(path, "Peter"):
            pass
    # make sure the lock file is not removed by context manager
    assert lock_path.exists()


def test_session_error_wronguser():
    path = get_clean_data_path()
    with session.DCTagSession(path, "Peter"):
        pass

    with pytest.raises(session.DCTagSessionWrongUserError, match="Peter"):
        with session.DCTagSession(path, "Hans"):
            pass


def test_session_multiple_with_linked_features():
    path = get_clean_data_path()
    with session.DCTagSession(path, "Peter") as dts:
        dts.set_score("ml_score_abc", 0, True)
        dts.set_score("ml_score_abc", 1, True)
        dts.set_score("ml_score_abc", 0, False)
        dts.linked_features = ["ml_score_abc", "ml_score_456"]
        dts.set_score("ml_score_abc", 2, True)
        dts.set_score("ml_score_456", 3, True)

    with dclab.new_dataset(path) as ds:
        assert ds["ml_score_abc"][0] == 0
        assert ds["ml_score_abc"][1] == 1
        assert ds["ml_score_abc"][2] == 1
        assert ds["ml_score_abc"][3] == 0

        # unless a method is implemented that does "autocompletion",
        # we should not touch these.
        assert np.isnan(ds["ml_score_456"][0])
        assert np.isnan(ds["ml_score_456"][1])
        # from linked session:
        assert ds["ml_score_456"][2] == 0
        assert ds["ml_score_456"][3] == 1


def test_session_warning_closed_get_score():
    path = get_clean_data_path()
    dts = session.DCTagSession(path, "Peter")
    dts.set_score("ml_score_123", 0, True)
    dts.close()
    with pytest.warns(session.DCTagSessionClosedWarning,
                      match="get the score"):
        assert dts.get_score("ml_score_123", 0)


def test_session_warning_closed_close():
    path = get_clean_data_path()
    dts = session.DCTagSession(path, "Peter")
    dts.set_score("ml_score_123", 0, True)
    dts.close()
    with pytest.warns(session.DCTagSessionClosedWarning,
                      match="close the session"):
        dts.close()


def test_session_warning_closed_flush():
    path = get_clean_data_path()
    dts = session.DCTagSession(path, "Peter")
    dts.set_score("ml_score_123", 0, True)
    dts.close()
    with pytest.warns(session.DCTagSessionClosedWarning,
                      match="flush the session"):
        dts.flush()
