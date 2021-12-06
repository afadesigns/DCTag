import pkg_resources
from PyQt5 import QtWidgets, uic


class SessionView(QtWidgets.QWidget):
    """
    Class for the extraction widget
    """

    def __init__(self, *args, **kwargs):
        super(SessionView, self).__init__(*args, **kwargs)

        ui_file = pkg_resources.resource_filename(
            'dctag.session', 'session_view.ui')
        uic.loadUi(ui_file, self)