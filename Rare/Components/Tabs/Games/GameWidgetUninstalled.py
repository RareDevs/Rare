import os
from logging import getLogger

from PyQt5.QtCore import pyqtSignal, QSettings
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from custom_legendary.core import LegendaryCore
from custom_legendary.models.game import Game

from Rare.Components.Dialogs.InstallDialog import InstallDialog
from Rare.utils.Models import InstallOptions
from Rare.utils.QtExtensions import ClickableLabel
from Rare.utils.utils import download_image

logger = getLogger("Uninstalled")


class GameWidgetUninstalled(QWidget):
    install_game = pyqtSignal(InstallOptions)

    def __init__(self, core: LegendaryCore, game: Game):
        super(GameWidgetUninstalled, self).__init__()
        self.layout = QVBoxLayout()
        self.core = core
        self.game = game
        s = QSettings()
        IMAGE_DIR = s.value("img_dir", os.path.expanduser("~/.cache/rare"), type=str)
        if os.path.exists(f"{IMAGE_DIR}/{game.app_name}/UninstalledArt.png"):
            pixmap = QPixmap(f"{IMAGE_DIR}/{game.app_name}/UninstalledArt.png")

            if pixmap.isNull():
                logger.info(game.app_title + " has a corrupt image.")
                download_image(game, force=True)
                pixmap = QPixmap(f"{IMAGE_DIR}/{game.app_name}/UninstalledArt.png")

        else:
            logger.warning(f"No Image found: {self.game.app_title}")
            pixmap = None

        if pixmap:
            w = 200
            pixmap = pixmap.scaled(w, int(w * 4 / 3))
            self.image = ClickableLabel()
            self.image.setPixmap(pixmap)
            self.layout.addWidget(self.image)

        self.title_label = QLabel(f"<h3>{game.app_title}</h3>")
        self.title_label.setWordWrap(True)
        self.layout.addWidget(self.title_label)

        self.info_label = QLabel("")
        self.layout.addWidget(self.info_label)

        self.setLayout(self.layout)
        self.setFixedWidth(self.sizeHint().width())

    def mousePressEvent(self, a0) -> None:
        self.install()

    def enterEvent(self, QEvent):
        self.info_label.setText(self.tr("Install Game"))

    def leaveEvent(self, QEvent):
        self.info_label.setText("")

    def install(self):
        logger.info("Install " + self.game.app_title)

        infos = InstallDialog().get_information()
        if infos != 0:
            path, max_workers = infos
            self.install_game.emit(InstallOptions(app_name=self.game.app_name, max_workers=max_workers, path=path))
        # wait for update of legendary to get progress
