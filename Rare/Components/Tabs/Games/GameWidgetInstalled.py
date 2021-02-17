import os
from logging import getLogger

from PyQt5.QtCore import QEvent, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import *
from legendary.core import LegendaryCore
from legendary.models.game import InstalledGame

from Rare import style_path
from Rare.utils import LegendaryApi
from Rare.utils.QtExtensions import ClickableLabel
from Rare.utils.RareConfig import IMAGE_DIR

logger = getLogger("GameWidgetInstalled")


class GameWidgetInstalled(QWidget):
    update_list = pyqtSignal()

    def __init__(self, core: LegendaryCore, game: InstalledGame):
        super(GameWidgetInstalled, self).__init__()
        self.setObjectName("game_widget_parent")
        self.layout = QVBoxLayout()
        self.core = core
        self.game = game
        self.running = False

        self.update_available = self.core.get_asset(self.game.app_name, True).build_version != game.version
        if self.update_available:
            logger.info("Update available for game: " + self.game.app_name)

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
            w = 200
            pixmap = pixmap.scaled(w, int(w * 4 / 3))
            self.image = ClickableLabel()
            self.image.setObjectName("game_widget")
            self.image.setPixmap(pixmap)
            self.layout.addWidget(self.image)

        self.title_label = QLabel(f"<h4>{game.title}</h4>")
        self.title_label.setWordWrap(True)
        self.title_label.setFixedWidth(180)
        minilayout = QHBoxLayout()
        self.title_label.setObjectName("game_widget")
        minilayout.addWidget(self.title_label)
        # minilayout.addStretch(1)
        self.menu_btn = QPushButton(QIcon(style_path + "/Icons/menu.png"), "")
        self.menu = Menu()
        self.menu.action.connect(self.menu_action)
        self.menu_btn.setMenu(self.menu)
        self.menu_btn.setObjectName("menu")
        self.menu_btn.setFixedWidth(10)
        minilayout.addWidget(self.menu_btn)
        minilayout.addStretch(1)
        self.layout.addLayout(minilayout)

        self.info_label = QLabel("")
        self.info_label.setObjectName("info_label")
        self.layout.addWidget(self.info_label)

        self.setLayout(self.layout)
        self.setFixedWidth(self.sizeHint().width())

    def enterEvent(self, a0: QEvent) -> None:
        if not self.running:
            self.info_label.setText("Start Game")

    def leaveEvent(self, a0: QEvent) -> None:
        self.info_label.setText("")

    def mousePressEvent(self, a0) -> None:
        self.launch()

    def launch(self, offline=False):
        if not self.running:
            logger.info("Launching " + self.game.title)
            self.proc = LegendaryApi.launch_game(self.core, self.game.app_name, offline)
            if not self.proc:
                logger.error("Could not start process")
                return
            self.proc.finished.connect(self.finished)
            self.info_label.setText("Game running")
            self.running = True

    def finished(self):
        self.info_label.setText("")
        self.running = False

    def menu_action(self, action: str):
        if action == "uninstall":
            if QMessageBox.question(self, "Uninstall", f"Do you want to uninstall {self.game.title}",
                                    QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                logger.info("Uninstalling " + self.game.title)
                self.core.uninstall_game(self.game)
                self.update_list.emit()


class Menu(QMenu):
    action = pyqtSignal(str)

    def __init__(self):
        super(Menu, self).__init__()
        self.addAction("Game info", lambda: self.action.emit("info"))
        self.addAction("Uninstall", lambda: self.action.emit("uninstall"))

    def info(self):
        pass

    def uninstall(self):
        pass
