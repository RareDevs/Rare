from logging import getLogger

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QGroupBox, QLabel, QAction
from legendary.models.game import Game

from rare.shared.image_manager import ImageManagerSingleton, ImageSize

logger = getLogger("Uninstalled")


class BaseUninstalledWidget(QGroupBox):
    show_uninstalled_info = pyqtSignal(Game)

    def __init__(self, game, core, pixmap):
        super(BaseUninstalledWidget, self).__init__()
        self.image_manager = ImageManagerSingleton()

        self.game = game
        if self.game.app_title == "Unreal Engine":
            self.game.app_title = f"{self.game.app_title} {self.game.app_name.split('_')[-1]}"

        self.core = core
        self.image = QLabel()
        self.image.setFixedSize(ImageSize.Display.size)
        self.image.setPixmap(pixmap.scaled(ImageSize.Display.size, transformMode=Qt.SmoothTransformation))
        self.installing = False
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.setContentsMargins(0, 0, 0, 0)

        reload_image = QAction(self.tr("Reload Image"), self)
        reload_image.triggered.connect(self.reload_image)
        self.addAction(reload_image)

    def reload_image(self):
        self.image_manager.download_image_blocking(self.game, force=True)
        pm = self.image_manager.get_pixmap(self.game.app_name, color=False)
        self.image.setPixmap(pm.scaled(ImageSize.Display.size, transformMode=Qt.SmoothTransformation))

    def install(self):
        self.show_uninstalled_info.emit(self.game)
