import pyqtgraph as pg


class SimpleImageView(pg.ImageView):
    """Custom class for visualizing images"""

    def __init__(self, *args, **kwargs):
        super(SimpleImageView, self).__init__(*args, **kwargs)

        # disable pyqtgraph controls we don't need
        self.ui.histogram.hide()
        self.ui.roiBtn.hide()
        self.ui.menuBtn.hide()
        # disable keyboard shortcuts
        self.keyPressEvent = lambda _: None
        self.keyReleaseEvent = lambda _: None

    def getViewBox(self):
        return self.getPlotItem().getViewBox()
