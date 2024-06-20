from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton

from rare.shared import GlobalSignalsSingleton
from rare.utils.misc import ExitCodes


class DebugSettings(QWidget):
    def __init__(self, parent=None):
        super(DebugSettings, self).__init__(parent=parent)

        self.raise_runtime_exception_button = QPushButton("Raise Exception", self)
        self.raise_runtime_exception_button.clicked.connect(self.raise_exception)
        self.restart_button = QPushButton("Restart", self)
        self.restart_button.clicked.connect(
            lambda: GlobalSignalsSingleton().application.quit.emit(ExitCodes.LOGOUT)
        )
        self.send_notification_button = QPushButton("Notify", self)
        self.send_notification_button.clicked.connect(self.send_notification)

        layout = QVBoxLayout(self)
        layout.addWidget(self.raise_runtime_exception_button)
        layout.addWidget(self.restart_button)
        layout.addWidget(self.send_notification_button)
        layout.addStretch(1)

    def raise_exception(self):
        raise RuntimeError("Debug Crash")

    def send_notification(self):
        GlobalSignalsSingleton().application.notify.emit("Debug", "Test notification")
