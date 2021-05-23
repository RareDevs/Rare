import os
from multiprocessing import Queue as MPQueue

from PyQt5.QtCore import Qt, QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QDialog, QFileDialog, QCheckBox

from custom_legendary.core import LegendaryCore
from custom_legendary.utils.selective_dl import games
from rare.ui.components.dialogs.install_dialog import Ui_InstallDialog
from rare.utils.extra_widgets import PathEdit
from rare.utils.models import InstallDownloadModel, InstallQueueItemModel
from rare.utils.utils import get_size


class InstallDialog(QDialog, Ui_InstallDialog):

    def __init__(self, core: LegendaryCore, dl_item: InstallQueueItemModel, update=False, parent=None):
        super(InstallDialog, self).__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowStaysOnTopHint)
        self.setupUi(self)

        self.core = core
        self.dl_item = dl_item
        self.dl_item.status_q = MPQueue()
        self.app_name = self.dl_item.options.app_name
        self.game = self.core.get_game(self.app_name)
        self.update_game = update

        self.threadpool = QThreadPool(self)
        self.threadpool.setMaxThreadCount(1)

        header = self.tr("Update") if update else self.tr("Install")
        self.install_dialog_label.setText(f"<h3>{header} \"{self.game.app_title}\"</h3>")
        self.setWindowTitle(f"{self.windowTitle()} - {header} \"{self.game.app_title}\"")

        if self.core.lgd.config.has_option("Legendary", "install_dir"):
            default_path = self.core.lgd.config.get("Legendary", "install_dir")
        else:
            default_path = os.path.expanduser("~/legendary")
        if not default_path:
            default_path = os.path.expanduser("~/legendary")

        self.install_dir_edit = PathEdit(text=default_path,
                                         file_type=QFileDialog.DirectoryOnly,
                                         edit_func=self.on_option_widget_changed)
        self.install_dir_layout.addWidget(self.install_dir_edit)

        if update:
            self.install_dir_label.setVisible(False)
            self.install_dir_edit.setVisible(False)

        if self.core.lgd.config.has_option("Legendary", "max_workers"):
            max_workers = self.core.lgd.config.get("Legendary", "max_workers")
        else:
            max_workers = 0
        self.max_workers_spin.setValue(int(max_workers))
        self.max_workers_spin.valueChanged.connect(self.on_option_widget_changed)

        self.force_download_check.stateChanged.connect(self.on_option_widget_changed)
        self.ignore_space_check.stateChanged.connect(self.on_option_widget_changed)
        self.download_only_check.stateChanged.connect(self.on_option_widget_changed)

        self.sdl_list_checks = list()
        try:
            for key, info in games[self.app_name].items():
                cb = QDataCheckBox(info['name'], info['tags'])
                if key == '__required':
                    self.dl_item.options.sdl_list.extend(info['tags'])
                    cb.setChecked(True)
                    cb.setDisabled(True)
                self.sdl_list_layout.addWidget(cb)
                self.sdl_list_checks.append(cb)
            self.sdl_list_frame.resize(self.sdl_list_frame.minimumSize())
            for cb in self.sdl_list_checks:
                cb.stateChanged.connect(self.on_option_widget_changed)
        except KeyError:
            self.sdl_list_frame.setVisible(False)
            self.sdl_list_label.setVisible(False)

        self.get_options()
        self.get_download_info()

        self.cancel_button.clicked.connect(self.on_cancel_button_clicked)
        self.verify_button.clicked.connect(self.get_download_info)
        self.install_button.clicked.connect(self.on_install_button_clicked)

        self.options_changed = False
        self.worker_running = False

        self.resize(self.minimumSize())
        self.setFixedSize(self.size())

    def get_options(self):
        self.dl_item.options.base_path = self.install_dir_edit.text() if not self.update_game else None
        self.dl_item.options.max_workers = self.max_workers_spin.value()
        self.dl_item.options.force = self.force_download_check.isChecked()
        self.dl_item.options.ignore_space_req = self.ignore_space_check.isChecked()
        self.dl_item.options.no_install = self.download_only_check.isChecked()
        self.dl_item.options.sdl_list = ['']
        for cb in self.sdl_list_checks:
            if data := cb.isChecked():
                self.dl_item.options.sdl_list.extend(data)

    def get_download_item(self, path=None, silent=False):
        if path:
            self.install_dir_edit.setText(path)
        if silent:
            self.threadpool.waitForDone()
        else:
            self.exec_()
        return self.dl_item

    def get_download_info(self):
        message = self.tr("Updating...")
        self.download_size_info_label.setText(message)
        self.download_size_info_label.setStyleSheet("font-style: italic; font-weight: normal")
        self.install_size_info_label.setText(message)
        self.install_size_info_label.setStyleSheet("font-style: italic; font-weight: normal")
        self.verify_button.setEnabled(False)
        self.install_button.setEnabled(False)
        self.options_changed = False
        self.worker_running = True
        info_worker = InstallInfoWorker(self.core, self.dl_item)
        info_worker.setAutoDelete(True)
        info_worker.signals.finished.connect(self.on_worker_finished)
        self.threadpool.start(info_worker)

    def on_option_widget_changed(self):
        self.options_changed = True
        self.install_button.setEnabled(False)
        self.verify_button.setEnabled(not self.worker_running)
        self.get_options()

    def on_cancel_button_clicked(self):
        self.threadpool.waitForDone()
        self.dl_item.download = None
        self.threadpool.clear()
        self.close()

    def on_install_button_clicked(self):
        self.threadpool.clear()
        self.close()

    def on_worker_finished(self, dl_item: InstallQueueItemModel):
        # TODO: Check available size and act accordingly
        # TODO:     (show message in label | color it | disable install unless ignore)
        # TODO: Find a way to get the installation size delta and show it
        self.worker_running = False
        if dl_item:
            self.dl_item = dl_item
            download_size = self.dl_item.download.analysis.dl_size
            install_size = self.dl_item.download.analysis.install_size
            if download_size:
                self.download_size_info_label.setText("{}".format(get_size(download_size)))
                self.download_size_info_label.setStyleSheet("font-style: normal; font-weight: bold")
                self.install_button.setEnabled(not self.options_changed)
            else:
                self.install_size_info_label.setText(self.tr("Game already installed"))
                self.install_size_info_label.setStyleSheet("font-style: italics; font-weight: normal")
            self.install_size_info_label.setText("{}".format(get_size(install_size)))
            self.install_size_info_label.setStyleSheet("font-style: normal; font-weight: bold")
        else:
            self.download_size_info_label.setText("Error")
            self.install_size_info_label.setText("Error")
        self.verify_button.setEnabled(self.options_changed)
        self.sdl_list_frame.setEnabled(True)

    def closeEvent(self, a0: QCloseEvent) -> None:
        self.on_cancel_button_clicked()


class InstallInfoWorkerSignals(QObject):
    finished = pyqtSignal(InstallQueueItemModel)


class InstallInfoWorker(QRunnable):

    def __init__(self, core: LegendaryCore, dl_item: InstallQueueItemModel):
        super(InstallInfoWorker, self).__init__()
        self.signals = InstallInfoWorkerSignals()
        self.core = core
        self.dl_item = dl_item

    @pyqtSlot()
    def run(self):
        try:
            download = InstallDownloadModel(*self.core.prepare_download(
                app_name=self.dl_item.options.app_name,
                base_path=self.dl_item.options.base_path,
                force=self.dl_item.options.force,
                no_install=self.dl_item.options.no_install,
                status_q=self.dl_item.status_q,
                # max_shm=,
                max_workers=self.dl_item.options.max_workers,
                # game_folder=,
                # disable_patching=,
                # override_manifest=,
                # override_old_manifest=,
                # override_base_url=,
                # platform_override=,
                # file_prefix_filter=,
                # file_exclude_filter=,
                # file_install_tag=,
                # dl_optimizations=,
                # dl_timeout=,
                repair=self.dl_item.options.repair,
                # repair_use_latest=,
                ignore_space_req=self.dl_item.options.ignore_space_req,
                # disable_delta=,
                # override_delta_manifest=,
                # reset_sdl=,
                sdl_prompt=lambda app_name, title: self.dl_item.options.sdl_list
            ))
            self.dl_item.download = download
        except:
            self.dl_item.download = None
        self.signals.finished.emit(self.dl_item)
        return


class QDataCheckBox(QCheckBox):

    def __init__(self, text, data=None, parent=None):
        super(QDataCheckBox, self).__init__(parent)
        self.setText(text)
        self.data = data

    def isChecked(self):
        if super(QDataCheckBox, self).isChecked():
            return self.data
        else:
            return False
