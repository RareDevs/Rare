from logging import getLogger

from PyQt5.QtCore import QProcess, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout
from qtawesome import icon

from legendary.core import LegendaryCore
from legendary.models.game import InstalledGame, Game
from rare.components.tabs.games.game_widgets.base_installed_widget import BaseInstalledWidget

logger = getLogger("GameWidget")


class InstalledListWidget(BaseInstalledWidget):
    proc: QProcess
    signal = pyqtSignal(str)
    update_game = pyqtSignal()

    def __init__(self, igame: InstalledGame, core: LegendaryCore, pixmap, offline, is_orign: bool = False, game: Game = None):
        super(InstalledListWidget, self).__init__(igame, core, pixmap, offline, is_orign, game)
        self.dev = self.game.metadata["developer"]
        if not is_orign:
            self.size = igame.install_size
            self.launch_params = igame.launch_parameters
        else:
            self.size = 0
            self.launch_params = ""

        self.layout = QHBoxLayout()

        ##Layout on the right
        self.childLayout = QVBoxLayout()

        self.layout.addWidget(self.image)

        play_icon = icon("ei.play")
        self.title_widget = QLabel(f"<h1>{self.game.app_title}</h1>")
        self.app_name_label = QLabel(self.game.app_name)
        self.launch_button = QPushButton(play_icon, self.tr("Launch") if not self.is_origin else self.tr("Link/Play"))
        self.launch_button.setObjectName("launch_game_button")
        self.launch_button.setFixedWidth(120)

        self.info = QPushButton("Info")
        self.info.clicked.connect(lambda: self.show_info.emit(self.game.app_name))
        self.info.setFixedWidth(80)

        self.childLayout.addWidget(self.title_widget)
        self.launch_button.clicked.connect(self.launch)

        self.childLayout.addWidget(self.launch_button)
        self.childLayout.addWidget(self.info)
        self.childLayout.addWidget(self.app_name_label)
        self.developer_label = QLabel(self.tr("Developer: ") + self.dev)
        self.childLayout.addWidget(self.developer_label)
        if not self.is_origin:
            self.version_label = QLabel("Version: " + str(self.igame.version))
            self.size_label = QLabel(f"{self.tr('Installed size')}: {round(self.size / (1024 ** 3), 2)} GB")

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
