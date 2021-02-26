import os
from getpass import getuser

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QButtonGroup, QRadioButton
from legendary.core import LegendaryCore


class ImportWidget(QWidget):
    success = pyqtSignal(str)

    def __init__(self, core: LegendaryCore):
        super(ImportWidget, self).__init__()
        self.layout = QVBoxLayout()
        self.core = core

        self.back = QPushButton("Back")
        self.layout.addWidget(self.back)
        self.title = QLabel("<h3>Import existing Login session</h3>")
        self.title.setWordWrap(True)
        self.layout.addWidget(self.title)
        appdata_paths = self.get_appdata_paths()

        if len(appdata_paths) == 0:
            self.infoText = QLabel("Found Installations here. \n<b>Note:</b> You will get logged out there")
            self.infoText.setWordWrap(True)
            self.layout.addWidget(self.infoText)

        else:
            self.btn_group = QButtonGroup()
            for i, p in enumerate(appdata_paths):
                radio_button = QRadioButton(p)
                if i == 0:
                    radio_button.setChecked(True)
                self.btn_group.addButton(radio_button)
                self.layout.addWidget(radio_button)

            self.appdata_path_text = QLabel(self.tr("Appdata path: ") + str(self.core.egl.appdata_path))
            self.appdata_path_text.setWordWrap(True)
            self.login_text = QLabel("")
            # self.layout.addWidget(self.btn_group)
            self.layout.addWidget(self.login_text)
            self.layout.addStretch(1)
            self.import_btn = QPushButton("Import")
            self.layout.addWidget(self.import_btn)

        self.setLayout(self.layout)

    def get_appdata_paths(self) -> list:
        if self.core.egl.appdata_path:
            return [self.core.egl.appdata_path]

        else:  # Linux
            wine_paths = []
            possible_wine_paths = [os.path.expanduser('~/Games/epic-games-store/'),
                                   os.path.expanduser('~/.wine/')]
            if os.environ.get("WINEPREFIX"):
                possible_wine_paths.append(os.environ.get("WINEPREFIX"))

            for i in possible_wine_paths:
                if os.path.exists(i):
                    if os.path.exists(os.path.join(i, "drive_c/users", getuser(),
                                                   'Local Settings/Application Data/EpicGamesLauncher',
                                                   'Saved/Config/Windows')):
                        wine_paths.append(i)

            if len(wine_paths) > 0:
                appdata_dirs = [
                    os.path.join(i, "drive_c/users", getuser(), 'Local Settings/Application Data/EpicGamesLauncher',
                                 'Saved/Config/Windows') for i in wine_paths]
                return appdata_dirs
        return []
