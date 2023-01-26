import datetime
from ctypes import c_ulonglong
from logging import getLogger
from typing import Union, Optional

from PyQt5.QtCore import pyqtSignal, QSettings, pyqtSlot, QThreadPool
from PyQt5.QtWidgets import (
    QWidget,
    QMessageBox,
)

from rare.components.dialogs.install_dialog import InstallDialog, InstallInfoWorker
from rare.components.dialogs.uninstall_dialog import UninstallDialog
from rare.lgndr.models.downloading import UIUpdate
from rare.models.game import RareGame
from rare.models.install import InstallOptionsModel, InstallQueueItemModel, UninstallOptionsModel
from rare.shared import RareCore
from rare.shared.workers.uninstall import UninstallWorker
from rare.ui.components.tabs.downloads.downloads_tab import Ui_DownloadsTab
from rare.utils.misc import get_size, create_desktop_link
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
        self.ui = Ui_DownloadsTab()
        self.ui.setupUi(self)
        self.rcore = RareCore.instance()
        self.core = self.rcore.core()
        self.signals = self.rcore.signals()
        self.args = self.rcore.args()

        self.thread: Optional[DlThread] = None
        self.threadpool = QThreadPool.globalInstance()

        self.ui.kill_button.clicked.connect(self.stop_download)

        self.queue_group = QueueGroup(self)
        self.queue_group.update_count.connect(self.update_queues_count)
        self.queue_group.removed.connect(self.__on_queue_removed)
        self.queue_group.force.connect(self.__on_queue_force)
        self.ui.queue_scroll_contents_layout.addWidget(self.queue_group)

        self.updates_group = UpdateGroup(self)
        self.updates_group.update_count.connect(self.update_queues_count)
        self.updates_group.enqueue.connect(self.__get_install_options)
        self.ui.queue_scroll_contents_layout.addWidget(self.updates_group)

        self.__check_updates()

        self.signals.game.install.connect(self.__get_install_options)
        self.signals.game.uninstall.connect(self.__get_uninstall_options)
        self.signals.download.enqueue.connect(self.__add_update)
        self.signals.download.dequeue.connect(self.__remove_update)

        self.__reset_download()

        self.__forced_item: Optional[InstallQueueItemModel] = None
        self.__omit_queue = False

    def __check_updates(self):
        for rgame in self.rcore.updates:
            self.__add_update(rgame)

    @pyqtSlot()
    @pyqtSlot(int)
    def update_queues_count(self):
        count = self.updates_group.count() + self.queue_group.count()
        self.update_title.emit(count)

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
        if self.thread and self.thread.item.options.app_name == app_name:
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
            if self.rcore.get_game(app_name).is_installed:
                self.__add_update(app_name)

    @pyqtSlot(InstallQueueItemModel)
    def __on_queue_force(self, item: InstallQueueItemModel):
        if self.thread:
            self.stop_download()
            self.__forced_item = item
        else:
            self.__start_installation(item)

    def stop_download(self, omit_queue=False):
        """
        Stops the active download, by optionally skipping the queue

        :param omit_queue: bool
            If `True`, the stopped download won't be added back to the queue.
            Defaults to `False`
        :return:
        """
        self.thread.kill()
        self.ui.kill_button.setEnabled(False)
        # lk: if we are exitin Rare, waif for thread to finish
        # `self.on_exit` control whether we try to add the download
        # back in the queue. If we are on exit we wait for the thread
        # to finish, we do not care about handling the result really
        self.__omit_queue = omit_queue
        if omit_queue:
            self.thread.wait()

    def __start_installation(self, item: InstallQueueItemModel):
        thread = DlThread(item, self.rcore.get_game(item.options.app_name), self.core, self.args.debug)
        thread.result.connect(self.__on_download_result)
        thread.progress.connect(self.__on_download_progress)
        thread.finished.connect(thread.deleteLater)
        thread.start()
        self.thread = thread
        self.ui.kill_button.setDisabled(False)
        self.ui.dl_name.setText(item.download.game.app_title)

    @property
    def is_download_active(self):
        return self.thread is not None

    @pyqtSlot(UIUpdate, c_ulonglong)
    def __on_download_progress(self, ui_update: UIUpdate, dl_size: c_ulonglong):
        self.ui.progress_bar.setValue(int(ui_update.progress))
        self.ui.dl_speed.setText(f"{get_size(ui_update.download_compressed_speed)}/s")
        self.ui.cache_used.setText(
            f"{get_size(ui_update.cache_usage) if ui_update.cache_usage > 1023 else '0KB'}"
        )
        self.ui.downloaded.setText(
            f"{get_size(ui_update.total_downloaded)} / {get_size(dl_size.value)}"
        )
        self.ui.time_left.setText(get_time(ui_update.estimated_time_left))

    @pyqtSlot(InstallQueueItemModel)
    def __on_info_worker_result(self, item: InstallQueueItemModel):
        rgame = self.rcore.get_game(item.options.app_name)
        self.queue_group.push_front(item, rgame.igame)
        logger.info(f"Re-queued download for {item.download.game.app_name} ({item.download.game.app_title})")

    @pyqtSlot(str)
    def __on_info_worker_failed(self, message: str):
        logger.error(f"Failed to re-queue stopped download with error: {message}")

    @pyqtSlot()
    def __on_info_worker_finished(self):
        logger.info("Download re-queue worker finished")

    @pyqtSlot(DlResultModel)
    def __on_download_result(self, result: DlResultModel):
        if result.code == DlResultCode.FINISHED:
            if result.shortcuts:
                if not create_desktop_link(result.item.options.app_name, self.core, "desktop"):
                    # maybe add it to download summary, to show in finished downloads
                    pass
                else:
                    logger.info("Desktop shortcut written")
            logger.info(
                f"Download finished: {result.item.download.game.app_name} ({result.item.download.game.app_title})"
            )

            if result.item.options.overlay:
                self.signals.application.overlay_installed.emit()
            else:
                self.signals.application.notify.emit(result.item.download.game.app_title)

            if self.updates_group.contains(result.item.options.app_name):
                self.updates_group.set_widget_enabled(result.item.options.app_name, True)

        elif result.code == DlResultCode.ERROR:
            QMessageBox.warning(self, self.tr("Error"), self.tr("Download error: {}").format(result.message))
            logger.error(f"Download error: {result.message}")

        elif result.code == DlResultCode.STOPPED:
            logger.info(f"Download stopped: {result.item.download.game.app_title}")
            if not self.__omit_queue:
                worker = InstallInfoWorker(self.core, result.item.options)
                worker.signals.result.connect(self.__on_info_worker_result)
                worker.signals.failed.connect(self.__on_info_worker_failed)
                worker.signals.finished.connect(self.__on_info_worker_finished)
                self.threadpool.start(worker)
            else:
                return

        # lk: if we finished a repair, and we have a disabled update, re-enable it
        if self.updates_group.contains(result.item.options.app_name):
            self.updates_group.set_widget_enabled(result.item.options.app_name, True)

        if result.code == DlResultCode.FINISHED and self.queue_group.count():
                self.__start_installation(self.queue_group.pop_front())
        elif result.code == DlResultCode.STOPPED and self.__forced_item:
            self.__start_installation(self.__forced_item)
            self.__forced_item = None
        else:
            self.__reset_download()

    def __reset_download(self):
        self.ui.kill_button.setDisabled(True)
        self.ui.dl_name.setText(self.tr("No active download"))
        self.ui.progress_bar.setValue(0)
        self.ui.dl_speed.setText("n/a")
        self.ui.time_left.setText("n/a")
        self.ui.cache_used.setText("n/a")
        self.ui.downloaded.setText("n/a")
        self.thread = None

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
        if item:
            # lk: start update only if there is no other active thread and there is no queue
            if self.thread is None and not self.queue_group.count():
                self.__start_installation(item)
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
        if options and options.uninstall:
            self.__remove_update(options.app_name)
            worker = UninstallWorker(self.core, self.rcore.get_game(options.app_name), options)
            worker.signals.result.connect(self.__on_uninstall_worker_result)
            self.threadpool.start(worker)

    @pyqtSlot(RareGame, bool, str)
    def __on_uninstall_worker_result(self, rgame: RareGame, success: bool, message: str):
        if not success:
            QMessageBox.warning(None, self.tr("Uninstall - {}").format(rgame.title), message, QMessageBox.Close)
        rgame.set_installed(False)
