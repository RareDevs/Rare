from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel


class LinuxSettings(QWidget):
    def __init__(self):
        super(LinuxSettings, self).__init__()
        self.layout = QVBoxLayout()

        self.title = QLabel("<h2>Linux settings (Wine, dxvk)</h2>")
        self.layout.addWidget(self.title)

        self.setLayout(self.layout)
