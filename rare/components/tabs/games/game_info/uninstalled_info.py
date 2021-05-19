import json
import os

from PyQt5.QtCore import pyqtSignal, QSettings, Qt
from PyQt5.QtGui import QPixmap, QKeyEvent
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTabWidget, QTreeView
from qtawesome import icon

from custom_legendary.core import LegendaryCore
from custom_legendary.models.game import Game
from rare.utils.extra_widgets import SideTabBar
from rare.utils.json_formatter import QJsonModel


class UninstalledTabInfo(QTabWidget):
    def __init__(self, core, parent):
        super(UninstalledTabInfo, self).__init__(parent=parent)
        self.app_name = ""
        self.core = core
        self.setTabBar(SideTabBar())

        self.setTabPosition(QTabWidget.West)

        self.addTab(QWidget(), icon("mdi.keyboard-backspace", color="white"), self.tr("Back"))
        self.tabBarClicked.connect(lambda x: self.parent().layout.setCurrentIndex(0) if x == 0 else None)

        self.info = UninstalledInfo(core, self)
        self.addTab(self.info, self.tr("Game Info"))

        self.view = QTreeView()
        self.view.setColumnWidth(0, 300)
        self.view.setWordWrap(True)

        self.model = QJsonModel()
        self.view.setModel(self.model)

        self.addTab(self.view, self.tr("Metadata"))

        # self.setTabEnabled(1, False)
        self.setCurrentIndex(1)

    def update_game(self, app_name):
        self.info.update_game(app_name)
        self.model.clear()
        self.model.load(json.load(open(os.path.expanduser(f"~/.config/legendary/metadata/{app_name}.json"), "r")))

    def keyPressEvent(self, e: QKeyEvent):
        if e.key() == Qt.Key_Escape:
            self.parent().layout.setCurrentIndex(0)


class UninstalledInfo(QWidget):
    game: Game
    install_game = pyqtSignal(str)

    def __init__(self, core: LegendaryCore, parent):
        super(UninstalledInfo, self).__init__(parent=parent)
        self.layout = QVBoxLayout()
        self.grade_table = json.load(open(os.path.expanduser("~/.cache/rare/game_list.json")))

        self.ratings = {"platinum": self.tr("Platinum"),
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

        self.title = QLabel("Error")
        self.right_layout.addWidget(self.title)

        self.app_name = QLabel("Error")
        self.right_layout.addWidget(self.app_name)

        self.rating = QLabel("Rating: Error")
        self.right_layout.addWidget(self.rating)

        self.install_button = QPushButton(self.tr("Install"))
        self.install_button.setFixedWidth(300)
        self.install_button.setStyleSheet("""background-color: #090""")
        self.install_button.clicked.connect(lambda: self.install_game.emit(self.game.app_name))
        self.right_layout.addWidget(self.install_button)
        self.version = QLabel("Error")
        self.right_layout.addWidget(self.version)

        self.right_layout.addStretch(1)
        self.top_layout.addLayout(self.right_layout)

        self.top_layout.addStretch(1)
        self.layout.addLayout(self.top_layout)

        self.setLayout(self.layout)

    def update_game(self, app_name):
        self.game = self.core.get_game(app_name)

        self.title.setText(f"<h2>{self.game.app_title}</h2>")
        self.app_name.setText("Appname: " + app_name)

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

        self.version.setText(self.game.asset_info.build_version)

        rating = self.grade_table[app_name]["grade"]
        if rating not in ["fail", "pending"]:
            self.rating.setText(self.tr("Rating from ProtonDB: ") + self.ratings[rating])
        else:
            self.rating.setText(self.ratings[rating])
