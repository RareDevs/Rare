import datetime
import platform
from logging import getLogger
from typing import Union, Optional

from PyQt5.QtCore import pyqtSignal, QSettings, pyqtSlot, QThreadPool, Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QWidget,
    QMessageBox, QScrollArea, QVBoxLayout, QSizePolicy,
)

from rare.components.dialogs.install_dialog import InstallDialog
from rare.components.dialogs.uninstall_dialog import UninstallDialog
from rare.lgndr.models.downloading import UIUpdate
from rare.models.game import RareGame
from rare.models.install import InstallOptionsModel, InstallQueueItemModel, UninstallOptionsModel
from rare.shared import RareCore
from rare.shared.workers.install_info import InstallInfoWorker
from rare.shared.workers.uninstall import UninstallWorker
from rare.utils.misc import format_size
from rare.utils.paths import create_desktop_link, desktop_links_supported
from .download import DownloadWidget
from .groups import UpdateGroup, QueueGroup
from .thread import DlThread, DlResultModel, DlResultCode
from .widgets import UpdateWidget, QueueWidget

logger = getLogger("Download")


def get_time(seconds: Union[int, float]) -> str:
    return str(datetime.timedelta(seconds=seconds))


class DownloadsTab(QWidget):
    # int: number of updates
    update_title = pyqtSignal(int)

    def __init__(self, parent=None):
        super(DownloadsTab, self).__init__(parent=parent)
        self.rcore = RareCore.instance()
        self.core = RareCore.instance().core()
        self.signals = RareCore.instance().signals()
        self.args = RareCore.instance().args()

        self.__thread: Optional[DlThread] = None

        layout = QVBoxLayout(self)

        self.download_widget = DownloadWidget(self)
        self.download_widget.ui.kill_button.clicked.connect(self.stop_download)
        layout.addWidget(self.download_widget)

        self.queue_scrollarea = QScrollArea(self)
        self.queue_scrollarea.setWidgetResizable(True)
        self.queue_scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.queue_scrollarea.setFrameStyle(QScrollArea.Plain | QScrollArea.NoFrame)
        layout.addWidget(self.queue_scrollarea)

        queue_contents = QWidget(self.queue_scrollarea)
        queue_contents.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.queue_scrollarea.setWidget(queue_contents)

        queue_contents_layout = QVBoxLayout(queue_contents)
        queue_contents_layout.setContentsMargins(0, 0, 3, 0)

        self.queue_group = QueueGroup(self)
        self.queue_group.update_count.connect(self.update_queues_count)
        self.queue_group.removed.connect(self.__on_queue_removed)
        self.queue_group.force.connect(self.__on_queue_force)
        queue_contents_layout.addWidget(self.queue_group)

        self.updates_group = UpdateGroup(self)
        self.updates_group.update_count.connect(self.update_queues_count)
        self.updates_group.enqueue.connect(self.__get_install_options)
        queue_contents_layout.addWidget(self.updates_group)

        self.__check_updates()
        self.__reset_download()

        self.signals.game.install.connect(self.__get_install_options)
        self.signals.game.uninstall.connect(self.__get_uninstall_options)
        self.signals.download.enqueue.connect(self.__add_update)
        self.signals.download.dequeue.connect(self.__remove_update)

        self.__forced_item: Optional[InstallQueueItemModel] = None
        self.__omit_requeue = False

    @pyqtSlot()
    @pyqtSlot(int)
    def update_queues_count(self):
        count = self.updates_group.count() + self.queue_group.count() +  (1 if self.is_download_active else 0)
        self.update_title.emit(count)

    @property
    def is_download_active(self):
        return self.__thread is not None

    def __check_updates(self):
        for rgame in self.rcore.updates:
            self.__add_update(rgame)

    @pyqtSlot(str)
    @pyqtSlot(RareGame)
    def __add_update(self, update: Union[str,RareGame]):
        if isinstance(update, str):
            update = self.rcore.get_game(update)
        if update.metadata.auto_update or QSettings().value("auto_update", False, bool):
            self.__get_install_options(
                InstallOptionsModel(app_name=update.app_name, update=True, silent=True)
            )
        else:
            self.updates_group.append(update.game, update.igame)
        self.update_queues_count()

    @pyqtSlot(str)
    def __remove_update(self, app_name):
        if self.__thread and self.__thread.item.options.app_name == app_name:
            self.stop_download(omit_queue=True)
        if self.queue_group.contains(app_name):
            self.queue_group.remove(app_name)
        if self.updates_group.contains(app_name):
            self.updates_group.remove(app_name)

    @pyqtSlot(str)
    def __on_queue_removed(self, app_name: str):
        """
        Handle removing a queued item.
        If the item exists in the updates (it means a repair was removed), re-enable the buttons.
        If it doesn't exist in the updates, recreate the widget.
        :param app_name:
        :return:
        """
        if self.updates_group.contains(app_name):
            self.updates_group.set_widget_enabled(app_name, True)
        else:
            rgame = self.rcore.get_game(app_name)
            if rgame.is_installed and rgame.has_update:
                self.__add_update(app_name)

    @pyqtSlot(InstallQueueItemModel)
    def __on_queue_force(self, item: InstallQueueItemModel):
        if self.__thread:
            self.stop_download()
            self.__forced_item = item
        else:
            self.__start_download(item)

    def stop_download(self, omit_queue=False):
        """
        Stops the active download, by optionally skipping the queue

        :param omit_queue: bool
            If `True`, the stopped download won't be added back to the queue.
            Defaults to `False`
        :return:
        """
        self.__thread.kill()
        self.download_widget.ui.kill_button.setEnabled(False)
        # lk: if we are exiting Rare, wait for thread to finish
        # `self.on_exit` control whether we try to add the download
        # back in the queue. If we are on exit we wait for the thread
        # to finish, we do not care about handling the result really
        self.__omit_requeue = omit_queue
        if omit_queue:
            self.__thread.wait()

    def __refresh_download(self, item: InstallQueueItemModel):
        worker = InstallInfoWorker(self.core, item.options)
        worker.signals.result.connect(
            lambda d: self.__start_download(InstallQueueItemModel(options=item.options, download=d))
        )
        worker.signals.failed.connect(
            lambda m: logger.error(f"Failed to refresh download for {item.options.app_name} with error: {m}")
        )
        worker.signals.finished.connect(
            lambda: logger.info(f"Download refresh worker finished for {item.options.app_name}")
        )
        QThreadPool.globalInstance().start(worker)

    def __start_download(self, item: InstallQueueItemModel):
        rgame = self.rcore.get_game(item.options.app_name)
        if not rgame.is_idle:
            logger.error(f"Can't start download {item.options.app_name} due to non-idle state {rgame.state}")
            # lk: invalidate the queue item in case the game was uninstalled
            self.__requeue_download(InstallQueueItemModel(options=item.options))
            return
        if item.expired:
            self.__refresh_download(item)
            return
        rgame.state = RareGame.State.DOWNLOADING
        thread = DlThread(item, self.rcore.get_game(item.options.app_name), self.core, self.args.debug)
        thread.result.connect(self.__on_download_result)
        thread.progress.connect(self.__on_download_progress)
        thread.finished.connect(thread.deleteLater)
        thread.start()
        self.__thread = thread
        self.download_widget.ui.kill_button.setDisabled(False)
        self.download_widget.ui.dl_name.setText(item.download.game.app_title)
        self.download_widget.setPixmap(
            RareCore.instance().image_manager().get_pixmap(rgame.app_name, True)
        )

    @pyqtSlot(UIUpdate, object)
    def __on_download_progress(self, ui_update: UIUpdate, dl_size: int):
        self.download_widget.ui.progress_bar.setValue(int(ui_update.progress))
        self.download_widget.ui.dl_speed.setText(f"{format_size(ui_update.download_compressed_speed)}/s")
        self.download_widget.ui.cache_used.setText(
            f"{format_size(ui_update.cache_usage) if ui_update.cache_usage > 1023 else '0KB'}"
        )
        self.download_widget.ui.downloaded.setText(
            f"{format_size(ui_update.total_downloaded)} / {format_size(dl_size)}"
        )
        self.download_widget.ui.time_left.setText(get_time(ui_update.estimated_time_left))

    def __requeue_download(self, item: InstallQueueItemModel):
        rgame = self.rcore.get_game(item.options.app_name)
        self.queue_group.push_front(item, rgame.igame)
        logger.info(f"Re-queued download for {rgame.app_name} ({rgame.app_title})")

    @pyqtSlot(DlResultModel)
    def __on_download_result(self, result: DlResultModel):
        if result.code == DlResultCode.FINISHED:
            logger.info(f"Download finished: {result.options.app_name}")
            if result.shortcut and desktop_links_supported():
                if not create_desktop_link(
                    app_name=result.options.app_name,
                    app_title=result.shortcut_title,
                    link_name=result.shortcut_name,
                    link_type="desktop",
                ):
                    # maybe add it to download summary, to show in finished downloads
                    logger.error(f"Failed to create desktop link on {platform.system()}")
                else:
                    logger.info(f"Created desktop link {result.shortcut_name} for {result.options.app_name}")

            if result.options.overlay:
                self.signals.application.overlay_installed.emit()
            else:
                self.signals.application.notify.emit(result.options.app_name)

            if self.updates_group.contains(result.options.app_name):
                self.updates_group.set_widget_enabled(result.options.app_name, True)

        elif result.code == DlResultCode.ERROR:
            logger.error(f"Download error: {result.options.app_name} ({result.message})")
            QMessageBox.warning(self, self.tr("Error"), self.tr("Download error: {}").format(result.message))

        elif result.code == DlResultCode.STOPPED:
            logger.info(f"Download stopped: {result.options.app_name}")
            if not self.__omit_requeue:
                self.__requeue_download(InstallQueueItemModel(options=result.options))
            else:
                return

        # lk: if we finished a repair, and we have a disabled update, re-enable it
        if self.updates_group.contains(result.options.app_name):
            self.updates_group.set_widget_enabled(result.options.app_name, True)

        if result.code == DlResultCode.FINISHED and self.queue_group.count():
            self.__start_download(self.queue_group.pop_front())
        elif result.code == DlResultCode.STOPPED and self.__forced_item:
            self.__start_download(self.__forced_item)
            self.__forced_item = None
        else:
            self.__reset_download()

    def __reset_download(self):
        self.download_widget.setPixmap(QPixmap())
        self.download_widget.ui.kill_button.setDisabled(True)
        self.download_widget.ui.dl_name.setText(self.tr("No active download"))
        self.download_widget.ui.progress_bar.setValue(0)
        self.download_widget.ui.dl_speed.setText("...")
        self.download_widget.ui.time_left.setText("...")
        self.download_widget.ui.cache_used.setText("...")
        self.download_widget.ui.downloaded.setText("...")
        self.__thread = None

    @pyqtSlot(InstallOptionsModel)
    def __get_install_options(self, options: InstallOptionsModel):
        install_dialog = InstallDialog(
            self.rcore.get_game(options.app_name),
            options=options,
            parent=self,
        )
        install_dialog.result_ready.connect(self.__on_install_dialog_closed)
        install_dialog.execute()

    @pyqtSlot(InstallQueueItemModel)
    def __on_install_dialog_closed(self, item: InstallQueueItemModel):
        if item and not item.download.game.is_dlc and not item.download.analysis.dl_size:
            self.rcore.get_game(item.download.game.app_name).set_installed(True)
            return
        if item:
            # lk: start update only if there is no other active thread and there is no queue
            if self.__thread is None and not self.queue_group.count():
                self.__start_download(item)
            else:
                rgame = self.rcore.get_game(item.options.app_name)
                self.queue_group.push_back(item, rgame.igame)
            # lk: Handle repairing into the current version
            # When we add something to the queue from repair, we might select to update or not
            # if we do select to update with repair, we can remove the widget from the updates groups
            # otherwise we disable it and keep it in the updates
            if self.updates_group.contains(item.options.app_name):
                if item.download.igame.version == self.updates_group.get_widget_version(item.options.app_name):
                    self.updates_group.remove(item.options.app_name)
                else:
                    self.updates_group.set_widget_enabled(item.options.app_name, False)
        else:
            if self.updates_group.contains(item.options.app_name):
                self.updates_group.set_widget_enabled(item.options.app_name, True)

    @pyqtSlot(UninstallOptionsModel)
    def __get_uninstall_options(self, options: UninstallOptionsModel):
        uninstall_dialog = UninstallDialog(
            self.rcore.get_game(options.app_name),
            options=options,
            parent=self,
        )
        uninstall_dialog.result_ready.connect(self.__on_uninstall_dialog_closed)
        uninstall_dialog.exec()

    @pyqtSlot(UninstallOptionsModel)
    def __on_uninstall_dialog_closed(self, options: UninstallOptionsModel):
        if options and options.accepted:
            rgame = self.rcore.get_game(options.app_name)
            rgame.set_installed(False)
            worker = UninstallWorker(self.core, rgame, options)
            worker.signals.result.connect(self.__on_uninstall_worker_result)
            QThreadPool.globalInstance().start(worker)

    @pyqtSlot(RareGame, bool, str)
    def __on_uninstall_worker_result(self, rgame: RareGame, success: bool, message: str):
        if not success:
            QMessageBox.warning(None, self.tr("Uninstall - {}").format(rgame.title), message, QMessageBox.Close)
