import os

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QLineEdit, QPushButton, QCheckBox, QVBoxLayout, QWidget, QLabel

from Rare.utils import legendaryUtils


class ImportWidget(QWidget):
    signal = pyqtSignal(int)
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

        print("import")
        if self.use_lutris_button.isChecked():
            if legendaryUtils.auth_import(wine_prefix=wine_prefix,
                                          lutris=self.use_lutris_button.isChecked()):
                print("login successful")
                self.signal.emit(0)
            else:
                self.text.setText("Failed")
                self.import_button.setText("Das hat nicht funktioniert")


class LoginWidget(QWidget):
    def __init__(self):
        super(LoginWidget, self).__init__()
        self.open_browser_button = QPushButton("Open Browser to get sid")
        self.open_browser_button.clicked.connect(self.open_browser)
        self.sid_field = QLineEdit()
        self.sid_field.setPlaceholderText("Enter sid from the Browser")
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.login)

    def login(self):
        pass

    def open_browser(self):
        pass
