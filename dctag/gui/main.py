import getpass
import pathlib
import pkg_resources
import signal
import sys
import time
import traceback

import dclab
import h5py
import numpy
from PyQt5 import uic, QtCore, QtWidgets
import pyqtgraph as pg

from .. import session
from .._version import version


# global plotting configuration parameters
pg.setConfigOption("background", None)
pg.setConfigOption("foreground", "k")
pg.setConfigOption("antialias", True)
pg.setConfigOption("imageAxisOrder", "row-major")


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
        self.set_title()
        # Disable native menubar (e.g. on Mac)
        self.menubar.setNativeMenuBar(False)
        # File menu
        self.actionOpen.triggered.connect(self.on_action_open)
        self.actionQuit.triggered.connect(self.on_action_quit)
        self.actionClose.triggered.connect(self.on_action_close)
        # Help menu
        self.actionSoftware.triggered.connect(self.on_action_software)
        self.actionAbout.triggered.connect(self.on_action_about)

        # tabwidget
        self.tabWidget.currentChanged.connect(self.on_tab_changed)

        #: holds the current DCTagSession instance
        self.session = None

        # if "--version" was specified, print the version and exit
        if "--version" in sys.argv:
            print(version)
            QtWidgets.QApplication.processEvents(
                QtCore.QEventLoop.AllEvents, 300)
            sys.exit(0)
        self.show()
        self.raise_()
        self.activateWindow()

        # flush session regularly
        if bool(int(self.settings.value("debug/without timers", "0"))):
            self.timer = None
        else:
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.session_flush_statusbar)
            self.timer.start(60000)

    def closeEvent(self, event):
        if self.session_close():
            event.accept()
        else:
            event.ignore()

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
        QtWidgets.QMessageBox.about(self, f"DCTag {version}", about_text)

    @QtCore.pyqtSlot()
    def on_action_close(self):
        self.session_close()
        # Go to session tab and update info
        self.tabWidget.setCurrentIndex(0)
        self.on_tab_changed()

    @QtCore.pyqtSlot()
    def on_action_open(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            'Select RT-DC data',
            self.settings.value("paths/open", ""),
            'RT-DC data (*.rtdc)')
        if path:
            self.settings.setValue(
                "paths/open", str(pathlib.Path(path).parent))
            self.session_open(path)

    @QtCore.pyqtSlot()
    def on_action_quit(self):
        self.on_action_close()
        QtCore.QCoreApplication.quit()

    @QtCore.pyqtSlot()
    def on_action_software(self):
        libs = [dclab,
                h5py,
                numpy,
                ]
        sw_text = "DCTag {}\n\n".format(version)
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
        self.set_title()

    def session_close(self):
        if not self.session:
            success = True
        else:
            try:
                self.session.flush()
            except session.DCTagSessionWriteError as e:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Cannot close this session",
                    "For some reason, it is not possible to close the current "
                    + f"session '{self.session.path}'. Details:<br><br>"
                    + e.args[-1]
                )
                success = False
            else:
                self.session.close()
                self.session = None
                success = True
        return success

    def session_flush_statusbar(self):
        """Flush the session, writing all changes to the file

        If any errors occur, this is written to the status bar.
        """
        if self.session:
            date = time.strftime("%Y-%m-%d %H:%M:%S")
            try:
                self.session.flush()
            except BaseException as e:
                self.statusBar().showMessage(
                    f"{date} Saving failed with {e.__class__.__name__}: {e}")
                self.statusBar().setStyleSheet("color: red")
            else:
                self.statusBar().showMessage(f"{date} Session flushed.", 3000)
                self.statusBar().setStyleSheet("")

    def session_open(self, path_rtdc):
        """Load an .rtdc file into the user interface"""
        if self.session_close():
            user = self.settings.value("user/name", None)
            assert user
            # check whether we have a dctag-history log and if not,
            # ask the user whether to create a copy of the file.
            if session.is_dctag_session(path_rtdc):
                cont = True
            else:
                reply = QtWidgets.QMessageBox.question(
                    self,
                    "Claim this file?",
                    f"The file '{path_rtdc}' is not (yet) a DCTag session. "
                    + "Would you like to claim this file? If you select "
                    + "'Yes', this file will be tied to your username/alias. "
                    + "This cannot be undone. You may alternatively select "
                    + "'No' and open a copy of that file instead."
                )
                cont = reply == QtWidgets.QMessageBox.Yes
            if cont:
                try:
                    self.session = session.DCTagSession(path=path_rtdc,
                                                        user=user,
                                                        linked_features=[])
                except session.DCTagSessionWrongUserError as e:
                    QtWidgets.QMessageBox.warning(
                        self,
                        "Cannot load session",
                        "You are trying to open a session from another user. "
                        + "This is not supported yet. These are the details: "
                        + "<br><br>"
                        + e.args[-1]
                    )
                else:
                    # Go to session tab and update info
                    self.tabWidget.setCurrentIndex(0)
                    self.on_tab_changed()

    def set_title(self, task=None):
        if task is None:
            title = f"DCTag {version}"
        else:
            title = f"{task} [DCTag {version}]"
        self.setWindowTitle(title)


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
    vinfo = f"Unhandled exception in DCTag version {version}:\n"
    tmp = traceback.format_exception(etype, value, trace)
    exception = "".join([vinfo]+tmp)
    print(exception)

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
