import pyqtgraph as pg


class SimplePlotItem(pg.PlotItem):
    """Custom class for data visualization in DCTag

    Modifications include:
    - top and right axes
    """

    def __init__(self, parent=None, *args, **kwargs):
        super(SimplePlotItem, self).__init__(parent, *args, **kwargs)
        # show top and right axes, but not ticklabels
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
        # This screwed up zooming with right-click:
        # self.showGrid(x=True, y=True, alpha=.1)
        # Use the new GridItem instead:
        grid = pg.GridItem()
        grid.setTextPen("#FFFF")  # hide grid tick labels
        self.addItem(grid)

        # visualization
        self.hideButtons()


class ScatterPlotWidget(pg.PlotWidget):
    """Custom class for data visualization in DCTag
    """

    def __init__(self, parent=None, background='w', **kargs):
        plot_item = SimplePlotItem(**kargs)
        super(ScatterPlotWidget, self).__init__(parent,
                                                background=background,
                                                plotItem=plot_item)

        self.scatter = RTDCScatterPlot()
        self.addItem(self.scatter)
        self.select = pg.PlotDataItem(x=[1], y=[2], symbol="o",
                                      symbolBrush="red")
        self.select.hide()
        self.addItem(self.select)

    def set_scatter(self, x, y):
        self.scatter.setData(x, y)

    def set_event(self, x, y):
        self.select.show()
        self.select.setData([x], [y])


class RTDCScatterPlot(pg.ScatterPlotItem):
    def __init__(self, size=3, pen=None, brush=None, *args, **kwargs):
        if pen is None:
            pen = pg.mkPen(color=(0, 0, 0, .5))
        if brush is None:
            brush = pg.mkBrush("k")
        super(RTDCScatterPlot, self).__init__(size=size,
                                              pen=pen,
                                              brush=brush,
                                              symbol="s",
                                              *args,
                                              **kwargs)
        self.setData(x=range(10), y=range(10), brush=brush)
