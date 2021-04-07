from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QGroupBox


class SettingsWidget(QGroupBox):
    def __init__(self, text: str, widget: QWidget, accept_button: QPushButton = None):
        super(SettingsWidget, self).__init__()
        self.setObjectName("settings_widget")
        self.setStyleSheet("""QGroupBox{border: 1px solid gray;
                            border-radius: 3px;
                            margin-top: 1ex;}""")
        self.layout = QVBoxLayout()
        self.info_text = QLabel("")
        self.setTitle(text)
        self.layout.addWidget(widget)
        if accept_button:
            self.layout.addWidget(accept_button)
        self.layout.addWidget(self.info_text)
        self.setLayout(self.layout)
