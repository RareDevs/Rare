from logging import getLogger

from PyQt5.QtCore import pyqtSignal, QProcess
from PyQt5.QtWidgets import QWidget

from Rare.utils import LegendaryApi

logger = getLogger("Game")


class BaseInstalledWidget(QWidget):
    launch_signal = pyqtSignal(str)
    show_info = pyqtSignal(str)
    proc: QProcess()

    def __init__(self, game, core, pixmap):
        super(BaseInstalledWidget, self).__init__()
        self.game = game
        self.core = core
        self.pixmap = pixmap
        self.game_running = False

    def launch(self, offline=False, skip_version_check=False):

        logger.info("Launching " + self.game.title)
        self.proc = LegendaryApi.launch_game(self.core, self.game.app_name, offline,
                                             skip_version_check=skip_version_check)
        if not self.proc:
            logger.error("Could not start process")
            return 1
        self.proc.finished.connect(self.finished)
        self.launch_signal.emit(self.game.app_name)
        self.game_running = True
        return 0
    def finished(self):
        self.game_running = False
