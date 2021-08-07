import json
import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QKeyEvent
from PyQt5.QtWidgets import QWidget, QTabWidget, QTreeView
from qtawesome import icon

from custom_legendary.core import LegendaryCore
from custom_legendary.models.game import Game
from rare import data_dir
from rare.ui.components.tabs.games.game_info.game_info import Ui_GameInfo
from rare.utils.extra_widgets import SideTabBar
from rare.utils.json_formatter import QJsonModel
from rare.utils.utils import IMAGE_DIR


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


class UninstalledInfo(QWidget, Ui_GameInfo):
    game: Game
    install_game = pyqtSignal(str)

    def __init__(self, core: LegendaryCore, parent=None):
        super(UninstalledInfo, self).__init__(parent=parent)
        self.setupUi(self)
        self.core = core

        self.ratings = {"platinum": self.tr("Platinum"),
                        "gold": self.tr("Gold"),
                        "silver": self.tr("Silver"),
                        "bronze": self.tr("Bronze"),
                        "fail": self.tr("Could not get grade"),
                        "pending": self.tr("Not enough reports")}
        if os.path.exists(p := os.path.join(data_dir, "game_list.json")):
            self.grade_table = json.load(open(p))
        else:
            self.grade_table = {}

        if os.name == "nt":
            self.lbl_grade.setVisible(False)
            self.grade.setVisible(False)

        self.install_size.setEnabled(False)
        self.lbl_install_size.setEnabled(False)
        self.install_path.setEnabled(False)
        self.lbl_install_path.setEnabled(False)

        self.game_actions_stack.setCurrentIndex(1)
        self.game_actions_stack.resize(self.game_actions_stack.minimumSize())

        self.install_button.clicked.connect(lambda: self.install_game.emit(self.game.app_name))

    def update_game(self, app_name):
        self.game = self.core.get_game(app_name)

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

        self.app_name.setText(self.game.app_name)
        self.version.setText(self.game.app_version)
        self.dev.setText(self.game.metadata["developer"])
        self.install_size.setText("N/A")
        self.install_path.setText("N/A")

        if os.name != "nt" and self.grade_table:
            try:
                grade = self.grade_table[app_name]["grade"]
            except KeyError:
                grade = "fail"
            self.grade.setText(self.ratings[grade])
