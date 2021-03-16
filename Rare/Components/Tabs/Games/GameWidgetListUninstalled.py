import os
from logging import getLogger

from PyQt5.QtCore import pyqtSignal, QSettings
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton

from Rare.Components.Dialogs.InstallDialog import InstallDialog
from Rare.utils.Models import InstallOptions
from custom_legendary.core import LegendaryCore

logger = getLogger("Game")


class UninstalledGameWidget(QWidget):
    install_game = pyqtSignal(InstallOptions)

    def __init__(self, core: LegendaryCore, game):
        super(UninstalledGameWidget, self).__init__()
        self.title = game.app_title
        self.app_name = game.app_name
        self.version = game.app_version
        self.layout = QHBoxLayout()
        self.game = game
        self.core = core
        settings = QSettings()
        IMAGE_DIR = settings.value("img_dir", os.path.expanduser("~/.cache/rare"), type=str)

        if os.path.exists(f"{IMAGE_DIR}/{game.app_name}/UninstalledArt.png"):
            pixmap = QPixmap(f"{IMAGE_DIR}/{game.app_name}/UninstalledArt.png")
            pixmap = pixmap.scaled(120, 160)
            self.image = QLabel()
            self.image.setPixmap(pixmap)
            self.layout.addWidget(self.image)

        self.child_layout = QVBoxLayout()

        self.title_label = QLabel(f"<h2>{self.title}</h2>")
        self.app_name_label = QLabel(f"App Name: {self.app_name}")
        self.version_label = QLabel(f"Version: {self.version}")
        self.install_button = QPushButton(self.tr("Install"))
        self.install_button.setFixedWidth(120)
        self.install_button.clicked.connect(self.install)

        self.child_layout.addWidget(self.title_label)
        self.child_layout.addWidget(self.app_name_label)
        self.child_layout.addWidget(self.version_label)
        self.child_layout.addWidget(self.install_button)
        self.child_layout.addStretch(1)
        self.layout.addLayout(self.child_layout)

        self.layout.addStretch(1)
        self.setLayout(self.layout)

    def install(self):
        logger.info("Install " + self.game.app_title)

        infos = InstallDialog().get_information()
        if infos != 0:
            path, max_workers = infos
            self.install_game.emit(InstallOptions(
                app_name=self.game.app_name,
                path=path,
                max_workers=max_workers,
                repair=False))
        # wait for update of legendary to get progress
