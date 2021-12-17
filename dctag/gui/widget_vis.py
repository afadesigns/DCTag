import pkg_resources

from PyQt5 import QtWidgets, uic


class WidgetVisualize(QtWidgets.QWidget):
    """Widget for visualizing data"""
    def __init__(self, *args, **kwargs):
        super(WidgetVisualize, self).__init__(*args, **kwargs)

        ui_file = pkg_resources.resource_filename(
            'dctag.gui', 'widget_vis.ui')
        uic.loadUi(ui_file, self)
