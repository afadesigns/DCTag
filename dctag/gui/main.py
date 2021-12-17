import getpass
import pathlib
import pkg_resources
import signal
import sys
import traceback

import dclab
import h5py
import numpy
from PyQt5 import uic, QtCore, QtWidgets

from .. import session
from .._version import version as __version__


class DCTag(QtWidgets.QMainWindow):
    def __init__(self, check_update=True):
        super(DCTag, self).__init__()

        # Settings are stored in the .ini file format. Even though
        # `self.settings` may return integer/bool in the same session,
        # in the next session, it will reliably return strings. Lists
        # of strings (comma-separated) work nicely though.
        # Some promoted widgets need the below constants set in order
        # to access the settings upon initialization.
        QtCore.QCoreApplication.setOrganizationName("MPL")
        QtCore.QCoreApplication.setOrganizationDomain("mpl.mpg.de")
        QtCore.QCoreApplication.setApplicationName("dctag")
        QtCore.QSettings.setDefaultFormat(QtCore.QSettings.IniFormat)

        #: DCOR-Aid settings
        self.settings = QtCore.QSettings()
        username = self.settings.value("user/name", None)
        if username is None:
            username, ok = QtWidgets.QInputDialog.getText(
                self,
                "Specify username",
                "Please specify your alias. This will be used to<br>"
                + "attribute the datasets you labeled to a unique<br>"
                + "entity and it will be used to lock/link .rtdc files<br>"
                + "to that entity.<br><br>"
                + "Please choose wisely.<br>"
                + "You should not change it in the future.",
                text=getpass.getuser()
                )
            if ok and username.strip():
                username = username.strip()
            else:
                # Abort
                sys.exit(0)
        self.settings.setValue("user/name", username)

        # initialize UI
        path_ui = pkg_resources.resource_filename("dctag.gui", "main.ui")
        uic.loadUi(path_ui, self)
        self.setWindowTitle("DCTag {}".format(__version__))
        # Disable native menubar (e.g. on Mac)
        self.menubar.setNativeMenuBar(False)
        # File menu
        self.actionOpen.triggered.connect(self.on_action_open)
        # Help menu
        self.actionSoftware.triggered.connect(self.on_action_software)
        self.actionAbout.triggered.connect(self.on_action_about)

        # tabwidget
        self.tabWidget.currentChanged.connect(self.on_tab_changed)

        #: holds the current DCTagSession instance
        self.session = None

        # if "--version" was specified, print the version and exit
        if "--version" in sys.argv:
            print(__version__)
            QtWidgets.QApplication.processEvents(
                QtCore.QEventLoop.AllEvents, 300)
            sys.exit(0)
        self.show()
        self.raise_()
        self.activateWindow()
        self.setWindowState(QtCore.Qt.WindowState.WindowActive)

    def dragEnterEvent(self, e):
        """Whether files are accepted"""
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        """Add dropped files to view"""
        urls = e.mimeData().urls()
        if len(urls) > 1:
            raise ValueError(
                f"Can only open one file at a time, got {len(urls)}!")
        elif urls:
            pp = pathlib.Path(urls[0].toLocalFile())
            self.session_open(pp)

    @QtCore.pyqtSlot()
    def on_action_about(self):
        about_text = "DCTag: Annotate .rtdc files for ML training"
        QtWidgets.QMessageBox.about(self,
                                    "DCTag {}".format(__version__),
                                    about_text)

    @QtCore.pyqtSlot()
    def on_action_open(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            'Select RT-DC data',
            '',
            'RT-DC data (*.rtdc)')
        if path:
            self.session_open(path)

    @QtCore.pyqtSlot()
    def on_action_software(self):
        libs = [dclab,
                h5py,
                numpy,
                ]
        sw_text = "DCTag {}\n\n".format(__version__)
        sw_text += "Python {}\n\n".format(sys.version)
        sw_text += "Modules:\n"
        for lib in libs:
            sw_text += "- {} {}\n".format(lib.__name__, lib.__version__)
        sw_text += "- PyQt5 {}\n".format(QtCore.QT_VERSION_STR)
        if hasattr(sys, 'frozen'):
            sw_text += "\nThis executable has been created using PyInstaller."
        QtWidgets.QMessageBox.information(self,
                                          "Software",
                                          sw_text)

    @QtCore.pyqtSlot()
    def on_tab_changed(self):
        curtab = self.tabWidget.currentWidget()
        curtab.update_session(self.session)

    def session_close(self):
        if self.session is None:
            success = True
        else:
            try:
                self.session.flush()
            except session.DCTagSessionWriteError as e:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Cannot close previous session",
                    "For some reason, it is not possible to close the current "
                    + f"session'{self.session.path}', so I will not open a "
                    + "new session. Details:<br><br>"
                    + e.args[-1]
                )
                success = False
            else:
                self.session.close()
                self.session = None
                success = True
        return success

    def session_open(self, path_rtdc):
        """Load an .rtdc file into the user interface"""
        if self.session_close():
            try:
                user = self.settings.value("user/name", None)
                assert user
                self.session = session.DCTagSession(path=path_rtdc,
                                                    user=user,
                                                    linked_features=[])
            except session.DCTagSessionWrongUserError as e:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Cannot load session",
                    "You are trying to open a session from another user. This "
                    + "is not supported yet. These are the details:<br><br>"
                    + e.args[-1]
                )
            else:
                # Go to session tab and update info
                self.tabWidget.setCurrentIndex(0)
                self.on_tab_changed()


def excepthook(etype, value, trace):
    """
    Handler for all unhandled exceptions.

    :param `etype`: the exception type (`SyntaxError`,
        `ZeroDivisionError`, etc...);
    :type `etype`: `Exception`
    :param string `value`: the exception error message;
    :param string `trace`: the traceback header, if any (otherwise, it
        prints the standard Python header: ``Traceback (most recent
        call last)``.
    """
    vinfo = "Unhandled exception in DCTag version {}:\n".format(
        __version__)
    tmp = traceback.format_exception(etype, value, trace)
    exception = "".join([vinfo]+tmp)

    errorbox = QtWidgets.QMessageBox()
    errorbox.setIcon(QtWidgets.QMessageBox.Critical)
    errorbox.addButton(QtWidgets.QPushButton('Close'),
                       QtWidgets.QMessageBox.YesRole)
    errorbox.addButton(QtWidgets.QPushButton(
        'Copy text && Close'), QtWidgets.QMessageBox.NoRole)
    errorbox.setText(exception)
    ret = errorbox.exec_()
    if ret == 1:
        cb = QtWidgets.QApplication.clipboard()
        cb.clear(mode=cb.Clipboard)
        cb.setText(exception)


# Make Ctr+C close the app
signal.signal(signal.SIGINT, signal.SIG_DFL)
# Display exception hook in separate dialog instead of crashing
sys.excepthook = excepthook
