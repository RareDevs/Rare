from logging import getLogger
from typing import Optional

from PyQt5.QtCore import pyqtSignal, Qt, QThreadPool, pyqtSlot
from PyQt5.QtWidgets import QWidget, QFrame
from legendary.models.downloading import AnalysisResult
from legendary.models.game import Game, InstalledGame
from qtawesome import icon

from rare.models.install import InstallQueueItemModel, InstallOptionsModel, InstallDownloadModel
from rare.shared import RareCore, ImageManagerSingleton
from rare.shared.workers.install_info import InstallInfoWorker
from rare.ui.components.tabs.downloads.queue_base_widget import Ui_QueueBaseWidget
from rare.ui.components.tabs.downloads.queue_info_widget import Ui_QueueInfoWidget
from rare.utils.misc import format_size, widget_object_name, elide_text
from rare.widgets.image_widget import ImageWidget, ImageSize

logger = getLogger("DownloadWidgets")


class QueueInfoWidget(QWidget):
    def __init__(
        self,
        game: Optional[Game],
        igame: Optional[InstalledGame],
        analysis: Optional[AnalysisResult] = None,
        old_igame: Optional[InstalledGame] = None,
        parent=None,
    ):
        super(QueueInfoWidget, self).__init__(parent=parent)
        self.ui = Ui_QueueInfoWidget()
        self.ui.setupUi(self)

        self.image_manager = ImageManagerSingleton()

        self.image = ImageWidget(self)
        self.image.setFixedSize(ImageSize.Icon)
        self.ui.image_layout.addWidget(self.image)

        self.ui.queue_info_layout.setAlignment(Qt.AlignTop)

        if game and igame:
            self.update_information(game, igame, analysis, old_igame)
        else:
            self.ui.title.setText("...")
            self.ui.remote_version.setText("...")
            self.ui.local_version.setText("...")
            self.ui.dl_size.setText("...")
            self.ui.install_size.setText("...")

        if old_igame:
            self.ui.title.setText(old_igame.title)
            self.image.setPixmap(self.image_manager.get_pixmap(old_igame.app_name, color=True))

    def update_information(self, game, igame, analysis, old_igame):
        self.ui.title.setText(game.app_title)
        self.ui.remote_version.setText(
            elide_text(self.ui.remote_version, old_igame.version if old_igame else game.app_version(igame.platform))
        )
        self.ui.local_version.setText(elide_text(self.ui.local_version, igame.version))
        self.ui.dl_size.setText(format_size(analysis.dl_size) if analysis else "")
        self.ui.install_size.setText(format_size(analysis.install_size) if analysis else "")
        self.image.setPixmap(self.image_manager.get_pixmap(game.app_name, color=True))


class UpdateWidget(QFrame):
    enqueue = pyqtSignal(InstallOptionsModel)

    def __init__(self, game: Game, igame: InstalledGame, parent=None):
        super(UpdateWidget, self).__init__(parent=parent)
        self.ui = Ui_QueueBaseWidget()
        self.ui.setupUi(self)
        # lk: setObjectName has to be after `setupUi` because it is also set in that function
        self.setObjectName(widget_object_name(self, game.app_name))

        self.game = game
        self.igame = igame

        self.ui.queue_buttons.setVisible(False)
        self.ui.move_buttons.setVisible(False)

        self.info_widget = QueueInfoWidget(game, igame, parent=self)
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
        self.ui = Ui_QueueBaseWidget()
        self.ui.setupUi(self)
        # lk: setObjectName has to be after `setupUi` because it is also set in that function
        self.setObjectName(widget_object_name(self, item.options.app_name))

        if not item:
            self.ui.queue_buttons.setEnabled(False)
            worker = InstallInfoWorker(RareCore.instance().core(), item.options)
            worker.signals.result.connect(self.__update_info)
            worker.signals.failed.connect(
                lambda m: logger.error(f"Failed to requeue download for {item.options.app_name} with error: {m}")
            )
            worker.signals.failed.connect(lambda m: self.remove.emit(item.options.app_name))
            worker.signals.finished.connect(
                lambda: logger.info(f"Download requeue worker finished for {item.options.app_name}")
            )
            QThreadPool.globalInstance().start(worker)
            self.info_widget = QueueInfoWidget(None, None, None, old_igame, parent=self)
        else:
            self.info_widget = QueueInfoWidget(
                item.download.game, item.download.igame, item.download.analysis, old_igame, parent=self
            )
        self.ui.info_layout.addWidget(self.info_widget)
        self.ui.update_buttons.setVisible(False)

        self.old_igame = old_igame
        self.item = item

        self.ui.move_up_button.setIcon(icon("fa.arrow-up"))
        self.ui.move_up_button.clicked.connect(
            lambda: self.move_up.emit(self.item.options.app_name)
        )

        self.ui.move_down_button.setIcon(icon("fa.arrow-down"))
        self.ui.move_down_button.clicked.connect(
            lambda: self.move_down.emit(self.item.options.app_name)
        )

        self.ui.remove_button.clicked.connect(lambda: self.remove.emit(self.item.options.app_name))
        self.ui.force_button.clicked.connect(lambda: self.force.emit(self.item))

    @pyqtSlot(InstallDownloadModel)
    def __update_info(self, download: InstallDownloadModel):
        self.item.download = download
        if self.item:
            self.info_widget.update_information(download.game, download.igame, download.analysis, self.old_igame)
        self.ui.queue_buttons.setEnabled(bool(self.item))

    def toggle_arrows(self, index: int, length: int):
        self.ui.move_up_button.setEnabled(bool(index))
        self.ui.move_down_button.setEnabled(bool(length - (index + 1)))
