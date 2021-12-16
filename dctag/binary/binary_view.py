import pkg_resources

from PyQt5 import QtWidgets, uic


class BinaryView(QtWidgets.QWidget):
    """
    Class for the extraction widget
    """

    def __init__(self, *args, **kwargs):
        super(BinaryView, self).__init__(*args, **kwargs)

        ui_file = pkg_resources.resource_filename(
            'dctag.binary', 'binary_view.ui')
        uic.loadUi(ui_file, self)
