import os

from PyQt5.QtWidgets import QLineEdit, QPushButton, QLabel, QVBoxLayout, QDialog, QHBoxLayout
from legendary.models.game import Game


class InstallDialog(QDialog):
    def __init__(self, game: Game):
        super(InstallDialog, self).__init__()
        self.setWindowTitle(self.tr("Install Game"))
        self.layout = QVBoxLayout()
        self.yes = False
        self.install_path = QLineEdit(f"{os.path.expanduser('~')}/legendary")
        self.options = QLabel("Some Settings (Comming soon)")
        # self.layout.addWidget(self.options)

        self.layout.addStretch(1)
        self.yes_button = QPushButton(self.tr("Install game ") + game.app_title)
        self.yes_button.clicked.connect(self.close)
        self.cancel_button = QPushButton(self.tr("cancel"))

        self.layout.addWidget(self.options)
        self.layout.addWidget(self.install_path)

        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.yes_button)
        self.button_layout.addWidget(self.cancel_button)
        self.yes_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.cancel)
        self.layout.addLayout(self.button_layout)
        self.setLayout(self.layout)

    def get_data(self) -> dict:
        self.exec_()
        return {
            "install_path": self.install_path.text()
        } if self.yes else 0

    def accept(self):
        self.yes = True
        self.close()

    def cancel(self):
        self.yes = False
        self.close()
