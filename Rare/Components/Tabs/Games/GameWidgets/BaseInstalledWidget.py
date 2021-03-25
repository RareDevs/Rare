from logging import getLogger

from PyQt5.QtCore import pyqtSignal, QProcess
from PyQt5.QtWidgets import QWidget
from custom_legendary.models.game import InstalledGame

from custom_legendary.core import LegendaryCore

from Rare.utils import LegendaryApi

logger = getLogger("Game")


class BaseInstalledWidget(QWidget):
    launch_signal = pyqtSignal(str)
    show_info = pyqtSignal(str)
    proc: QProcess()

    def __init__(self, igame: InstalledGame, core: LegendaryCore, pixmap):
        super(BaseInstalledWidget, self).__init__()
        self.igame = igame
        self.core = core
        self.game = self.core.get_game(self.igame.app_name)
        self.pixmap = pixmap
        self.game_running = False
        self.update_available = self.update_available = self.core.get_asset(self.game.app_name, True).build_version != igame.version

    def launch(self, offline=False, skip_version_check=False):

        logger.info("Launching " + self.igame.title)
        self.proc = LegendaryApi.launch_game(self.core, self.igame.app_name, offline,
                                             skip_version_check=skip_version_check)
        if not self.proc:
            logger.error("Could not start process")
            return 1
        self.proc.finished.connect(self.finished)
        self.launch_signal.emit(self.igame.app_name)
        self.game_running = True
        return 0
    def finished(self):
        self.game_running = False
