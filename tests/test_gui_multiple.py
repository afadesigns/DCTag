import pathlib
from unittest import mock

from PyQt5 import QtCore, QtWidgets
import pytest

from dctag import session
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
def test_goto_event_limits(event_index, expected, qtbot, mw):
    path = get_clean_data_path()
    # claim session
    with session.DCTagSession(path, "dctag-tester"):
        pass
    # open session
    mw.on_action_open(path)
    # select multiple tab
    mw.tabWidget.setCurrentIndex(2)
    mw.tab_multiple.comboBox_score.setItemChecked(0, True)  # r1f
    mw.tab_multiple.comboBox_score.setItemChecked(1, True)  # r1u
    assert mw.tab_multiple.comboBox_score.itemChecked(0)
    assert mw.tab_multiple.comboBox_score.itemChecked(1)
    assert not mw.tab_multiple.comboBox_score.itemChecked(2)
    # start labeling
    qtbot.mouseClick(mw.tab_multiple.pushButton_start, QtCore.Qt.LeftButton)

    # go to event
    mw.tab_multiple.goto_event(event_index)
    assert mw.tab_multiple.event_index == expected


def test_goto_event_button_labels(qtbot, mw):
    path = get_clean_data_path()
    with session.DCTagSession(path, "dctag-tester") as dts:
        dts.set_score("ml_score_r1f", 0, True)
        dts.set_score("ml_score_r1f", 1, False)
        dts.set_score("ml_score_r1f", 2, True)
        dts.set_score("ml_score_r1f", 3, False)
        dts.set_score("ml_score_r1u", 3, True)

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


def test_lock_in_twice(qtbot, mw):
    path = get_clean_data_path()
    with session.DCTagSession(path, "dctag-tester") as dts:
        dts.set_score("ml_score_r1f", 0, True)
        dts.set_score("ml_score_r1f", 1, False)
        dts.set_score("ml_score_r1f", 2, True)
        dts.set_score("ml_score_r1f", 3, False)
        dts.set_score("ml_score_r1u", 3, True)

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

    # Now add another item and lock in again
    mw.tabWidget.setCurrentIndex(0)
    mw.tabWidget.setCurrentIndex(2)
    mw.tab_multiple.comboBox_score.setItemChecked(0, True)  # r1f
    mw.tab_multiple.comboBox_score.setItemChecked(1, True)  # r1u
    mw.tab_multiple.comboBox_score.setItemChecked(2, True)  # r20

    qtbot.mouseClick(mw.tab_multiple.pushButton_start, QtCore.Qt.LeftButton)

    br1f, br1u, br1n = mw.tab_multiple.label_buttons
    assert br1f.pushButton.text() == "[R1F]"
    assert br1u.pushButton.text() == "!R1U"  # because it auto-filled!
    assert br1n.pushButton.text() == "!R1N"  # because it auto-filled!


def test_event_push_buttons(qtbot, mw):
    path = get_clean_data_path()
    with session.DCTagSession(path, "dctag-tester") as dts:
        dts.set_score("ml_score_r1f", 0, True)
        dts.set_score("ml_score_r1f", 1, False)
        dts.set_score("ml_score_r1u", 1, True)
        dts.set_score("ml_score_r1f", 2, True)
        dts.set_score("ml_score_r1f", 3, False)
        dts.set_score("ml_score_r1u", 3, True)

    mw.on_action_open(path)
    # select multiple tab
    mw.tabWidget.setCurrentIndex(2)
    mw.tab_multiple.comboBox_score.setItemChecked(0, True)  # r1f
    mw.tab_multiple.comboBox_score.setItemChecked(1, True)  # r1u

    qtbot.mouseClick(mw.tab_multiple.pushButton_start, QtCore.Qt.LeftButton)
    assert mw.tab_multiple.event_index == 0
    qtbot.mouseClick(mw.tab_multiple.pushButton_next, QtCore.Qt.LeftButton)
    assert mw.tab_multiple.event_index == 1
    qtbot.mouseClick(mw.tab_multiple.pushButton_fast_next,
                     QtCore.Qt.LeftButton)
    assert mw.tab_multiple.event_index == 4
    qtbot.mouseClick(mw.tab_multiple.pushButton_prev, QtCore.Qt.LeftButton)
    assert mw.tab_multiple.event_index == 3
    qtbot.mouseClick(mw.tab_multiple.pushButton_fast_prev,
                     QtCore.Qt.LeftButton)
    assert mw.tab_multiple.event_index == 0

    # now label a little
    qtbot.mouseClick(mw.tab_multiple.pushButton_fast_next,
                     QtCore.Qt.LeftButton)
    assert mw.tab_multiple.event_index == 4
    qtbot.mouseClick(mw.tab_multiple.label_buttons[0].pushButton,
                     QtCore.Qt.LeftButton)
    assert mw.tab_multiple.event_index == 5
    assert mw.tab_multiple.label_score_prev.text() == "R1F"
    qtbot.mouseClick(mw.tab_multiple.label_buttons[1].pushButton,
                     QtCore.Qt.LeftButton)
    assert mw.tab_multiple.event_index == 6
    assert mw.tab_multiple.label_score_prev.text() == "R1U"

    # go forward, label and then test fast_prev
    qtbot.mouseClick(mw.tab_multiple.pushButton_next, QtCore.Qt.LeftButton)
    qtbot.mouseClick(mw.tab_multiple.pushButton_next, QtCore.Qt.LeftButton)
    assert mw.tab_multiple.event_index == 8
    qtbot.mouseClick(mw.tab_multiple.label_buttons[1].pushButton,
                     QtCore.Qt.LeftButton)
    qtbot.mouseClick(mw.tab_multiple.label_buttons[1].pushButton,
                     QtCore.Qt.LeftButton)
    assert mw.tab_multiple.event_index == 10
    qtbot.mouseClick(mw.tab_multiple.pushButton_fast_prev,
                     QtCore.Qt.LeftButton)
    assert mw.tab_multiple.event_index == 7

    # go to the end and then test fast_next
    mw.tab_multiple.goto_event(16)
    assert mw.tab_multiple.event_index == 16
    qtbot.mouseClick(mw.tab_multiple.label_buttons[1].pushButton,
                     QtCore.Qt.LeftButton)
    qtbot.mouseClick(mw.tab_multiple.label_buttons[1].pushButton,
                     QtCore.Qt.LeftButton)
    qtbot.mouseClick(mw.tab_multiple.pushButton_prev, QtCore.Qt.LeftButton)
    qtbot.mouseClick(mw.tab_multiple.pushButton_prev, QtCore.Qt.LeftButton)
    assert mw.tab_multiple.event_index == 15
    qtbot.mouseClick(mw.tab_multiple.pushButton_fast_next,
                     QtCore.Qt.LeftButton)
    assert mw.tab_multiple.event_index == 17


def test_start_without_events_checked(qtbot, monkeypatch, mw):
    path = get_clean_data_path()
    with session.DCTagSession(path, "dctag-tester"):
        pass

    mw.on_action_open(path)
    # select multiple tab
    mw.tabWidget.setCurrentIndex(2)

    with mock.patch.object(QtWidgets.QMessageBox, "warning") as mc:
        qtbot.mouseClick(mw.tab_multiple.pushButton_start,
                         QtCore.Qt.LeftButton)
        mc.assert_called_once()
    mw.close()


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
    # select multiple tab
    mw.tabWidget.setCurrentIndex(2)
    # add spinbox
    qtbot.addWidget(mw.tab_multiple.spinBox_jump_to)
    # set spinBox value
    mw.tab_multiple.spinBox_jump_to.setValue(event_index + 1)
    # check if event_index is updated correspondingly
    assert mw.tab_multiple.event_index == expected


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
    # select multiple tab
    mw.tabWidget.setCurrentIndex(2)
    # add spinbox
    qtbot.addWidget(mw.tab_multiple.spinBox_jump_to)

    mw.tab_multiple.goto_event(event_index)
    # check if spinBox is updated correspondingly
    assert mw.tab_multiple.spinBox_jump_to.value() == expected + 1
