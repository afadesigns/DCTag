import pathlib

from PyQt5 import QtCore, QtWidgets
import pytest

from dctag.gui.main import DCTag
from dctag import session
from helper import get_clean_data_path


data_dir = pathlib.Path(__file__).parent / "data"


def test_empty_session(qtbot):
    mw = DCTag()
    QtWidgets.QApplication.setActiveWindow(mw)
    # select multiple tab
    mw.tabWidget.setCurrentIndex(2)
    # make sure things are disabled
    assert not mw.tab_multiple.isEnabled()


@pytest.mark.parametrize("event_index,expected", [
    [-10, 0],
    [-1, 0],
    [0, 0],
    [16, 16],
    [17, 17],
    [18, 17],
    [5000, 17]])
def test_goto_event_limits(event_index, expected, qtbot):
    path = get_clean_data_path()
    mw = DCTag()
    QtWidgets.QApplication.setActiveWindow(mw)
    # claim session
    with session.DCTagSession(path, "dctag-tester"):
        pass
    # open session
    mw.on_action_open(path)
    # select multiple tab
    mw.tabWidget.setCurrentIndex(2)
    mw.tab_multiple.comboBox_score.setItemChecked(0, True)  # r1f
    mw.tab_multiple.comboBox_score.setItemChecked(1, True)  # r1u
    # start labeling
    qtbot.mouseClick(mw.tab_multiple.pushButton_start, QtCore.Qt.LeftButton)

    # go to event
    mw.tab_multiple.goto_event(event_index)
    assert mw.tab_multiple.event_index == expected


def test_goto_event_button_labels(qtbot):
    path = get_clean_data_path()
    with session.DCTagSession(path, "dctag-tester") as dts:
        dts.set_score("ml_score_r1f", 0, True)
        dts.set_score("ml_score_r1f", 1, False)
        dts.set_score("ml_score_r1f", 2, True)
        dts.set_score("ml_score_r1f", 3, False)
        dts.set_score("ml_score_r1u", 3, True)

    mw = DCTag()
    QtWidgets.QApplication.setActiveWindow(mw)
    mw.on_action_open(path)
    # select multiple tab
    mw.tabWidget.setCurrentIndex(2)
    mw.tab_multiple.comboBox_score.setItemChecked(0, True)  # r1f
    mw.tab_multiple.comboBox_score.setItemChecked(1, True)  # r1u

    qtbot.mouseClick(mw.tab_multiple.pushButton_start, QtCore.Qt.LeftButton)

    assert len(mw.tab_multiple.label_buttons) == 2

    br1f, br1u = mw.tab_multiple.label_buttons
    assert br1f.pushButton.text() == "[R1F]"
    assert br1u.pushButton.text() == "!R1U"  # because it auto-filled!
    assert mw.tab_multiple.label_score_prev.text() == ""
    assert mw.tab_multiple.label_score_next.text() == "nan"

    # click on next.
    qtbot.mouseClick(mw.tab_multiple.pushButton_next, QtCore.Qt.LeftButton)

    assert br1f.pushButton.text() == "!R1F"
    assert br1u.pushButton.text() == "R1U"
    assert mw.tab_multiple.label_score_prev.text() == "R1F"
    assert mw.tab_multiple.label_score_next.text() == "R1F"

    # click on next.
    qtbot.mouseClick(mw.tab_multiple.pushButton_next, QtCore.Qt.LeftButton)

    assert br1f.pushButton.text() == "[R1F]"
    assert br1u.pushButton.text() == "!R1U"
    assert mw.tab_multiple.label_score_prev.text() == "nan"
    assert mw.tab_multiple.label_score_next.text() == "R1U"

    qtbot.mouseClick(mw.tab_multiple.pushButton_next, QtCore.Qt.LeftButton)

    assert br1f.pushButton.text() == "!R1F"
    assert br1u.pushButton.text() == "[R1U]"
    assert mw.tab_multiple.label_score_prev.text() == "R1F"
    assert mw.tab_multiple.label_score_next.text() == "nan"
