import pathlib

from PyQt5 import QtCore, QtWidgets
import pytest

from dctag import session
from dctag.gui.main import DCTag
from .helper import get_clean_data_path


data_dir = pathlib.Path(__file__).parent / "data"


@pytest.fixture(autouse=True)
def run_around_tests():
    # Code that will run before your test
    QtWidgets.QApplication.processEvents(QtCore.QEventLoop.AllEvents, 3000)
    pass
    # A test function will be run at this point
    yield
    # Code that will run after your test
    # restore dctag-tester for other tests
    QtCore.QCoreApplication.setOrganizationName("MPL")
    QtCore.QCoreApplication.setOrganizationDomain("dc-cosmos.org")
    QtCore.QCoreApplication.setApplicationName("dctag")
    QtCore.QSettings.setDefaultFormat(QtCore.QSettings.IniFormat)
    settings = QtCore.QSettings()
    settings.setValue("user/name", "dctag-tester")
    QtWidgets.QApplication.processEvents(QtCore.QEventLoop.AllEvents, 3000)


def test_empty_session(mw):
    QtWidgets.QApplication.setActiveWindow(mw)
    # select binary tab
    mw.tabWidget.setCurrentIndex(1)
    # make sure things are disabled
    assert not mw.tab_binary.isEnabled()


@pytest.mark.parametrize("event_index,expected", [
    [-10, 0],
    [-1, 0],
    [0, 0],
    [16, 16],
    [17, 17],
    [18, 17],
    [5000, 17]])
def test_goto_event_limits(event_index, expected, qtbot, mw):
    path = get_clean_data_path()
    # claim session
    with session.DCTagSession(path, "dctag-tester"):
        pass
    # open session
    mw.on_action_open(path)
    # select binary tab
    mw.tabWidget.setCurrentIndex(1)
    # start labeling
    qtbot.mouseClick(mw.tab_binary.pushButton_start, QtCore.Qt.LeftButton)

    # go to event
    mw.tab_binary.goto_event(event_index)
    assert mw.tab_binary.event_index == expected


def test_goto_event_button_labels(qtbot, mw):
    path = get_clean_data_path()
    with session.DCTagSession(path, "dctag-tester") as dts:
        dts.set_score("ml_score_r1f", 0, True)
        dts.set_score("ml_score_r1f", 1, False)
        dts.set_score("ml_score_r1f", 2, True)
        dts.set_score("ml_score_r1f", 3, False)

    mw.on_action_open(path)
    # select binary tab
    mw.tabWidget.setCurrentIndex(1)
    idx = mw.tab_binary.comboBox_score.findData("ml_score_r1f")
    mw.tab_binary.comboBox_score.setCurrentIndex(idx)

    qtbot.mouseClick(mw.tab_binary.pushButton_start, QtCore.Qt.LeftButton)

    # The first event should be displayed, and it should be set to True
    assert mw.tab_binary.pushButton_yes.text() == "[Yes]"
    assert mw.tab_binary.pushButton_no.text() == "No"
    assert mw.tab_binary.label_score_prev.text() == ""
    assert mw.tab_binary.label_score_next.text() == "No"

    # click on next.
    qtbot.mouseClick(mw.tab_binary.pushButton_next, QtCore.Qt.LeftButton)

    # This should be False now
    assert mw.tab_binary.pushButton_yes.text() == "Yes"
    assert mw.tab_binary.pushButton_no.text() == "[No]"
    assert mw.tab_binary.label_score_prev.text() == "Yes"
    assert mw.tab_binary.label_score_next.text() == "Yes"


def test_goto_event_button_labels_userdef(qtbot):
    settings = QtCore.QSettings()
    settings.setValue("labeling group", "userdef")

    path = get_clean_data_path()
    with session.DCTagSession(path, "dctag-tester") as dts:
        dts.set_score("userdef1", 0, True)
        dts.set_score("userdef1", 1, False)
        dts.set_score("userdef1", 2, True)
        dts.set_score("userdef1", 3, False)

    mw = DCTag()
    qtbot.addWidget(mw)
    QtWidgets.QApplication.setActiveWindow(mw)
    mw.on_action_open(path)
    # select binary tab
    mw.tabWidget.setCurrentIndex(1)
    idx = mw.tab_binary.comboBox_score.findData("userdef1")
    mw.tab_binary.comboBox_score.setCurrentIndex(idx)

    qtbot.mouseClick(mw.tab_binary.pushButton_start, QtCore.Qt.LeftButton)

    # The first event should be displayed, and it should be set to True
    assert mw.tab_binary.pushButton_yes.text() == "[Yes]"
    assert mw.tab_binary.pushButton_no.text() == "No"
    assert mw.tab_binary.label_score_prev.text() == ""
    assert mw.tab_binary.label_score_next.text() == "No"

    # click on next.
    qtbot.mouseClick(mw.tab_binary.pushButton_next, QtCore.Qt.LeftButton)

    # This should be False now
    assert mw.tab_binary.pushButton_yes.text() == "Yes"
    assert mw.tab_binary.pushButton_no.text() == "[No]"
    assert mw.tab_binary.label_score_prev.text() == "Yes"
    assert mw.tab_binary.label_score_next.text() == "Yes"
    mw.close()
    settings.setValue("labeling group", "ml_scores_blood")


def test_event_push_buttons(qtbot, mw):
    path = get_clean_data_path()
    with session.DCTagSession(path, "dctag-tester") as dts:
        dts.set_score("ml_score_r1f", 0, True)
        dts.set_score("ml_score_r1f", 1, False)
        dts.set_score("ml_score_r1f", 2, True)
        dts.set_score("ml_score_r1f", 3, False)

    mw.on_action_open(path)
    # select binary tab
    mw.tabWidget.setCurrentIndex(1)
    idx = mw.tab_binary.comboBox_score.findData("ml_score_r1f")
    mw.tab_binary.comboBox_score.setCurrentIndex(idx)

    qtbot.mouseClick(mw.tab_binary.pushButton_start, QtCore.Qt.LeftButton)
    assert mw.tab_binary.event_index == 0
    qtbot.mouseClick(mw.tab_binary.pushButton_next, QtCore.Qt.LeftButton)
    assert mw.tab_binary.event_index == 1
    qtbot.mouseClick(mw.tab_binary.pushButton_fast_next, QtCore.Qt.LeftButton)
    assert mw.tab_binary.event_index == 4
    qtbot.mouseClick(mw.tab_binary.pushButton_prev, QtCore.Qt.LeftButton)
    assert mw.tab_binary.event_index == 3
    qtbot.mouseClick(mw.tab_binary.pushButton_fast_prev, QtCore.Qt.LeftButton)
    assert mw.tab_binary.event_index == 0

    # now label a little
    qtbot.mouseClick(mw.tab_binary.pushButton_fast_next, QtCore.Qt.LeftButton)
    assert mw.tab_binary.event_index == 4
    qtbot.mouseClick(mw.tab_binary.pushButton_yes, QtCore.Qt.LeftButton)
    assert mw.tab_binary.event_index == 5
    assert mw.tab_binary.label_score_prev.text() == "Yes"
    qtbot.mouseClick(mw.tab_binary.pushButton_no, QtCore.Qt.LeftButton)
    assert mw.tab_binary.event_index == 6
    assert mw.tab_binary.label_score_prev.text() == "No"

    # go forward, label and then test fast_prev
    qtbot.mouseClick(mw.tab_binary.pushButton_next, QtCore.Qt.LeftButton)
    qtbot.mouseClick(mw.tab_binary.pushButton_next, QtCore.Qt.LeftButton)
    assert mw.tab_binary.event_index == 8
    qtbot.mouseClick(mw.tab_binary.pushButton_no, QtCore.Qt.LeftButton)
    qtbot.mouseClick(mw.tab_binary.pushButton_no, QtCore.Qt.LeftButton)
    assert mw.tab_binary.event_index == 10
    qtbot.mouseClick(mw.tab_binary.pushButton_fast_prev, QtCore.Qt.LeftButton)
    assert mw.tab_binary.event_index == 7

    # go to the end and then test fast_next
    mw.tab_binary.goto_event(16)
    assert mw.tab_binary.event_index == 16
    qtbot.mouseClick(mw.tab_binary.pushButton_no, QtCore.Qt.LeftButton)
    qtbot.mouseClick(mw.tab_binary.pushButton_no, QtCore.Qt.LeftButton)
    qtbot.mouseClick(mw.tab_binary.pushButton_prev, QtCore.Qt.LeftButton)
    qtbot.mouseClick(mw.tab_binary.pushButton_prev, QtCore.Qt.LeftButton)
    assert mw.tab_binary.event_index == 15
    qtbot.mouseClick(mw.tab_binary.pushButton_fast_next, QtCore.Qt.LeftButton)
    assert mw.tab_binary.event_index == 17


def test_session_load(qtbot, mw):
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


@pytest.mark.parametrize("event_index,expected", [
    [-10, 0],
    [-1, 0],
    [0, 0],
    [16, 16],
    [17, 17],
    [18, 17],
    [5000, 17]])
def test_on_spin(event_index, expected, qtbot, mw):
    path = get_clean_data_path()
    # claim session
    with session.DCTagSession(path, "dctag-tester"):
        pass
    # open session
    mw.on_action_open(path)
    # select binary tab
    mw.tabWidget.setCurrentIndex(1)
    # add spinbox
    qtbot.addWidget(mw.tab_binary.spinBox_jump_to)
    # set spinBox
    mw.tab_binary.spinBox_jump_to.setValue(event_index + 1)
    # check if event_index is updated correspondingly
    assert mw.tab_binary.event_index == expected


@pytest.mark.parametrize("event_index,expected", [
    [-10, 0],
    [-1, 0],
    [0, 0],
    [16, 16],
    [17, 17],
    [18, 17],
    [5000, 17]])
def test_update_spinBox(event_index, expected, qtbot, mw):
    path = get_clean_data_path()
    # claim session
    with session.DCTagSession(path, "dctag-tester"):
        pass
    # open session
    mw.on_action_open(path)
    # select binary tab
    mw.tabWidget.setCurrentIndex(1)
    # add spinbox
    qtbot.addWidget(mw.tab_binary.spinBox_jump_to)

    mw.tab_binary.goto_event(event_index)
    # check if spinBox is updated correspondingly
    assert mw.tab_binary.spinBox_jump_to.value() == expected + 1
