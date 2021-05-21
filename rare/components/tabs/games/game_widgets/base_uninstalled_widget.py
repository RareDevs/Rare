from logging import getLogger

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QGroupBox

logger = getLogger("Uninstalled")


class BaseUninstalledWidget(QGroupBox):
    show_uninstalled_info = pyqtSignal(str)

    def __init__(self, game, core, pixmap):
        super(BaseUninstalledWidget, self).__init__()
        self.game = game
        self.core = core
        self.pixmap = pixmap
        self.installing = False

        self.setContentsMargins(0, 0, 0, 0)

    def install(self):
        self.show_uninstalled_info.emit(self.game.app_name)
