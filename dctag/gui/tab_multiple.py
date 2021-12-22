import pkg_resources

import numpy as np
from PyQt5 import QtCore, QtWidgets, uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut

from .. import scores


class CheckableComboBox(QtWidgets.QComboBox):
    def __init__(self, *args, **kwargs):
        super(CheckableComboBox, self).__init__(*args, **kwargs)
        self._changed = False
        self.view().pressed.connect(self.handleItemPressed)

    def addItem(self, text, userData):
        super(CheckableComboBox, self).addItem(text, userData)
        item = self.model().item(self.count() - 1, self.modelColumn())
        item.setCheckState(Qt.Unchecked)

    def handleItemPressed(self, index):
        item = self.model().itemFromIndex(index)
        checked = item.checkState() == Qt.Checked
        item.setCheckState(Qt.Unchecked if checked else Qt.Checked)
        self._changed = True

    def hidePopup(self):
        if not self._changed:
            super(CheckableComboBox, self).hidePopup()
        self._changed = False

    def itemChecked(self, index):
        item = self.model().item(index, self.modelColumn())
        return item.checkState() == Qt.Checked

    def itemsCheckedData(self):
        data_checked = []
        for ii in range(self.count()):
            item = self.model().item(ii, self.modelColumn())
            if item.checkState() == Qt.Checked:
                # get the actual item
                data_checked.append(self.itemData(ii))
        return data_checked

    def setItemChecked(self, index, checked=False):
        item = self.model().item(index, self.modelColumn())
        item.setCheckState(Qt.Checked if checked else Qt.Unchecked)


class LabelButtonWidget(QtWidgets.QWidget):
    button_pressed = QtCore.pyqtSignal(str)

    def __init__(self, feature, *args, **kwargs):
        super(LabelButtonWidget, self).__init__(*args, **kwargs)
        self.feature = feature
        self.shortcut = None

        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.pushButton = QtWidgets.QPushButton("label")
        self.pushButton.setToolTip(scores.get_feature_label(feature))
        self.pushButton.pressed.connect(self.on_button)
        self.verticalLayout.addWidget(self.pushButton)
        self.comboBox = QtWidgets.QComboBox(self)
        shortcut = scores.get_feature_shortcut(feature)
        self.comboBox.addItem(shortcut)
        for sc in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            self.comboBox.addItem(sc)
        self.comboBox.currentTextChanged.connect(self.on_combobox)
        self.on_combobox(shortcut)  # initial shortcut
        self.verticalLayout.addWidget(self.comboBox)
        # Initialize button label
        self.set_score(np.nan)

    @QtCore.pyqtSlot()
    def on_button(self):
        self.button_pressed.emit(self.feature)

    @QtCore.pyqtSlot(str)
    def on_combobox(self, shortcut=None):
        if shortcut is None:
            shortcut = self.comboBox.currentText()
        seq = QKeySequence(shortcut)
        self.pushButton.setShortcut(seq)

    def set_score(self, score=np.nan):
        """Add square brackets in the button"""
        label = self.feature[-3:].upper()
        if score is True:
            label = f"[{label}]"
        elif score is False:
            label = f"!{label}"
        self.pushButton.setText(label)
        # Somehow necessary to re-enable the shortcut
        self.on_combobox(None)


class TabMultiClassLabel(QtWidgets.QWidget):
    """Tab for doing binary classification"""

    def __init__(self, *args, **kwargs):
        super(TabMultiClassLabel, self).__init__(*args, **kwargs)

        ui_file = pkg_resources.resource_filename(
            'dctag.gui', 'tab_multiple.ui')
        uic.loadUi(ui_file, self)

        self.session = None
        self.event_index = 0

        # populate ML scores combobox
        self.comboBox_score.clear()
        for feat in scores.get_dctag_score_dict("blood"):
            self.comboBox_score.addItem(scores.get_feature_label(feat), feat)

        # signals
        self.pushButton_start.clicked.connect(self.on_start)
        self.pushButton_next.clicked.connect(self.on_event_button)
        self.pushButton_prev.clicked.connect(self.on_event_button)
        self.pushButton_fast_next.clicked.connect(self.on_event_button)
        self.pushButton_fast_prev.clicked.connect(self.on_event_button)

        # keyboard shortcuts
        self.shortcuts = []
        for button, shortcuts in [
            [self.pushButton_next, ["Right"]],
            [self.pushButton_prev, ["Left"]],
            [self.pushButton_fast_prev, ["Shift+Left"]],
            [self.pushButton_fast_next, ["Shift+Right"]],
        ]:
            for seq in shortcuts:
                sc = QShortcut(QKeySequence(seq), self)
                sc.activated.connect(button.click)
                # include original ToolTip
                tt = button.toolTip()
                tt = tt + "; " if tt else ""
                button.setToolTip(f"{tt}Shortcuts: {', '.join(shortcuts)}")
                self.shortcuts.append(sc)  # keep a reference

        #: list of buttons for labeling
        self.label_buttons = []

    @property
    def features(self):
        datas = self.comboBox_score.itemsCheckedData()
        return sorted(datas)

    def update_session(self, session):
        """Update this widget with the session info"""
        # Whenever the user leaves and comes back to this tab, he has
        # to lock-in again to label data.
        self.lock_out()
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
        if index != 0 and self.features:
            candidates = self.session.get_scores_true(index - 1)
            scs = [f for f in candidates if f in self.session.linked_features]
            label = " ".join([s[-3:] for s in scs]).upper()
            self.label_score_prev.setText(label)
        else:
            self.label_score_prev.setText("")

        if index != self.session.event_count - 1 and self.features:
            candidates = self.session.get_scores_true(index + 1)
            scs = [f for f in candidates if f in self.session.linked_features]
            label = " ".join([s[-3:] for s in scs]).upper()
            self.label_score_next.setText(label)
        else:
            self.label_score_next.setText("")

        # indicate current score label
        if self.features:
            for button in self.label_buttons:
                score = self.session.get_score(button.feature, index)
                button.set_score(score)

        # update progress bar
        if self.features:
            fscores = self.session.scores_cache.get(self.features[0], [])
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
        lids = [scores.get_feature_label(ft)[-3:] for ft in self.features]
        main.set_title("-".join(lids).upper())
        # clear current layout of label buttons
        for widgetrm in self.label_buttons:
            widgetrm.deleteLater()
            widgetrm.setParent(None)
        self.label_buttons.clear()
        # populate the score buttons and connect signals
        for feat in self.features:
            fbutton = LabelButtonWidget(feat)
            fbutton.button_pressed.connect(self.on_event_button_feature)
            self.layout_label_buttons.addWidget(fbutton)
            self.label_buttons.append(fbutton)

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
        elif btn is self.pushButton_fast_prev:
            for ii in range(1, self.event_index):
                new_index = self.event_index - ii
                curscores = self.session.get_scores_true(new_index)
                if set(self.features).isdisjoint(set(curscores)):
                    break
            else:
                new_index = 0
            self.goto_event(new_index)
        elif btn is self.pushButton_fast_next:
            start = min(self.event_index + 1, self.session.event_count - 1)
            for new_index in range(start, self.session.event_count):
                curscores = self.session.get_scores_true(new_index)
                if set(self.features).isdisjoint(set(curscores)):
                    break
            else:
                new_index = self.session.event_count - 1
            self.goto_event(new_index)

    @QtCore.pyqtSlot(str)
    def on_event_button_feature(self, feature):
        self.session.set_score(feature, self.event_index, True)
        self.goto_event(self.event_index + 1)

    @QtCore.pyqtSlot()
    def on_start(self):
        if not self.features:
            QtWidgets.QMessageBox.warning(
                self,
                "No score features chosen.",
                "Please select ML score features in the combobox first!"
                )
        else:
            self.session.linked_features = self.features
            self.session.autocomplete_linked_features()
            self.lock_in()
            self.goto_event(0)
