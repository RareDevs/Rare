import os

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit
from Rare.utils import legendaryUtils

class InstallDialog(QDialog):
    def __init__(self, game):
        super(InstallDialog, self).__init__()
        self.setWindowTitle("Install Game")
        self.layout = QVBoxLayout()
        self.yes = False
        self.install_path = QLineEdit(f"{os.path.expanduser('~')}/legendary")
        self.options = QLabel("Verschiedene Optionene")
        self.layout.addWidget(self.options)

        self.layout.addStretch(1)
        self.yes_button = QPushButton("Install")
        self.yes_button.clicked.connect(self.close)
        self.cancel_button = QPushButton("cancel")

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


class LoginDialog(QDialog):
    def __init__(self):
        super(LoginDialog, self).__init__()
        self.open_browser_button = QPushButton("Open Browser to get sid")
        self.open_browser_button.clicked.connect(self.open_browser)
        self.sid_field = QLineEdit()
        self.sid_field.setPlaceholderText("Enter sid from the Browser")
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.login)
        self.import_button = QPushButton("Or Import Login from EGL")
        self.import_button.clicked.connect(self.import_key)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.open_browser_button)
        self.layout.addWidget(self.sid_field)
        self.layout.addWidget(self.login_button)
        self.layout.addWidget(self.import_button)
        self.setLayout(self.layout)

    def open_browser(self):
        pass

    def login(self):
        legendaryUtils.auth(self.sid_field.text())

    def import_key(self):
        if legendaryUtils.auth_import():
            self.close()
        else:
            self.import_button.setText("Das hat nicht funktioniert")


class GameSettingsDialog(QDialog):
    def __init__(self):
        super(GameSettingsDialog, self).__init__()