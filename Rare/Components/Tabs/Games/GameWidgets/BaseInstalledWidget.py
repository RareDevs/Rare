from logging import getLogger

from PyQt5.QtCore import pyqtSignal, QProcess
from PyQt5.QtWidgets import QGroupBox

from Rare.utils import LegendaryApi
from custom_legendary.core import LegendaryCore
from custom_legendary.models.game import InstalledGame

logger = getLogger("Game")


class BaseInstalledWidget(QGroupBox):
    launch_signal = pyqtSignal(str)
    show_info = pyqtSignal(str)
    finish_signal = pyqtSignal(str)
    proc: QProcess()

    def __init__(self, igame: InstalledGame, core: LegendaryCore, pixmap):
        super(BaseInstalledWidget, self).__init__()
        self.igame = igame
        self.core = core
        self.game = self.core.get_game(self.igame.app_name)
        self.pixmap = pixmap
        self.game_running = False
        self.update_available = self.core.get_asset(self.game.app_name, True).build_version != igame.version

        self.setContentsMargins(0, 0, 0, 0)

        # self.setStyleSheet("border-radius: 5px")

    def launch(self, offline=False, skip_version_check=False):
        logger.info("Launching " + self.igame.title)
        self.proc, params = LegendaryApi.launch_game(self.core, self.igame.app_name, offline,
                                                     skip_version_check=skip_version_check)
        if not self.proc:
            logger.error("Could not start process")
            return 1
        self.proc.finished.connect(self.finished)
        self.proc.start(params[0], params[1:])
        self.launch_signal.emit(self.igame.app_name)
        self.game_running = True
        return 0

    def finished(self, exit_code):
        logger.info("Game exited with exit code: ", exit_code)
        self.finish_signal.emit(self.game.app_name)
        self.game_running = False
