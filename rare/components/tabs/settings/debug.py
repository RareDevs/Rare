from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton

from rare.shared import GlobalSignalsSingleton
from rare.utils.misc import ExitCodes


class DebugSettings(QWidget):
    def __init__(self, parent=None):
        super(DebugSettings, self).__init__(parent=parent)

        self.raise_runtime_exception_button = QPushButton("Raise Exception")
        self.raise_runtime_exception_button.clicked.connect(self.raise_exception)
        self.restart_button = QPushButton("Restart")
        self.restart_button.clicked.connect(
            lambda: GlobalSignalsSingleton().application.quit.emit(ExitCodes.LOGOUT)
        )

        layout = QVBoxLayout(self)
        layout.addWidget(self.raise_runtime_exception_button)
        layout.addWidget(self.restart_button)
        layout.addStretch(1)

    def raise_exception(self):
        raise RuntimeError("Debug Crash")
