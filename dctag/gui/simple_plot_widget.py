import pyqtgraph as pg


class SimplePlotItem(pg.PlotItem):
    """Custom class for data visualization in dctag.

    Modifications include:
    - top and right axes
    """

    def __init__(self, *args, **kwargs):
        super(SimplePlotItem, self).__init__(*args, **kwargs)
        # show top and right axes
        for kax in ["top", "right", "left"]:
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


class SimplePlotWidget(pg.PlotWidget):
    """Custom class for data visualization in dctag.

    Modifications include:
    - white background
    - those of SimplePlotItem
    """

    def __init__(self, parent=None, background='w', **kargs):
        plot_item = SimplePlotItem(**kargs)
        super(SimplePlotWidget, self).__init__(parent,
                                               background=background,
                                               plotItem=plot_item)
