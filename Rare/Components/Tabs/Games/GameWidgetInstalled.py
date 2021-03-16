import os
from logging import getLogger

from PyQt5.QtCore import QEvent, pyqtSignal, QSettings, QSize, Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import *
from custom_legendary.core import LegendaryCore
from custom_legendary.models.game import InstalledGame
from qtawesome import icon

from Rare.utils import LegendaryApi
from Rare.utils.QtExtensions import ClickableLabel

logger = getLogger("GameWidgetInstalled")


class GameWidgetInstalled(QWidget):
    update_list = pyqtSignal()
    show_info = pyqtSignal(str)
    update_game = pyqtSignal()

    def __init__(self, core: LegendaryCore, game: InstalledGame):
        super(GameWidgetInstalled, self).__init__()
        self.setObjectName("game_widget_parent")

        self.layout = QVBoxLayout()
        self.core = core
        self.game = game
        self.running = False
        settings = QSettings()
        self.info_text = ""
        self.IMAGE_DIR = settings.value("img_dir", os.path.expanduser("~/.cache/rare"))

        self.update_available = self.core.get_asset(self.game.app_name, True).build_version != game.version
        if self.update_available:
            logger.info("Update available for game: " + self.game.app_name)
            self.info_text = self.tr("Update available")

        if os.path.exists(f"{self.IMAGE_DIR}/{game.app_name}/FinalArt.png"):
            pixmap = QPixmap(f"{self.IMAGE_DIR}/{game.app_name}/FinalArt.png")
        elif os.path.exists(f"{self.IMAGE_DIR}/{game.app_name}/DieselGameBoxTall.png"):
            pixmap = QPixmap(f"{self.IMAGE_DIR}/{game.app_name}/DieselGameBoxTall.png")
        elif os.path.exists(f"{self.IMAGE_DIR}/{game.app_name}/DieselGameBoxLogo.png"):
            pixmap = QPixmap(f"{self.IMAGE_DIR}/{game.app_name}/DieselGameBoxLogo.png")
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
        self.title_label.setAutoFillBackground(False)
        self.title_label.setWordWrap(True)
        self.title_label.setFixedWidth(175)
        minilayout = QHBoxLayout()
        self.title_label.setObjectName("game_widget")
        minilayout.addWidget(self.title_label)

        # Info Button
        self.menu_btn = QPushButton()
        self.menu_btn.setIcon(icon("ei.info-circle", color="white"))
        # self.menu_btn.setObjectName("installed_menu_button")
        self.menu_btn.setIconSize(QSize(18, 18))
        self.menu_btn.enterEvent = lambda x: self.info_label.setText("Information")
        self.menu_btn.leaveEvent = lambda x: self.info_label.setText(
            "Please update Game") if self.update_available else self.info_label.setText("Start Game")
        # remove Border

        self.menu_btn.setObjectName("menu_button")

        self.menu_btn.clicked.connect(lambda: self.show_info.emit(self.game.app_name))
        self.menu_btn.setFixedWidth(17)
        minilayout.addWidget(self.menu_btn)
        minilayout.addStretch(1)
        self.layout.addLayout(minilayout)

        self.info_label = QLabel(self.info_text)
        self.info_label.setAutoFillBackground(False)
        self.info_label.setObjectName("info_label")
        self.layout.addWidget(self.info_label)

        #p = self.palette()
        #p.setColor(self.backgroundRole(), Qt.red)
        #self.setPalette(p)

        self.setLayout(self.layout)
        self.setFixedWidth(self.sizeHint().width())

    def enterEvent(self, a0: QEvent) -> None:
        if self.update_available:
            self.info_label.setText(self.tr("Please update Game"))
        elif not self.running:
            self.info_label.setText("Start Game")
        else:
            self.info_label.setText(self.tr("Game running"))

    def leaveEvent(self, a0: QEvent) -> None:
        if self.running:
            self.info_label.setText(self.tr("Game running"))
        else:
            self.info_label.setText(self.info_text)

    def mousePressEvent(self, a0) -> None:
        self.launch()

    def launch(self, offline=False):
        if not self.running and not self.update_available:
            logger.info("Launching " + self.game.title)
            self.proc = LegendaryApi.launch_game(self.core, self.game.app_name, offline)
            if not self.proc:
                logger.error("Could not start process")
                return
            self.proc.finished.connect(self.finished)
            self.info_label.setText(self.tr("Game running"))
            self.running = True
        if self.update_available:
            self.update_game.emit()

    def finished(self):
        self.info_label.setText("")
        self.running = False
