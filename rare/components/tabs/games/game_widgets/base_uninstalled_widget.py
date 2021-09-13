from logging import getLogger

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QGroupBox, QLabel, QAction
from legendary.models.game import Game

from rare.utils import utils

logger = getLogger("Uninstalled")


class BaseUninstalledWidget(QGroupBox):
    show_uninstalled_info = pyqtSignal(Game)

    def __init__(self, game, core, pixmap):
        super(BaseUninstalledWidget, self).__init__()
        self.game = game
        self.core = core
        self.image = QLabel()
        self.image.setPixmap(pixmap.scaled(200, int(200 * 4 / 3), transformMode=Qt.SmoothTransformation))
        self.installing = False
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.setContentsMargins(0, 0, 0, 0)

        reload_image = QAction(self.tr("Reload Image"), self)
        reload_image.triggered.connect(self.reload_image)
        self.addAction(reload_image)

    def reload_image(self):
        utils.download_image(self.game, True)
        pm = utils.get_uninstalled_pixmap(self.game.app_name)
        self.image.setPixmap(pm.scaled(200, int(200 * 4 / 3), transformMode=Qt.SmoothTransformation))

    def install(self):
        self.show_uninstalled_info.emit(self.game)
