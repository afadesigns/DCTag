import pkg_resources

import numpy as np
from PyQt5 import QtCore, QtWidgets, uic
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut

from .. import scores


class TabBinaryLabel(QtWidgets.QWidget):
    """Tab for doing binary classification"""

    def __init__(self, *args, **kwargs):
        super(TabBinaryLabel, self).__init__(*args, **kwargs)

        ui_file = pkg_resources.resource_filename(
            'dctag.gui', 'tab_binary.ui')
        uic.loadUi(ui_file, self)

        self.session = None
        self.event_index = 0

        # settings
        self.settings = QtCore.QSettings()

        # populate ML scores combobox
        self.comboBox_score.clear()
        for feat in scores.get_dctag_label_dict(
                name=self.settings.value("labeling group", "ml_scores_blood")):
            flabel = f"{scores.get_feature_label(feat)} [{feat[-3:].upper()}]"
            self.comboBox_score.addItem(flabel, feat)

        # signals
        self.pushButton_start.clicked.connect(self.on_start)
        self.pushButton_next.clicked.connect(self.on_event_button)
        self.pushButton_prev.clicked.connect(self.on_event_button)
        self.pushButton_yes.clicked.connect(self.on_event_button)
        self.pushButton_no.clicked.connect(self.on_event_button)
        self.pushButton_fast_next.clicked.connect(self.on_event_button)
        self.pushButton_fast_prev.clicked.connect(self.on_event_button)
        self.toolButton_reset.clicked.connect(self.on_event_button)
        self.spinBox_jump_to.valueChanged.connect(self.on_jump_to)

        self.toolButton_reset.setIcon(self.style().standardIcon(
            QtWidgets.QStyle.SP_TrashIcon))
        self.toolButton_reset.repaint()

        # keyboard shortcuts
        self.shortcuts = []
        for button, shortcuts in [
            [self.pushButton_yes, ["Up", "J", "Y"]],
            [self.pushButton_no, ["Down", "F", "N"]],
            [self.pushButton_next, ["Right"]],
            [self.pushButton_prev, ["Left"]],
            [self.pushButton_fast_prev, ["Shift+Left"]],
            [self.pushButton_fast_next, ["Shift+Right"]],
        ]:
            for seq in shortcuts:
                sc = QShortcut(QKeySequence(seq), self)
                sc.activated.connect(button.click)
                self.shortcuts.append(sc)  # keep a reference
            # append shortcuts tool tip to original tool tip
            tt = button.toolTip()
            tt = tt + "; " if tt else ""
            button.setToolTip(f"{tt}Shortcuts: {', '.join(shortcuts)}")

    @property
    def feature(self):
        return self.comboBox_score.currentData()

    def update_session(self, session):
        """Update this widget with the session info"""
        # Whenever the user leaves and comes back to this tab, he has
        # to lock-in again to label data.
        self.lock_out()
        if self.session is not session:
            self.session = session
            self.event_index = 0
        if self.session:
            self.setEnabled(True)
            self.spinBox_jump_to.setMaximum(self.session.event_count)
            self.goto_event(self.event_index)
        else:
            self.setEnabled(False)
            self.widget_vis.reset(reset_plots=True)

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
        yes = "Yes"
        no = "No"
        if self.feature:
            current_score = self.session.get_score(self.feature, index)
            if not np.isnan(current_score):
                if current_score:
                    yes = "[Yes]"
                else:
                    no = "[No]"
        self.pushButton_no.setText(no)
        self.pushButton_yes.setText(yes)

        # update spinBox_jump_to
        self.spinBox_jump_to.blockSignals(True)
        self.spinBox_jump_to.setValue(self.event_index + 1)
        self.spinBox_jump_to.blockSignals(False)

        # update progress bar
        if self.feature:
            fscores = self.session.scores_cache.get(self.feature, [])
            num_rated = np.sum(~np.isnan(fscores))
            perc = int(np.floor(num_rated / self.session.event_count * 100))
            self.progressBar.setValue(perc)

        # visualization
        self.widget_vis.set_event(self.session, index)

    def lock_in(self):
        """Begin labeling"""
        self.pushButton_start.setVisible(False)
        self.comboBox_score.setEnabled(False)
        self.progressBar.setVisible(True)
        self.widget_label_keys.setEnabled(True)
        main = QtWidgets.QApplication.activeWindow()
        assert self.feature is not None, "feature not set!"
        label = scores.get_feature_label(self.feature)
        main.set_title(f"{self.feature[-3:].upper()}: {label}")

    def lock_out(self):
        """Stop labeling"""
        self.pushButton_start.setVisible(True)
        self.comboBox_score.setEnabled(True)
        self.progressBar.setVisible(False)
        self.widget_label_keys.setEnabled(False)

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
        elif btn is self.pushButton_fast_prev:
            for ii in range(1, self.event_index):
                new_index = self.event_index - ii
                if np.isnan(self.session.get_score(self.feature, new_index)):
                    break
            else:
                new_index = 0
            self.goto_event(new_index)
        elif btn is self.pushButton_fast_next:
            start = min(self.event_index + 1, self.session.event_count - 1)
            for new_index in range(start, self.session.event_count):
                if np.isnan(self.session.get_score(self.feature, new_index)):
                    break
            else:
                new_index = self.session.event_count - 1
            self.goto_event(new_index)
        elif btn is self.toolButton_reset:
            self.session.reset_score(self.feature, self.event_index)
            self.goto_event(self.event_index + 1)

    @QtCore.pyqtSlot(int)
    def on_jump_to(self, event_index):
        self.goto_event(event_index - 1)

    @QtCore.pyqtSlot()
    def on_start(self):
        self.session.linked_features = []
        self.lock_in()
        self.goto_event(0)
