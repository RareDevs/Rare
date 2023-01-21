from typing import Optional

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget, QFrame
from legendary.models.downloading import AnalysisResult
from legendary.models.game import Game, InstalledGame
from qtawesome import icon

from rare.models.install import InstallQueueItemModel, InstallOptionsModel
from rare.shared import ImageManagerSingleton
from rare.ui.components.tabs.downloads.download_widget import Ui_DownloadWidget
from rare.ui.components.tabs.downloads.info_widget import Ui_InfoWidget
from rare.utils.misc import get_size, widget_object_name
from rare.widgets.image_widget import ImageWidget, ImageSize


class InfoWidget(QWidget):
    def __init__(
        self,
        game: Game,
        igame: InstalledGame,
        analysis: Optional[AnalysisResult] = None,
        old_igame: Optional[InstalledGame] = None,
        parent=None,
    ):
        super(InfoWidget, self).__init__(parent=parent)
        self.ui = Ui_InfoWidget()
        self.ui.setupUi(self)

        self.image_manager = ImageManagerSingleton()

        self.ui.title.setText(game.app_title)
        self.ui.remote_version.setText(old_igame.version if old_igame else game.app_version(igame.platform))
        self.ui.local_version.setText(igame.version)
        self.ui.dl_size.setText(get_size(analysis.dl_size) if analysis else "")
        self.ui.install_size.setText(get_size(analysis.install_size) if analysis else "")

        self.image = ImageWidget(self)
        self.image.setFixedSize(ImageSize.Icon)
        self.image.setPixmap(self.image_manager.get_pixmap(game.app_name, color=True))
        self.ui.image_layout.addWidget(self.image)

        self.ui.info_widget_layout.setAlignment(Qt.AlignTop)


class UpdateWidget(QFrame):
    enqueue = pyqtSignal(InstallOptionsModel)

    def __init__(self, game: Game, igame: InstalledGame, parent=None):
        super(UpdateWidget, self).__init__(parent=parent)
        self.ui = Ui_DownloadWidget()
        self.ui.setupUi(self)
        # lk: setObjectName has to be after `setupUi` because it is also set in that function
        self.setObjectName(widget_object_name(self, game.app_name))

        self.game = game
        self.igame = igame

        self.ui.queue_buttons.setVisible(False)
        self.ui.move_buttons.setVisible(False)

        self.info_widget = InfoWidget(game, igame, parent=self)
        self.ui.info_layout.addWidget(self.info_widget)

        self.ui.update_button.clicked.connect(lambda: self.update_game(True))
        self.ui.settings_button.clicked.connect(lambda: self.update_game(False))

    def update_game(self, auto: bool):
        self.ui.update_button.setDisabled(True)
        self.ui.settings_button.setDisabled(True)
        self.enqueue.emit(InstallOptionsModel(app_name=self.game.app_name, update=True, silent=auto))  # True if settings

    def set_enabled(self, enabled: bool):
        self.ui.update_button.setEnabled(enabled)
        self.ui.settings_button.setEnabled(enabled)

    def version(self) -> str:
        return self.game.app_version(self.igame.platform)


class QueueWidget(QFrame):
    # str: app_name
    move_up = pyqtSignal(str)
    # str: app_name
    move_down = pyqtSignal(str)
    # str: app_name
    remove = pyqtSignal(str)
    # InstallQueueItemModel
    force = pyqtSignal(InstallQueueItemModel)


    def __init__(self, item: InstallQueueItemModel, old_igame: InstalledGame, parent=None):
        super(QueueWidget, self).__init__(parent=parent)
        self.ui = Ui_DownloadWidget()
        self.ui.setupUi(self)
        # lk: setObjectName has to be after `setupUi` because it is also set in that function
        self.setObjectName(widget_object_name(self, item.options.app_name))

        self.item = item

        self.ui.update_buttons.setVisible(False)

        self.ui.move_up_button.setIcon(icon("fa.arrow-up"))
        self.ui.move_up_button.clicked.connect(
            lambda: self.move_up.emit(self.item.download.game.app_name)
        )

        self.ui.move_down_button.setIcon(icon("fa.arrow-down"))
        self.ui.move_down_button.clicked.connect(
            lambda: self.move_down.emit(self.item.download.game.app_name)
        )

        self.info_widget = InfoWidget(
            item.download.game, item.download.igame, item.download.analysis, old_igame, parent=self
        )
        self.ui.info_layout.addWidget(self.info_widget)

        self.ui.remove_button.clicked.connect(lambda: self.remove.emit(self.item.download.game.app_name))
        self.ui.force_button.clicked.connect(lambda: self.force.emit(self.item))

    def toggle_arrows(self, index: int, length: int):
        self.ui.move_up_button.setEnabled(bool(index))
        self.ui.move_down_button.setEnabled(bool(length - (index + 1)))
