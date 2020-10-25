from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel


class InstallDialog(QDialog):
    def __init__(self, game):
        super(InstallDialog, self).__init__()
        self.setWindowTitle("Install Game")
        self.layout = QVBoxLayout()


        self.options = QLabel("Verschiedene Optionene")
        self.layout.addWidget(self.options)
       
        self.layout.addStretch(1)
        self.yes_button = QPushButton("Install")
        self.cancel_button = QPushButton("cancel")

        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.yes_button)
        self.button_layout.addWidget(self.cancel_button)
        self.cancel_button.clicked.connect(self.exit)
        self.layout.addLayout(self.button_layout)
        self.setLayout(self.layout)
