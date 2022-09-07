import datetime
from logging import getLogger
from typing import List, Dict, Union, Set

from PyQt5.QtCore import QThread, pyqtSignal, QSettings, pyqtSlot
from PyQt5.QtWidgets import (
    QWidget,
    QMessageBox,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
)
from legendary.core import LegendaryCore
from legendary.models.game import Game, InstalledGame

from rare.components.dialogs.install_dialog import InstallDialog
from rare.components.tabs.downloads.dl_queue_widget import DlQueueWidget, DlWidget
from rare.components.tabs.downloads.download_thread import DownloadThread
from rare.lgndr.downloading import UIUpdate
from rare.models.install import InstallOptionsModel, InstallQueueItemModel
from rare.shared import LegendaryCoreSingleton, GlobalSignalsSingleton
from rare.ui.components.tabs.downloads.downloads_tab import Ui_DownloadsTab
from rare.utils.misc import get_size, create_desktop_link

logger = getLogger("Download")


class DownloadsTab(QWidget, Ui_DownloadsTab):
    thread: QThread
    dl_queue: List[InstallQueueItemModel] = []
    dl_status = pyqtSignal(int)

    def __init__(self, updates: Set):
        super(DownloadsTab, self).__init__()
        self.setupUi(self)
        self.core = LegendaryCoreSingleton()
        self.signals = GlobalSignalsSingleton()
        self.active_game: Game = None
        self.analysis = None

        self.kill_button.clicked.connect(self.stop_download)

        self.queue_widget = DlQueueWidget()
        self.queue_widget.update_list.connect(self.update_dl_queue)
        self.queue_scroll_contents_layout.addWidget(self.queue_widget)

        self.updates = QGroupBox(self.tr("Updates"))
        self.updates.setObjectName("updates_group")
        self.update_layout = QVBoxLayout(self.updates)
        self.queue_scroll_contents_layout.addWidget(self.updates)

        self.update_widgets: Dict[str, UpdateWidget] = {}

        self.update_text = QLabel(self.tr("No updates available"))
        self.update_layout.addWidget(self.update_text)
        self.update_text.setVisible(len(updates) == 0)

        for app_name in updates:
            self.add_update(app_name)

        self.queue_widget.item_removed.connect(self.queue_item_removed)

        self.signals.install_game.connect(self.get_install_options)
        self.signals.game_uninstalled.connect(self.queue_item_removed)
        self.signals.game_uninstalled.connect(self.remove_update)

        self.signals.add_download.connect(
            lambda app_name: self.add_update(app_name)
        )
        self.signals.game_uninstalled.connect(self.game_uninstalled)

        self.reset_infos()

    def queue_item_removed(self, app_name):
        if w := self.update_widgets.get(app_name):
            w.update_button.setDisabled(False)
            w.update_with_settings.setDisabled(False)

    def add_update(self, app_name: str):
        if old_widget := self.update_widgets.get(app_name, False):
            old_widget.deleteLater()
            self.update_widgets.pop(app_name)
        widget = UpdateWidget(self.core, app_name, self)
        self.update_layout.addWidget(widget)
        self.update_widgets[app_name] = widget
        widget.update_signal.connect(self.get_install_options)
        if QSettings().value("auto_update", False, bool):
            self.get_install_options(
                InstallOptionsModel(app_name=app_name, update=True, silent=True)
            )
            widget.update_button.setDisabled(True)
        self.update_text.setVisible(False)

    def game_uninstalled(self, app_name):
        # game in dl_queue
        for i, item in enumerate(self.dl_queue):
            if item.options.app_name == app_name:
                self.dl_queue.pop(i)
                self.queue_widget.update_queue(self.dl_queue)
            break

        # if game is updating
        if self.active_game and self.active_game.app_name == app_name:
            self.stop_download()

        # game has available update
        if app_name in self.update_widgets.keys():
            self.remove_update(app_name)

    def remove_update(self, app_name):
        if w := self.update_widgets.get(app_name):
            w.deleteLater()
            self.update_widgets.pop(app_name)

        if len(self.update_widgets) == 0:
            self.update_text.setVisible(True)

        self.signals.update_download_tab_text.emit()

    def update_dl_queue(self, dl_queue):
        self.dl_queue = dl_queue

    def stop_download(self):
        self.thread.kill()
        self.kill_button.setEnabled(False)

    def install_game(self, queue_item: InstallQueueItemModel):
        if self.active_game is None:
            self.start_installation(queue_item)
        else:
            self.dl_queue.append(queue_item)
            self.queue_widget.update_queue(self.dl_queue)

    def start_installation(self, queue_item: InstallQueueItemModel):
        if self.dl_queue:
            self.dl_queue.pop(0)
            self.queue_widget.update_queue(self.dl_queue)
        self.active_game = queue_item.download.game
        self.thread = DownloadThread(self.core, queue_item)
        self.thread.ret_status.connect(self.status)
        self.thread.ui_update.connect(self.progress_update)
        self.thread.start()
        self.kill_button.setDisabled(False)
        self.analysis = queue_item.download.analysis
        self.dl_name.setText(self.active_game.app_title)

        self.signals.installation_started.emit(self.active_game.app_name)

    @pyqtSlot(DownloadThread.ReturnStatus)
    def status(self, result: DownloadThread.ReturnStatus):
        if result.ret_code == result.ReturnCode.FINISHED:
            if result.shortcuts:
                if not create_desktop_link(result.app_name, self.core, "desktop"):
                    # maybe add it to download summary, to show in finished downloads
                    pass
                else:
                    logger.info("Desktop shortcut written")

            self.dl_name.setText(self.tr("Download finished. Reload library"))
            logger.info(f"Download finished: {self.active_game.app_title}")

            game = self.active_game
            self.active_game = None

            if self.dl_queue:
                if self.dl_queue[0].download.game.app_name == game.app_name:
                    self.dl_queue.pop(0)
                    self.queue_widget.update_queue(self.dl_queue)

            if game.app_name in self.update_widgets.keys():
                igame = self.core.get_installed_game(game.app_name)
                if (
                    self.core.get_asset(
                        game.app_name, igame.platform, False
                    ).build_version
                    == igame.version
                ):
                    self.remove_update(game.app_name)

            self.signals.send_notification.emit(game.app_title)
            self.signals.update_gamelist.emit([game.app_name])
            self.signals.update_download_tab_text.emit()

            self.signals.installation_finished.emit(True, game.app_name)

            self.reset_infos()

            if len(self.dl_queue) != 0:
                self.start_installation(self.dl_queue[0])
            else:
                self.queue_widget.update_queue(self.dl_queue)

        elif result.ret_code == result.ReturnCode.ERROR:
            QMessageBox.warning(self, self.tr("Error"), f"Download error: {result.message}")

        elif result.ret_code == result.ReturnCode.STOPPED:
            self.reset_infos()
            if w := self.update_widgets.get(self.active_game.app_name):
                w.update_button.setDisabled(False)
                w.update_with_settings.setDisabled(False)
            self.signals.installation_finished.emit(False, self.active_game.app_name)
            self.active_game = None
            if self.dl_queue:
                self.start_installation(self.dl_queue[0])

    def reset_infos(self):
        self.kill_button.setDisabled(True)
        self.dl_name.setText(self.tr("No active download"))
        self.progress_bar.setValue(0)
        self.dl_speed.setText("n/a")
        self.time_left.setText("n/a")
        self.cache_used.setText("n/a")
        self.downloaded.setText("n/a")
        self.analysis = None

    def progress_update(self, ui_update: UIUpdate):
        self.progress_bar.setValue(
            100 * ui_update.total_downloaded // self.analysis.dl_size
        )
        self.dl_speed.setText(f"{get_size(ui_update.download_speed)}/s")
        self.cache_used.setText(
            f"{get_size(ui_update.cache_usage) if ui_update.cache_usage > 1023 else '0KB'}"
        )
        self.downloaded.setText(
            f"{get_size(ui_update.total_downloaded)} / {get_size(self.analysis.dl_size)}"
        )
        self.time_left.setText(self.get_time(ui_update.estimated_time_left))
        self.signals.dl_progress.emit(
            100 * ui_update.total_downloaded // self.analysis.dl_size
        )

    def get_time(self, seconds: Union[int, float]) -> str:
        return str(datetime.timedelta(seconds=seconds))

    def on_install_dialog_closed(self, download_item: InstallQueueItemModel):
        if download_item:
            self.install_game(download_item)
            # lk: In case the download in comming from game verification/repair
            if w := self.update_widgets.get(download_item.options.app_name):
                w.update_button.setDisabled(True)
                w.update_with_settings.setDisabled(True)
            self.signals.set_main_tab_index.emit(1)
        else:
            if w := self.update_widgets.get(download_item.options.app_name):
                w.update_button.setDisabled(False)
                w.update_with_settings.setDisabled(False)

    def get_install_options(self, options: InstallOptionsModel):

        install_dialog = InstallDialog(
            InstallQueueItemModel(options=options),
            update=options.update,
            silent=options.silent,
            parent=self,
        )
        install_dialog.result_ready.connect(self.on_install_dialog_closed)
        install_dialog.execute()

    @property
    def is_download_active(self):
        return self.active_game is not None


class UpdateWidget(QWidget):
    update_signal = pyqtSignal(InstallOptionsModel)

    def __init__(self, core: LegendaryCore, app_name: str, parent):
        super(UpdateWidget, self).__init__(parent=parent)
        self.core = core
        self.game: Game = core.get_game(app_name)
        self.igame: InstalledGame = self.core.get_installed_game(app_name)

        layout = QVBoxLayout()
        self.title = QLabel(self.igame.title)
        layout.addWidget(self.title)

        self.update_button = QPushButton(self.tr("Update Game"))
        self.update_button.clicked.connect(lambda: self.update_game(True))
        self.update_with_settings = QPushButton("Update with settings")
        self.update_with_settings.clicked.connect(lambda: self.update_game(False))
        layout.addWidget(self.update_button)
        layout.addWidget(self.update_with_settings)
        layout.addWidget(
            QLabel(
                self.tr("Version: <b>")
                + self.igame.version
                + "</b> >> <b>"
                + self.game.app_version(self.igame.platform)
                + "</b>"
            )
        )

        self.setLayout(layout)

    def update_game(self, auto: bool):
        self.update_button.setDisabled(True)
        self.update_with_settings.setDisabled(True)
        self.update_signal.emit(
            InstallOptionsModel(app_name=self.igame.app_name, silent=auto)
        )  # True if settings
