import atexit
import shutil
import tempfile
import time

from PyQt5 import QtCore

TMPDIR = tempfile.mkdtemp(prefix=time.strftime(
    "dctag_test_%H.%M_"))


def pytest_configure(config):
    """
    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest
    file after command line options have been parsed.
    """
    tempfile.tempdir = TMPDIR

    # Default settings
    QtCore.QCoreApplication.setOrganizationName("MPL")
    QtCore.QCoreApplication.setOrganizationDomain("mpl.mpg.de")
    QtCore.QCoreApplication.setApplicationName("dctag")
    QtCore.QSettings.setDefaultFormat(QtCore.QSettings.IniFormat)
    settings = QtCore.QSettings()
    settings.setValue("user/name", "dctag-tester")
    settings.setValue("debug/without timers", "1")
    atexit.register(shutil.rmtree, TMPDIR, ignore_errors=True)


def pytest_unconfigure(config):
    """
    called before test process is exited.
    """
    QtCore.QCoreApplication.setOrganizationName("MPL")
    QtCore.QCoreApplication.setOrganizationDomain("mpl.mpg.de")
    QtCore.QCoreApplication.setApplicationName("dctag")
    QtCore.QSettings.setDefaultFormat(QtCore.QSettings.IniFormat)
    settings = QtCore.QSettings()
    settings.remove("user/name")
    settings.remove("debug/without timers")
