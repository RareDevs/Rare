from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton


class DebugSettings(QWidget):
    def __init__(self):
        super(DebugSettings, self).__init__()
        self.setLayout(QVBoxLayout())

        self.raise_runtime_exception_button = QPushButton("Raise Exception")
        self.layout().addWidget(self.raise_runtime_exception_button)
        self.raise_runtime_exception_button.clicked.connect(self.raise_exception)

        self.layout().addStretch(1)

    def raise_exception(self):
        raise RuntimeError("Debug Crash")
