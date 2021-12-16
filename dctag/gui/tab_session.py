import pkg_resources
from PyQt5 import QtWidgets, uic

import dclab


class TabSessionInfo(QtWidgets.QWidget):
    """Tab that displays .rtdc file DCTagSession information"""
    def __init__(self, *args, **kwargs):
        super(TabSessionInfo, self).__init__(*args, **kwargs)

        ui_file = pkg_resources.resource_filename(
            'dctag.gui', 'tab_session.ui')
        uic.loadUi(ui_file, self)

    def update_session(self, session):
        """Update this widget with the session info"""
        if session is None:
            user = ""
            logs = "No session."
        else:
            user = session.user
            with session.score_lock:
                try:
                    with dclab.new_dataset(session.path) as ds:
                        logs = "\n".join(ds.logs["dctag-history"])
                except BaseException:
                    logs = f"Cannot get logs from '{session.path}'!"
        self.plainTextEdit_logs.setPlainText(logs)
        self.label_username.setText(user)
        self.label_num_sessions.setText(f"{logs.count('new session')}")
