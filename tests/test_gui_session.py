import pathlib

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


def test_error_session(qtbot, mw):
    path = get_clean_data_path()
    with session.DCTagSession(path, "dctag-tester") as dts:
        dts.set_score("ml_score_r1f", 0, True)
    # open session
    mw.on_action_open(path)
    # got to other tab and remove the file
    mw.tabWidget.setCurrentIndex(1)
    assert not mw.tab_session.plainTextEdit_logs.toPlainText() == "No session."
    path.unlink()
    mw.tabWidget.setCurrentIndex(0)
    assert mw.tab_session.plainTextEdit_logs.toPlainText().startswith(
        "Cannot get logs from")


def test_view_session(qtbot, mw):
    """Clearing the session should not cause any trouble"""
    path = get_clean_data_path()
    # make sure there is no session
    assert mw.tab_session.plainTextEdit_logs.toPlainText() == "No session."
    # claim session
    with session.DCTagSession(path, "dctag-tester") as dts:
        dts.set_score("ml_score_r1f", 0, True)
        dts.set_score("ml_score_r1f", 1, False)
        dts.set_score("ml_score_r1f", 2, True)
        dts.set_score("ml_score_r1f", 3, False)
    # open session
    mw.on_action_open(path)
    assert mw.tab_session.plainTextEdit_logs.toPlainText().count(
        "ml_score_r1f")
    mw.on_action_close()
    assert mw.tab_session.plainTextEdit_logs.toPlainText() == "No session."
