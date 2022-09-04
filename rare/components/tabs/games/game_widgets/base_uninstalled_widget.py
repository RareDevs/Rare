from logging import getLogger

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QFrame, QAction
from legendary.models.game import Game

from rare.shared import ImageManagerSingleton
from rare.shared.image_manager import ImageSize
from rare.widgets.image_widget import ImageWidget

logger = getLogger("Uninstalled")


class BaseUninstalledWidget(QFrame):
    show_uninstalled_info = pyqtSignal(Game)

    def __init__(self, game, core, pixmap):
        super(BaseUninstalledWidget, self).__init__()
        self.image_manager = ImageManagerSingleton()

        self.game = game
        if self.game.app_title == "Unreal Engine":
            self.game.app_title = f"{self.game.app_title} {self.game.app_name.split('_')[-1]}"

        self.core = core
        self.image = ImageWidget(self)
        self.image.setFixedSize(ImageSize.Display)
        self.image.setPixmap(pixmap)
        self.installing = False
        self.setContextMenuPolicy(Qt.ActionsContextMenu)

        reload_image = QAction(self.tr("Reload Image"), self)
        reload_image.triggered.connect(self.reload_image)
        self.addAction(reload_image)

    def reload_image(self):
        self.image_manager.download_image_blocking(self.game, force=True)
        pm = self.image_manager.get_pixmap(self.game.app_name, color=False)
        self.image.setPixmap(pm)

    def install(self):
        self.show_uninstalled_info.emit(self.game)

    # From RareGame, added from sorting to work
    @property
    def is_non_asset(self) -> bool:
        """!
        @brief Property to report if a Game doesn't have assets

        Typically, games have assets, however some games that require
        other launchers do not have them. Rare treats these games as installed
        offering to execute their launcher.

        @return bool If the game doesn't have assets
        """
        return not self.game.asset_infos

    @property
    def is_installed(self) -> bool:
        """!
        @brief Property to report if a game is installed

        This returns True if InstalledGame data have been loaded for the game
        or if the game is a game without assets, for example an Origin game.

        @return bool If the game should be considered installed
        """
        return False or self.is_non_asset

    @property
    def app_title(self) -> str:
        return self.game.app_title
