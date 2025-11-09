import importlib.resources

from PyQt6 import QtWidgets, uic

import dclab


class TabSessionInfo(QtWidgets.QWidget):
    """Tab that displays .rtdc file DCTagSession information"""

    def __init__(self, *args, **kwargs):
        super(TabSessionInfo, self).__init__(*args, **kwargs)

        ref = importlib.resources.files("dctag.gui") / "tab_session.ui"
        with importlib.resources.as_file(ref) as path_ui:
            uic.loadUi(path_ui, self)

    def update_session(self, session):
        """Update this widget with the session info"""
        if not session:
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
