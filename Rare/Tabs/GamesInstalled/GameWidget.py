import os
from logging import getLogger

from PyQt5.QtCore import QProcess, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QStyle, QVBoxLayout
from legendary.core import LegendaryCore
from legendary.models.game import InstalledGame

from Rare.Tabs.GamesInstalled.GameSettingsDialog import GameSettingsDialog
from Rare.utils import legendaryUtils
from Rare.utils.RareConfig import IMAGE_DIR

logger = getLogger("GameWidget")


class GameWidget(QWidget):
    proc: QProcess
    signal = pyqtSignal(str)

    # TODO Repair
    def __init__(self, game: InstalledGame, core: LegendaryCore):
        super(GameWidget, self).__init__()
        self.core = core
        self.game = game
        self.dev = core.get_game(self.game.app_name).metadata["developer"]
        self.title = game.title
        self.app_name = game.app_name
        self.version = game.version
        self.size = game.install_size
        self.launch_params = game.launch_parameters
        # self.dev =
        self.game_running = False
        self.layout = QHBoxLayout()
        if os.path.exists(f"{IMAGE_DIR}/{game.app_name}/FinalArt.png"):
            pixmap = QPixmap(f"{IMAGE_DIR}/{game.app_name}/FinalArt.png")
        elif os.path.exists(f"{IMAGE_DIR}/{game.app_name}/DieselGameBoxTall.png"):
            pixmap = QPixmap(f"{IMAGE_DIR}/{game.app_name}/DieselGameBoxTall.png")
        elif os.path.exists(f"{IMAGE_DIR}/{game.app_name}/DieselGameBoxLogo.png"):
            pixmap = QPixmap(f"{IMAGE_DIR}/{game.app_name}/DieselGameBoxLogo.png")
        else:
            logger.warning(f"No Image found: {self.game.title}")
            pixmap = None
        if pixmap:
            pixmap = pixmap.scaled(180, 240)
            self.image = QLabel()
            self.image.setPixmap(pixmap)
            self.layout.addWidget(self.image)

        ##Layout on the right
        self.childLayout = QVBoxLayout()
        play_icon = self.style().standardIcon(getattr(QStyle, 'SP_MediaPlay'))
        settings_icon = self.style().standardIcon(getattr(QStyle, 'SP_DirIcon'))
        self.title_widget = QLabel(f"<h1>{self.title}</h1>")
        self.app_name_label = QLabel(self.app_name)
        self.launch_button = QPushButton(play_icon, self.tr("Launch"))
        self.launch_button.setObjectName("launch_game_button")
        self.launch_button.setFixedWidth(120)

        self.launch_button.clicked.connect(self.launch)
        if os.name != "nt":
            self.wine_rating = QLabel("Wine Rating: " + self.get_rating())
        self.developer_label = QLabel(self.tr("Developer: ") + self.dev)
        self.version_label = QLabel("Version: " + str(self.version))
        self.size_label = QLabel(f"{self.tr('Installed size')}: {round(self.size / (1024 ** 3), 2)} GB")
        self.settings_button = QPushButton(settings_icon, f" {self.tr('Settings')} (Icon TODO)")
        self.settings_button.setFixedWidth(200)
        self.settings_button.clicked.connect(self.settings)

        self.childLayout.addWidget(self.title_widget)
        self.childLayout.addWidget(self.launch_button)
        self.childLayout.addWidget(self.app_name_label)
        self.childLayout.addWidget(self.developer_label)
        if os.name != "nt":
            self.childLayout.addWidget(self.wine_rating)
        self.childLayout.addWidget(self.version_label)
        self.childLayout.addWidget(self.size_label)
        self.childLayout.addWidget(self.settings_button)

        self.childLayout.addStretch(1)
        self.layout.addLayout(self.childLayout)
        self.layout.addStretch(1)
        self.setLayout(self.layout)

    def launch(self):
        print("Launch")
        if not self.game_running:
            logger.info(f"launching {self.title}")
            self.proc = legendaryUtils.launch_game(self.app_name, self.core)
            if not self.proc:
                print("Fail")
                return

            self.proc.reload.connect(self.finished)
            self.launch_button.setText("Kill")
            self.game_running = True

        else:
            self.kill()

    def finished(self, exit_code):
        self.launch_button.setText("Launch")
        logger.info(f"Game {self.title} finished with exit code {exit_code}")
        self.game_running = False

    def kill(self):
        self.proc.terminate()
        self.launch_button.setText("Launch")
        self.game_running = False
        logger.info("Killing Game")

    def get_rating(self) -> str:
        return "gold"  # TODO

    def settings(self):
        settings_dialog = GameSettingsDialog(self.game, self)
        action = settings_dialog.get_settings()
        del settings_dialog
        if action == "uninstall":
            legendaryUtils.uninstall(self.app_name, self.core)
            self.signal.emit(self.app_name)
