import functools
import pkg_resources

from PyQt5 import QtWidgets, uic

import dclab


class WidgetVisualize(QtWidgets.QWidget):
    """Widget for visualizing data"""
    def __init__(self, *args, **kwargs):
        super(WidgetVisualize, self).__init__(*args, **kwargs)

        ui_file = pkg_resources.resource_filename(
            'dctag.gui', 'widget_vis.ui')
        uic.loadUi(ui_file, self)

        self.session = None

    @functools.lru_cache(maxsize=50)
    def get_event_data(self, index):
        # is this too slow?
        with dclab.new_dataset(self.session.path) as ds:
            data = {"image": ds["image"][index],
                    "contour": ds["contour"][index]
                    }
        return data

    def set_event(self, session, event_index):
        if self.session is not session:
            # clear the event image cache
            self.get_event_data.cache_clear()
            self.session = session
        if self.session is None:
            self.setEnabled(False)
            self.groupBox_event.setTitle("Event")
        else:
            self.setEnabled(True)
            self.groupBox_event.setTitle(f"Event {event_index}")
            self.session = session
            data = self.get_event_data(event_index)
            # Plot the channel images
            self.image_channel.setImage(data["image"])
            # TODO:
            # - plot one image with contour
            # - plot square cutout in right plot
            # Plot the scatter plots
            # TODO:
            # - scatter plots should be plotted initially
            # - only position of current index should be changed (fast)
