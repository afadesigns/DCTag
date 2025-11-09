import atexit
import shutil
import tempfile
import time

from dctag.gui.main import DCTag

import pytest
from PyQt6 import QtCore, QtWidgets

TMPDIR = tempfile.mkdtemp(prefix=time.strftime(
    "dctag_test_%H.%M_"))


@pytest.fixture
def mw(qtbot):
    # Always set server correctly, because there is a test that
    # makes sure DCOR-Aid starts with a wrong server.
    QtWidgets.QApplication.processEvents(
        QtCore.QEventLoop.ProcessEventsFlag.AllEvents, 200)
    # Code that will run before your test
    mw = DCTag()
    qtbot.addWidget(mw)
    QtWidgets.QApplication.setActiveWindow(mw)
    QtWidgets.QApplication.processEvents(
        QtCore.QEventLoop.ProcessEventsFlag.AllEvents, 200)
    # Run test
    yield mw
    # Make sure that all daemons are gone
    mw.close()
    # It is extremely weird, but this seems to be important to avoid segfaults!
    QtWidgets.QApplication.processEvents(
        QtCore.QEventLoop.ProcessEventsFlag.AllEvents, 200)


def pytest_configure(config):
    """With this trick, we can access the settings from all tests"""
    # The idea is to create a QApplication instance that is used
    # to instantiate the settings.
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    # Some promoted widgets need the below constants set in order
    # to access the settings upon initialization.
    QtCore.QCoreApplication.setOrganizationName("MPL")
    QtCore.QCoreApplication.setOrganizationDomain("dc-cosmos.org")
    QtCore.QCoreApplication.setApplicationName("dctag-testing")
    QtCore.QSettings.setDefaultFormat(QtCore.QSettings.Format.IniFormat)
    # The settings are not used here, but this is the place where
    # they are created.
    settings = QtCore.QSettings()
    settings.clear()


def pytest_unconfigure(config):
    """Restore the settings"""
    # restore dctag-tester for other tests
    QtCore.QCoreApplication.setOrganizationName("MPL")
    QtCore.QCoreApplication.setOrganizationDomain("dc-cosmos.org")
    QtCore.QCoreApplication.setApplicationName("dctag")
    QtCore.QSettings.setDefaultFormat(QtCore.QSettings.Format.IniFormat)
    settings = QtCore.QSettings()
    settings.clear()
