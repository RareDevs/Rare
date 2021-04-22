from logging import getLogger

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QGroupBox

from rare.components.dialogs.install_dialog import InstallDialog
from rare.utils.models import InstallOptions

logger = getLogger("Uninstalled")


class BaseUninstalledWidget(QGroupBox):
    install_game = pyqtSignal(InstallOptions)

    def __init__(self, game, core, pixmap):
        super(BaseUninstalledWidget, self).__init__()
        self.game = game
        self.core = core
        self.pixmap = pixmap
        self.installing = False

        self.setContentsMargins(0, 0, 0, 0)

    def install(self):
        infos = InstallDialog(self.game.app_name, self.core).get_information()
        if infos != 0:
            path, max_workers, force, ignore_free_space = infos
            self.install_game.emit(
                InstallOptions(app_name=self.game.app_name, max_workers=max_workers, path=path, force=force,
                               ignore_free_space=ignore_free_space))
