from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton

from rare.shared import GlobalSignalsSingleton


class DebugSettings(QWidget):
    def __init__(self):
        super(DebugSettings, self).__init__()
        self.setLayout(QVBoxLayout())

        self.raise_runtime_exception_button = QPushButton("Raise Exception")
        self.layout().addWidget(self.raise_runtime_exception_button)
        self.raise_runtime_exception_button.clicked.connect(self.raise_exception)
        self.restart_button = QPushButton("Restart")
        self.layout().addWidget(self.restart_button)
        self.restart_button.clicked.connect(lambda: GlobalSignalsSingleton().exit_app.emit(-133742))

        self.layout().addStretch(1)

    def raise_exception(self):
        raise RuntimeError("Debug Crash")
