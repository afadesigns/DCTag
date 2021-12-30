import pathlib

from PyQt5 import QtWidgets

from dctag.gui.main import DCTag
from dctag import session
from helper import get_clean_data_path


data_dir = pathlib.Path(__file__).parent / "data"


def test_basic(qtbot):
    """Run the program and exit"""
    mw = DCTag()
    mw.close()


def test_clear_session(qtbot):
    """Clearing the session should not cause any trouble"""
    path = get_clean_data_path()
    mw = DCTag()
    QtWidgets.QApplication.setActiveWindow(mw)
    # claim session
    with session.DCTagSession(path, "dctag-tester"):
        pass
    # open session
    mw.on_action_open(path)
    # go through the tabs
    mw.tabWidget.setCurrentIndex(1)
    mw.tabWidget.setCurrentIndex(2)

    # Now clear the session
    mw.on_action_close()
    assert not mw.session
    # go through the tabs
    mw.tabWidget.setCurrentIndex(1)
    assert not mw.tab_binary.session
    assert not mw.tab_binary.widget_vis.session
    mw.tabWidget.setCurrentIndex(2)
