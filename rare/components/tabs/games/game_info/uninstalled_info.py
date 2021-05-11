import os
import json

from PyQt5.QtCore import pyqtSignal, QSettings
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel

from custom_legendary.core import LegendaryCore
from custom_legendary.models.game import Game


class UninstalledInfo(QWidget):
    game: Game
    install_game = pyqtSignal(str)

    grade_table = json.load(open(os.path.expanduser("~/.cache/rare/game_list.json")))

    def __init__(self, core: LegendaryCore):
        super(UninstalledInfo, self).__init__()
        self.layout = QVBoxLayout()

        self.ratings = {"platinum": self.tr("Platimum"),
                        "gold": self.tr("Gold"),
                        "silver": self.tr("Silver"),
                        "bronze": self.tr("Bronze"),
                        "fail": self.tr("Could not get grade from ProtonDB"),
                        "pending": "Not enough reports"}

        self.core = core

        self.settings = QSettings()

        self.top_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        self.image = QLabel()
        left_layout.addWidget(self.image)
        left_layout.addStretch(1)
        self.top_layout.addLayout(left_layout)
        self.right_layout = QVBoxLayout()

        self.back = QPushButton(self.tr("Back"))
        self.right_layout.addWidget(self.back)

        self.title = QLabel("Error")
        self.right_layout.addWidget(self.title)

        self.app_name = QLabel("Error")
        self.right_layout.addWidget(self.app_name)

        self.rating = QLabel("Rating: Error")
        self.right_layout.addWidget(self.rating)

        self.install_button = QPushButton(self.tr("Install"))
        self.right_layout.addWidget(self.install_button)

        self.right_layout.addStretch(1)
        self.top_layout.addLayout(self.right_layout)

        self.top_layout.addStretch(1)
        self.layout.addLayout(self.top_layout)

        self.setLayout(self.layout)

    def update_game(self, app_name):
        self.game = self.core.get_game(app_name)

        self.title.setText(f"<h2>{self.game.app_title}</h2>")
        self.app_name.setText(app_name)

        IMAGE_DIR = self.settings.value("img_dir", os.path.expanduser("~/.cache/rare/images"), str)

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

        rating = self.grade_table[app_name]["grade"]
        self.rating.setText(self.ratings[rating])

