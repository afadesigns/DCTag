import functools
import importlib.resources

import dclab
import numpy as np
from PyQt6 import QtCore, QtWidgets, uic
import pyqtgraph as pg
from scipy.ndimage import binary_erosion


#: dictionary with default axes limits for these features
LIMITS_FEAT = {
    "deform": [0.0, 0.5],
    "area_um": [10, 130],
    "bright_avg": [70, 140],
    "bright_sd": [5, 35],
    "time": None,
}

#: list with scatter plot axis features (there are three)
SCATTER_FEAT = [
    ["area_um", "deform"],
    ["area_um", "bright_avg"],
    ["bright_sd", "bright_avg"],
    ["time", "bright_avg"],
]


class WidgetVisualize(QtWidgets.QWidget):
    """Widget for visualizing data"""

    def __init__(self, *args, **kwargs):
        super(WidgetVisualize, self).__init__(*args, **kwargs)

        ref = importlib.resources.files("dctag.gui") / "widget_vis.ui"
        with importlib.resources.as_file(ref) as path_ui:
            uic.loadUi(path_ui, self)

        self.session = None

        self.scatter_plots = [self.scatter_1, self.scatter_2, self.scatter_3,
                              self.scatter_4]
        # Set individual plots
        kw0 = dict(x=np.arange(10), y=np.arange(10))
        self.trace_plots = {
            "fl1_raw": pg.PlotDataItem(pen="#15BF00", **kw0),  # green
            "fl2_raw": pg.PlotDataItem(pen="#BF8A00", **kw0),  # orange
            "fl3_raw": pg.PlotDataItem(pen="#BF0C00", **kw0),  # red
            "fl1_median": pg.PlotDataItem(pen="#15BF00", **kw0),  # green
            "fl2_median": pg.PlotDataItem(pen="#BF8A00", **kw0),  # orange
            "fl3_median": pg.PlotDataItem(pen="#BF0C00", **kw0),  # red
        }
        self.widget_trace.plotItem.setLabels(bottom="Event time [µs]")
        self.legend_trace = self.widget_trace.addLegend(
            offset=(+.001, -.001), labelTextSize='7pt', colCount=1)

        self.trace_plot_legends = {}

        for key in self.trace_plots:
            self.widget_trace.addItem(self.trace_plots[key])
            self.trace_plots[key].hide()

        # linked axes
        for ii, plota in enumerate(self.scatter_plots):
            vba = plota.getViewBox()
            for jj, plotb in enumerate(self.scatter_plots):
                vbb = plotb.getViewBox()
                if ii < jj:
                    if SCATTER_FEAT[ii][0] == SCATTER_FEAT[jj][0]:
                        vba.linkView(vba.XAxis, vbb)
                    if SCATTER_FEAT[ii][1] == SCATTER_FEAT[jj][1]:
                        vba.linkView(vba.YAxis, vbb)

        # signals
        self.checkBox_auto_contrast.stateChanged.connect(
            self.update_image_cropped)
        self.spinBox_contrast_max.valueChanged.connect(
            self.update_image_cropped)
        self.spinBox_contrast_min.valueChanged.connect(
            self.update_image_cropped)

    def reset(self, reset_plots=False):
        """Clear current visualization"""
        # clear the event image cache
        self.get_event_data.cache_clear()
        self.get_feature_data.cache_clear()
        # UI
        self.setEnabled(False)
        self.groupBox_event.setTitle("Event")
        if reset_plots:
            self.image_channel.clear()
            self.image_channel_contour.clear()
            self.image_cropped.clear()
            self.legend_trace.clear()
            for key in self.trace_plots:
                line = self.trace_plots[key]
                line.setData(np.arange(10), np.arange(10))
                self.widget_trace.update()
            for plot in self.scatter_plots:
                plot.set_scatter(np.arange(10), np.arange(10))

    @functools.lru_cache(maxsize=900)
    def get_feature_data(self, feature):
        with dclab.new_dataset(self.session.path) as ds:
            return ds[feature][:]

    @functools.lru_cache(maxsize=50)
    def get_event_data(self, index):
        # is this too slow?
        with dclab.new_dataset(self.session.path) as ds:
            pxs = ds.config["imaging"]["pixel size"]
            data = {"image": ds["image"][index],
                    "mask": ds["mask"][index],
                    "pos_x_px": self.get_feature_data("pos_x")[index] / pxs,
                    }
            for feat in LIMITS_FEAT:
                data[feat] = self.get_feature_data(feat)[index]
        return data

    def set_event(self, session, event_index):
        if self.session is not session:
            self.reset()
            self.session = session
            self.update_scatter_plots()
        if self.session:
            # Programmatically, this is always the case, but for clarity,
            # we use the `if self.session` case.
            self.setEnabled(True)
            self.groupBox_event.setTitle(
                f"Event {event_index + 1} (total {session.event_count}) ")
            self.session = session
            data = self.get_event_data(event_index)
            # Plot the channel images
            # raw image
            self.image_channel.setImage(data["image"])
            # image with contour
            image_contour = get_contour_image(data)
            self.image_channel_contour.setImage(image_contour)
            # cropped image
            image_cropped = get_cropped_image(data)
            self.update_image_cropped(image_cropped)

            # Plot event in the scatter plots
            for plot, [featx, featy] in zip(self.scatter_plots, SCATTER_FEAT):
                plot.set_event(data[featx], data[featy])

            # Add the Fluorescence traces of the event
            self.set_fluorescence_traces(event_index)

    @QtCore.pyqtSlot()
    def update_image_cropped(self, image_cropped=None):
        """Udpate the cropped image on the right

        This handles auto-contrast.
        """
        if image_cropped is None:
            # use the current data
            image_cropped = self.image_cropped.image
        if self.checkBox_auto_contrast.isChecked():
            levels = (image_cropped.min(), image_cropped.max())
        else:
            levels = (self.spinBox_contrast_min.value(),
                      self.spinBox_contrast_max.value())
        self.image_cropped.setImage(image_cropped, autoLevels=False,
                                    levels=levels)
        # make sure levels are shown in UI
        self.spinBox_contrast_min.blockSignals(True)
        self.spinBox_contrast_min.setValue(levels[0])
        self.spinBox_contrast_min.blockSignals(False)
        self.spinBox_contrast_max.blockSignals(True)
        self.spinBox_contrast_max.setValue(levels[1])
        self.spinBox_contrast_max.blockSignals(False)

    def update_scatter_plots(self):
        for plot, [featx, featy] in zip(self.scatter_plots, SCATTER_FEAT):
            with dclab.new_dataset(self.session.path) as ds:
                x, y = ds.get_downsampled_scatter(xax=featx,
                                                  yax=featy,
                                                  downsample=10000)
            plot.set_scatter(x, y)
            if LIMITS_FEAT[featx] is not None:
                plot.setXRange(*LIMITS_FEAT[featx])
            if LIMITS_FEAT[featy] is not None:
                plot.setYRange(*LIMITS_FEAT[featy])
            plot.setLabel('bottom', dclab.dfn.get_feature_label(featx))
            plot.setLabel('left', dclab.dfn.get_feature_label(featy))

    def set_fluorescence_traces(self, event_index):
        """Set the fluorescence traces on the widget"""
        self.legend_trace.clear()
        with dclab.new_dataset(self.session.path) as ds:
            if "trace" in ds:
                self.widget_trace.show()
                # time axis
                fl_samples = ds.config["fluorescence"]["samples per event"]
                fl_rate = ds.config["fluorescence"]["sample rate"]
                fl_time = np.arange(fl_samples) / fl_rate * 1e6
                # temporal range (min, max, fl-peak-maximum)
                range_t = [fl_time[0], fl_time[-1], 0]
                # fluorescence intensity
                range_fl = [0, 0]

                # Use this list to only show one trace type (raw or median)
                shown_traces = []

                for key in dclab.dfn.FLUOR_TRACES:
                    trid = key.split("_")[0]
                    if key in ds["trace"] and trid not in shown_traces:
                        shown_traces.append(trid)
                        # show the trace information
                        tracey = ds["trace"][key][event_index]  # trace data
                        range_fl[0] = min(range_fl[0], tracey.min())
                        range_fl[1] = max(range_fl[1], tracey.max())
                        self.trace_plots[key].setData(fl_time, tracey)
                        self.trace_plots[key].show()
                        # set legend name
                        ln = "{} {}".format(
                            "FL-{}".format(key[2]),
                            'median' if str(key[4]) == 'm' else 'raw')
                        self.legend_trace.addItem(self.trace_plots[key], ln)
                        self.legend_trace.update()
                    else:
                        self.trace_plots[key].hide()
                self.widget_trace.setXRange(*range_t[:2], padding=0)
                if range_fl[0] != range_fl[1]:
                    self.widget_trace.setYRange(*range_fl, padding=.01)
                self.widget_trace.setLimits(xMin=0, xMax=fl_time[-1])
            else:
                self.widget_trace.hide()


def get_contour_image(event_data):
    image = event_data["image"]
    mask = event_data["mask"]
    cellimg = np.copy(image)
    cellimg = cellimg.reshape(
        cellimg.shape[0], cellimg.shape[1], 1)
    cellimg = np.repeat(cellimg, 3, axis=2)
    # clip and convert to int
    cellimg = np.clip(cellimg, 0, 255)
    cellimg = np.require(cellimg, np.uint8, 'C')
    # Compute contour image from mask. If you are wondering
    # whether this is kosher, please take a look at issue #76:
    # https://github.com/ZELLMECHANIK-DRESDEN/dclab/issues/76
    cont = mask ^ binary_erosion(mask)
    # set red contour pixel values in original image
    cellimg[cont, 0] = int(255 * .7)
    cellimg[cont, 1] = 0
    cellimg[cont, 2] = 0
    return cellimg


def get_cropped_image(event_data):
    image = event_data["image"]
    pos_lat = int(event_data["pos_x_px"])
    width = image.shape[0]
    left = max(0, pos_lat - width // 2)
    left = min(left, image.shape[1] - width)
    right = left + width
    cropped = image[:, left:right]
    return cropped
