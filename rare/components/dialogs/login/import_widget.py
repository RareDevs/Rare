import os
from getpass import getuser
from logging import getLogger

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QButtonGroup, QRadioButton

from custom_legendary.core import LegendaryCore

logger = getLogger("Import")


class ImportWidget(QWidget):
    success = pyqtSignal()

    def __init__(self, core: LegendaryCore):
        super(ImportWidget, self).__init__()
        self.layout = QVBoxLayout()
        self.core = core

        self.back = QPushButton("Back")
        self.layout.addWidget(self.back)
        self.title = QLabel("<h3>Import existing Login session</h3>")
        self.title.setWordWrap(True)
        self.layout.addWidget(self.title)
        self.infoText = QLabel(
            "Found Installations here. \nPlease select prefix, where Epic Games Launcher is installed\nNote: You will get logged out there")
        self.infoText.setWordWrap(True)
        self.layout.addWidget(self.infoText)
        self.import_button = QPushButton(self.tr("Import"))
        self.data_path = ""
        if os.name == "nt":

            if not self.core.egl.appdata_path and os.path.exists(
                    os.path.expandvars("%LOCALAPPDATA%/EpicGamesLauncher/Saved/Config/Windows")):
                self.core.egl.appdata_path = os.path.expandvars("%LOCALAPPDATA%/EpicGamesLauncher/Saved/Config/Windows")

            if not self.core.egl.appdata_path:
                self.text = QLabel(self.tr("Could not find EGL program data"))

            else:
                self.text = QLabel(self.tr("Found EGL program Data. Do you want to import them?"))

            self.layout.addWidget(self.text)

        # Linux
        else:
            self.radio_buttons = []
            prefixes = self.get_wine_prefixes()
            if len(prefixes) == 0:
                self.infoText.setText(self.tr("Could not find any Epic Games login data"))
                self.import_button.setDisabled(True)
            else:
                self.btn_group = QButtonGroup()
                for i in prefixes:
                    radio_button = QRadioButton(i)
                    self.radio_buttons.append(radio_button)
                    self.btn_group.addButton(radio_button)
                    self.layout.addWidget(radio_button)
                    radio_button.toggled.connect(self.toggle_radiobutton)

        self.login_text = QLabel("")
        self.layout.addWidget(self.login_text)
        self.layout.addWidget(self.import_button)
        self.import_button.clicked.connect(self.import_login_data)

        self.setLayout(self.layout)

    def toggle_radiobutton(self):
        if self.sender().isChecked():
            self.data_path = self.sender().text()

    def get_wine_prefixes(self):
        possible_prefixes = [
            os.path.expanduser("~/.wine"),
            os.path.expanduser("~/Games/epic-games-store")
        ]
        prefixes = []
        for i in possible_prefixes:
            if os.path.exists(os.path.join(i, "drive_c/users", getuser(),
                                           "Local Settings/Application Data/EpicGamesLauncher/Saved/Config/Windows")):
                prefixes.append(i)
        return prefixes

    def import_login_data(self):
        self.import_button.setText(self.tr("Loading..."))
        self.import_button.setDisabled(True)
        if os.name != "nt":
            self.core.egl.appdata_path = os.path.join(self.data_path,
                                                      f"drive_c/users/{getuser()}/Local Settings/Application Data/EpicGamesLauncher/Saved/Config/Windows")
        try:
            if self.core.auth_import():
                logger.info(f"Logged in as {self.core.lgd.userdata['displayName']}")
                self.success.emit()
            else:
                logger.warning("Failed to import existing session")
        except Exception as e:
            logger.warning(e)

        logger.warning("Error: No valid session found")
        self.login_text.setText(self.tr("Error: No valid session found"))
        self.import_button.setText(self.tr("Import"))
        self.import_button.setDisabled(False)
