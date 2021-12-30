import pathlib

from PyQt5 import QtCore, QtWidgets

from dctag.gui.main import DCTag
from dctag import session
from helper import get_clean_data_path


data_dir = pathlib.Path(__file__).parent / "data"


def test_basic(qtbot):
    """Run the program and exit"""
    mw = DCTag()
    mw.close()


def test_session_load(qtbot):
    """Load an .rtdc file with labeled data"""
    path = get_clean_data_path()
    with session.DCTagSession(path, "dctag-tester") as dts:
        dts.set_score("ml_score_r1f", 0, True)
        dts.set_score("ml_score_r1f", 2, True)
        dts.set_score("ml_score_r1f", 3, True)
        dts.set_score("ml_score_r1u", 3, True)

        assert dts.get_scores_true(0) == ["ml_score_r1f"]
        assert dts.get_scores_true(1) == []
        assert dts.get_scores_true(2) == ["ml_score_r1f"]
        assert dts.get_scores_true(3) == ["ml_score_r1f", "ml_score_r1u"]
        assert dts.get_scores_true(4) == []

    mw = DCTag()
    QtWidgets.QApplication.setActiveWindow(mw)
    mw.on_action_open(path)
    # select binary tab
    mw.tabWidget.setCurrentIndex(1)
    idx = mw.tab_binary.comboBox_score.findData("ml_score_r1f")
    mw.tab_binary.comboBox_score.setCurrentIndex(idx)

    qtbot.mouseClick(mw.tab_binary.pushButton_start, QtCore.Qt.LeftButton)

    # The first event should be displayed, and it should be set to True
    assert not mw.tab_binary.pushButton_prev.isEnabled()
    assert mw.tab_binary.pushButton_yes.text() == "[Yes]"
    assert mw.tab_binary.pushButton_no.text() == "No"
    assert mw.tab_binary.label_score_next.text() == "nan"

    # Click the next button and check again
    qtbot.mouseClick(mw.tab_binary.pushButton_next, QtCore.Qt.LeftButton)
    assert mw.tab_binary.pushButton_prev.isEnabled()
    assert mw.tab_binary.pushButton_yes.text() == "Yes"
    assert mw.tab_binary.pushButton_no.text() == "No"
    assert mw.tab_binary.label_score_next.text() == "Yes"
