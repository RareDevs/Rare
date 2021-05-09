import os
from logging import getLogger

from PyQt5.QtCore import QProcess, pyqtSignal, Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout
from qtawesome import icon

from custom_legendary.core import LegendaryCore
from custom_legendary.models.game import InstalledGame
from rare.components.tabs.games.game_widgets.base_installed_widget import BaseInstalledWidget

logger = getLogger("GameWidget")


class InstalledListWidget(BaseInstalledWidget):
    proc: QProcess
    signal = pyqtSignal(str)
    update_game = pyqtSignal()

    def __init__(self, game: InstalledGame, core: LegendaryCore, pixmap, offline):
        super(InstalledListWidget, self).__init__(game, core, pixmap, offline)
        self.dev = core.get_game(self.igame.app_name).metadata["developer"]
        self.size = game.install_size
        self.launch_params = game.launch_parameters

        self.layout = QHBoxLayout()

        ##Layout on the right
        self.childLayout = QVBoxLayout()

        if self.pixmap:
            self.pixmap = self.pixmap.scaled(180, 240, transformMode=Qt.SmoothTransformation)
            self.image = QLabel()
            self.image.setPixmap(self.pixmap)
            self.layout.addWidget(self.image)

        play_icon = icon("ei.play", color="white")
        self.title_widget = QLabel(f"<h1>{self.igame.title}</h1>")
        self.app_name_label = QLabel(self.igame.app_name)
        self.launch_button = QPushButton(play_icon, self.tr("Launch"))
        self.launch_button.setObjectName("launch_game_button")
        self.launch_button.setFixedWidth(120)

        self.info = QPushButton("Info")
        self.info.clicked.connect(lambda: self.show_info.emit(self.igame.app_name))
        self.info.setFixedWidth(80)

        self.launch_button.clicked.connect(self.launch)
        if os.name != "nt":
            self.wine_rating = QLabel("Wine Rating: " + self.get_rating())
        self.developer_label = QLabel(self.tr("Developer: ") + self.dev)
        self.version_label = QLabel("Version: " + str(self.igame.version))
        self.size_label = QLabel(f"{self.tr('Installed size')}: {round(self.size / (1024 ** 3), 2)} GB")
        self.childLayout.addWidget(self.title_widget)
        self.childLayout.addWidget(self.launch_button)
        self.childLayout.addWidget(self.info)
        self.childLayout.addWidget(self.app_name_label)
        self.childLayout.addWidget(self.developer_label)

        # if os.name != "nt":
        #    self.childLayout.addWidget(self.wine_rating)
        self.childLayout.addWidget(self.version_label)
        self.childLayout.addWidget(self.size_label)

        self.info_label = QLabel("")
        self.childLayout.addWidget(self.info_label)
        # self.childLayout.addWidget(QPushButton("Settings"))
        # self.childLayout.addWidget(QPushButton("Uninstall"))
        self.childLayout.addStretch(1)
        self.layout.addLayout(self.childLayout)
        self.layout.addStretch(1)
        self.setLayout(self.layout)

    def launch(self):
        if not self.game_running:
            super(InstalledListWidget, self).launch(skip_version_check=self.update_available)

    def get_rating(self) -> str:
        return "gold"  # TODO
