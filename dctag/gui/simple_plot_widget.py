from PyQt5 import QtCore, QtWidgets
import pyqtgraph as pg


class SimplePlotItem(pg.PlotItem):
    """Custom class for data visualization

    Modifications include:
    - right click menu only with "Export..."
    - top and right axes
    """

    def __init__(self, parent=None, *args, **kwargs):
        if "viewBox" not in kwargs:
            kwargs["viewBox"] = SimpleViewBox()
        super(SimplePlotItem, self).__init__(parent, *args, **kwargs)
        self.vb.export.connect(self.on_export)
        # show top and right axes
        for kax in ["top", "right"]:
            self.showAxis(kax)
            ax = self.axes[kax]["item"]
            ax.setTicks([])
            ax.setLabel(None)
            ax.setStyle(tickTextOffset=0,
                        tickTextWidth=0,
                        tickTextHeight=0,
                        autoExpandTextSpace=False,
                        showValues=False,
                        )
        self.hideButtons()

    def on_export(self, suffix):
        """Export subplots as original figures (with axes labels, etc)"""
        file, _ = QtWidgets.QFileDialog.getSaveFileName(
            None,
            'Save {} file'.format(suffix.upper()),
            '',
            '{} file (*.{})'.format(suffix.upper(), suffix))
        if not file.endswith("." + suffix):
            file += "." + suffix
        self.perform_export(file)


class SimplePlotWidget(pg.PlotWidget):
    """Custom class for data visualization in Shape-Out

    Modifications include:
    - white background
    - those of SimplePlotItem
    """

    def __init__(self, parent=None, background='w', **kargs):
        plot_item = SimplePlotItem(**kargs)
        super(SimplePlotWidget, self).__init__(parent,
                                               background=background,
                                               plotItem=plot_item)

class SimpleViewBox(pg.ViewBox):
    export = QtCore.pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super(SimpleViewBox, self).__init__(*args, **kwargs)
        #: allowed right-click menu options with new name
        self.right_click_actions = {}
        settings = QtCore.QSettings()
        if int(settings.value("advanced/developer mode", 0)):
            # Enable advanced export in developer mode
            self.right_click_actions["Export..."] = "Advanced Export"

