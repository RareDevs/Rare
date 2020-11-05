import os
import webbrowser
from logging import getLogger

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QLineEdit, QPushButton, QCheckBox, QVBoxLayout, QWidget, QLabel

from Rare.utils import legendaryUtils

logger = getLogger(name="login")


class ImportWidget(QWidget):
    signal = pyqtSignal()

    def __init__(self):
        super(ImportWidget, self).__init__()

        self.layout = QVBoxLayout()

        self.use_lutris_button = QCheckBox("Use from Lutris")
        self.insert_wine_prefix = QLineEdit()
        self.info_text = QLabel("Use login from an existing EGL installation. You will logged out there")

        self.layout.addWidget(self.info_text)
        if os.name != "nt":
            self.insert_wine_prefix.setPlaceholderText("Or insert path of wineprefix")
            self.layout.addWidget(self.use_lutris_button)
            self.layout.addWidget(self.insert_wine_prefix)

        self.import_button = QPushButton("Import Login from EGL")
        self.import_button.clicked.connect(self.import_key)
        self.text = QLabel()
        self.layout.addWidget(self.text)

        self.layout.addWidget(self.import_button)

        self.setLayout(self.layout)

    def import_key(self):
        wine_prefix = self.insert_wine_prefix.text()
        if wine_prefix == "":
            wine_prefix = None

        logger.info("Import Key")
        if self.use_lutris_button.isChecked():
            if legendaryUtils.auth_import(wine_prefix=wine_prefix,
                                          lutris=self.use_lutris_button.isChecked()):
                logger.info("Successful")
                self.signal.emit()
            else:
                self.text.setText("Failed")
                self.import_button.setText("Das hat nicht funktioniert")


class LoginWidget(QWidget):
    signal = pyqtSignal()

    def __init__(self):
        super(LoginWidget, self).__init__()
        self.layout = QVBoxLayout()
        self.open_browser_button = QPushButton("Open Browser to get sid")
        self.open_browser_button.clicked.connect(self.open_browser)
        self.sid_field = QLineEdit()
        self.sid_field.setPlaceholderText("Enter sid from the Browser")
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.login)
        self.login_text = QLabel("")
        self.layout.addWidget(self.open_browser_button)
        self.layout.addWidget(self.sid_field)
        self.layout.addWidget(self.login_button)
        self.layout.addWidget(self.login_text)
        self.setLayout(self.layout)

    def login(self):
        print("Try to login")
        self.login_text.setText("Try to login")
        self.login_button.setDisabled(True)
        if legendaryUtils.login(self.sid_field.text()):
            self.signal.emit()
        else:
            self.login_text.setText("Login failed")
            self.login_button.setDisabled(False)

    def open_browser(self):
        webbrowser.open(
            'https://www.epicgames.com/id/login?redirectUrl=https%3A%2F%2Fwww.epicgames.com%2Fid%2Fapi%2Fredirect'
        )
