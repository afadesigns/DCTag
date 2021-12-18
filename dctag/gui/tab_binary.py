import pkg_resources

import numpy as np
from PyQt5 import QtCore, QtWidgets, uic


class TabBinaryLabel(QtWidgets.QWidget):
    """Tab for doing binary classification"""
    def __init__(self, *args, **kwargs):
        super(TabBinaryLabel, self).__init__(*args, **kwargs)

        ui_file = pkg_resources.resource_filename(
            'dctag.gui', 'tab_binary.ui')
        uic.loadUi(ui_file, self)

        self.feature = "ml_score_abc"
        self.session = None
        self.event_index = 0

        # Signals
        self.pushButton_next.clicked.connect(self.on_event_button)
        self.pushButton_prev.clicked.connect(self.on_event_button)
        self.pushButton_yes.clicked.connect(self.on_event_button)
        self.pushButton_no.clicked.connect(self.on_event_button)

    def update_session(self, session):
        """Update this widget with the session info"""
        if self.session is not session:
            self.session = session
            self.event_index = 0
        if self.session is None:
            self.setEnabled(False)
        else:
            self.setEnabled(True)
            self.goto_event(self.event_index)

    def goto_event(self, index):
        if index < 0:
            self.goto_event(0)
            return
        elif index >= self.session.event_count:
            self.goto_event(self.session.event_count - 1)
            return

        self.event_index = index

        # enable/disable skip buttons
        self.pushButton_prev.setDisabled(index == 0)
        self.pushButton_next.setDisabled(index == self.session.event_count - 1)

        # handle previous and next score labels
        if index != 0 and self.feature:
            prev_score = self.session.get_score(self.feature, index - 1)
            if not np.isnan(prev_score):
                prev_score = "Yes" if prev_score else "No"
            self.label_score_prev.setText(f"{prev_score}")
        else:
            self.label_score_prev.setText("")

        if index != self.session.event_count - 1 and self.feature:
            next_score = self.session.get_score(self.feature, index + 1)
            if not np.isnan(next_score):
                next_score = "Yes" if next_score else "No"
            self.label_score_next.setText(f"{next_score}")
        else:
            self.label_score_next.setText("")

        # indicate current score label
        current_score = self.session.get_score(self.feature, index)
        if np.isnan(current_score):
            yes = "Yes"
            no = "No"
        elif current_score:
            yes = "[Yes]"
            no = "No"
        else:
            yes = "Yes"
            no = "[No]"
        self.pushButton_no.setText(no)
        self.pushButton_yes.setText(yes)

        # visualization
        self.widget_vis.set_event(self.session, index)

    @QtCore.pyqtSlot()
    def on_event_button(self):
        btn = self.sender()
        if btn is self.pushButton_next:
            self.goto_event(self.event_index + 1)
        elif btn is self.pushButton_prev:
            self.goto_event(self.event_index - 1)
        elif btn is self.pushButton_no:
            self.session.set_score(self.feature, self.event_index, False)
            self.goto_event(self.event_index + 1)
        elif btn is self.pushButton_yes:
            self.session.set_score(self.feature, self.event_index, True)
            self.goto_event(self.event_index + 1)
