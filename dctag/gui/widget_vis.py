import functools
import pkg_resources

import numpy as np
from PyQt5 import QtWidgets, uic
from scipy.ndimage import binary_erosion

import dclab


#: dictionary with default axes limits for these features
LIMITS_FEAT = {
    "deform": [0.0, 0.5],
    "area_um": [10, 130],
    "bright_avg": [70, 140],
    "bright_sd": [5, 35],
}

#: list with scatter plot axis features (there are three)
SCATTER_FEAT = [
    ["area_um", "deform"],
    ["area_um", "bright_avg"],
    ["bright_sd", "bright_avg"],
]


class WidgetVisualize(QtWidgets.QWidget):
    """Widget for visualizing data"""
    def __init__(self, *args, **kwargs):
        super(WidgetVisualize, self).__init__(*args, **kwargs)

        ui_file = pkg_resources.resource_filename(
            'dctag.gui', 'widget_vis.ui')
        uic.loadUi(ui_file, self)

        self.session = None

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
            # clear the event image cache
            self.get_event_data.cache_clear()
            self.get_feature_data.cache_clear()
            self.session = session
            self.update_scatter_plots()
        if self.session is None:
            self.setEnabled(False)
            self.groupBox_event.setTitle("Event")
        else:
            self.setEnabled(True)
            self.groupBox_event.setTitle(f"Event {event_index}")
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
            self.image_cropped.setImage(image_cropped)
            # Plot event in the scatter plots
            for plot, [featx, featy] in zip(
                    [self.scatter_1, self.scatter_2, self.scatter_3],
                    SCATTER_FEAT):
                plot.set_event(data[featx], data[featy])

    def update_scatter_plots(self):
        for plot, [featx, featy] in zip(
                [self.scatter_1, self.scatter_2, self.scatter_3],
                SCATTER_FEAT):
            plot.set_scatter(self.get_feature_data(featx),
                             self.get_feature_data(featy))
            plot.setXRange(*LIMITS_FEAT[featx])
            plot.setYRange(*LIMITS_FEAT[featy])
            plot.setLabel('bottom', dclab.dfn.get_feature_label(featx))
            plot.setLabel('left', dclab.dfn.get_feature_label(featy))


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
