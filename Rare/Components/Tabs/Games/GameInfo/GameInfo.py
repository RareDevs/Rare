import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLabel, QHBoxLayout, QTabWidget
from legendary.core import LegendaryCore
from legendary.models.game import InstalledGame, Game

from Rare.utils.QtExtensions import SideTabBar
from Rare.utils.utils import IMAGE_DIR


class InfoTabs(QTabWidget):
    def __init__(self, core):
        super(InfoTabs, self).__init__()

        self.setTabBar(SideTabBar())
        self.setTabPosition(QTabWidget.West)

        self.info = GameInfo(core)
        self.addTab(self.info, "Game Info")
        self.addTab(QLabel("Coming soon"), "Settings")


class GameInfo(QWidget):
    igame: InstalledGame
    game: Game

    def __init__(self, core: LegendaryCore):
        super(GameInfo, self).__init__()
        self.core = core
        self.layout = QVBoxLayout()
        self.back_button = QPushButton("Back")
        self.layout.addWidget(self.back_button)

        # TODO More Information: Image text settings needs_verification platform
        top_layout = QHBoxLayout()

        self.image = QLabel()
        top_layout.addWidget(self.image)

        right_layout = QVBoxLayout()
        self.game_title = QLabel("Error")
        self.game_title.setTextInteractionFlags(Qt.TextSelectableByMouse)
        right_layout.addWidget(self.game_title)

        self.dev = QLabel("Error")
        right_layout.addWidget(self.dev)

        self.app_name = QLabel("Error")
        self.app_name.setTextInteractionFlags(Qt.TextSelectableByMouse)
        right_layout.addWidget(self.app_name)

        self.version = QLabel("Error")
        right_layout.addWidget(self.version)

        self.install_size = QLabel("Error")
        right_layout.addWidget(self.install_size)

        self.install_path = QLabel("Error")
        right_layout.addWidget(self.install_path)

        top_layout.addLayout(right_layout)
        top_layout.addStretch()

        self.layout.addLayout(top_layout)
        self.layout.addStretch()
        self.setLayout(self.layout)

    def update_game(self, app_name):
        self.game = self.core.get_game(app_name)
        self.igame = self.core.get_installed_game(app_name)

        self.game_title.setText(f"<h2>{self.game.app_title}</h2>")

        if os.path.exists(f"{IMAGE_DIR}/{self.game.app_name}/FinalArt.png"):
            pixmap = QPixmap(f"{IMAGE_DIR}/{self.game.app_name}/FinalArt.png")
        elif os.path.exists(f"{IMAGE_DIR}/{self.game.app_name}/DieselGameBoxTall.png"):
            pixmap = QPixmap(f"{IMAGE_DIR}/{self.game.app_name}/DieselGameBoxTall.png")
        elif os.path.exists(f"{IMAGE_DIR}/{self.game.app_name}/DieselGameBoxLogo.png"):
            pixmap = QPixmap(f"{IMAGE_DIR}/{self.game.app_name}/DieselGameBoxLogo.png")
        else:
            # logger.warning(f"No Image found: {self.game.title}")
            pixmap = None
        if pixmap:
            w = 200
            pixmap = pixmap.scaled(w, int(w * 4 / 3))
            self.image.setPixmap(pixmap)
        self.app_name.setText("App name: "+ self.game.app_name)
        self.version.setText("Version: " + self.game.app_version)
        self.dev.setText(self.tr("Developer: ") + self.game.metadata["developer"])
        self.install_size.setText(self.tr("Install size: ") + str(round(self.igame.install_size/(1024**3), 2))+ " GB")
        self.install_path.setText(self.tr("Install path: ") + self.igame.install_path)
        print(self.game.__dict__)
        print(self.igame.__dict__)