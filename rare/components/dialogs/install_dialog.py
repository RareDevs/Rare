import os
import platform
from multiprocessing import Queue as MPQueue

from PyQt5.QtCore import Qt, QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QDialog, QFileDialog, QCheckBox, QMessageBox

from legendary.core import LegendaryCore
from legendary.utils.selective_dl import games
from rare import shared
from rare.ui.components.dialogs.install_dialog import Ui_InstallDialog
from rare.utils.extra_widgets import PathEdit
from rare.utils.models import InstallDownloadModel, InstallQueueItemModel
from rare.utils.utils import get_size


class InstallDialog(QDialog, Ui_InstallDialog):
    result_ready = pyqtSignal(InstallQueueItemModel)

    def __init__(self, dl_item: InstallQueueItemModel, update=False, silent=False, parent=None):
        super(InstallDialog, self).__init__(parent)
        self.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)

        self.core = shared.core
        self.dl_item = dl_item
        self.dl_item.status_q = MPQueue()
        self.app_name = self.dl_item.options.app_name
        self.game = self.core.get_game(self.app_name)
        self.update = update
        self.silent = silent

        self.options_changed = False
        self.worker_running = False
        self.reject_close = True

        self.threadpool = QThreadPool(self)
        self.threadpool.setMaxThreadCount(1)

        header = self.tr("Update") if update else self.tr("Install")
        self.install_dialog_label.setText(f"<h3>{header} \"{self.game.app_title}\"</h3>")
        self.setWindowTitle(f"{self.windowTitle()} - {header} \"{self.game.app_title}\"")

        default_path = os.path.expanduser("~/legendary")
        if self.core.lgd.config.has_option("Legendary", "install_dir"):
            default_path = self.core.lgd.config.get("Legendary", "install_dir")

        self.install_dir_edit = PathEdit(path=default_path,
                                         file_type=QFileDialog.DirectoryOnly,
                                         edit_func=self.option_changed,
                                         parent=self)
        self.install_dir_layout.addWidget(self.install_dir_edit)

        if self.update:
            self.install_dir_label.setVisible(False)
            self.install_dir_edit.setVisible(False)

        self.warn_label.setVisible(False)
        self.warn_message.setVisible(False)

        platforms = ["Windows"]
        if dl_item.options.app_name in shared.api_results.bit32_games:
            platforms.append("Win32")
        if dl_item.options.app_name in shared.api_results.mac_games:
            platforms.append("Mac")
        self.platform_combo_box.addItems(platforms)
        self.platform_combo_box.currentIndexChanged.connect(lambda: self.option_changed(None))
        self.platform_combo_box.currentIndexChanged.connect(lambda i: QMessageBox.warning(self, "Warning", self.tr(
            "You will not be able to run the Game if you choose {}").format(self.platform_combo_box.itemText(i)))
        if (self.platform_combo_box.currentText() == "Mac" and platform.system() != "Darwin") else None)

        if platform.system() == "Darwin" and "Mac" in platforms:
            self.platform_combo_box.setCurrentIndex(platforms.index("Mac"))

        if self.core.lgd.config.has_option("Legendary", "max_workers"):
            max_workers = self.core.lgd.config.get("Legendary", "max_workers")
        else:
            max_workers = 0
        self.max_workers_spin.setValue(int(max_workers))
        self.max_workers_spin.valueChanged.connect(self.option_changed)

        self.force_download_check.stateChanged.connect(self.option_changed)
        self.ignore_space_check.stateChanged.connect(self.option_changed)
        self.download_only_check.stateChanged.connect(lambda: self.non_reload_option_changed("download_only"))

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
                cb.stateChanged.connect(self.option_changed)
        except KeyError:
            self.sdl_list_frame.setVisible(False)
            self.sdl_list_label.setVisible(False)

        self.install_button.setEnabled(False)

        self.cancel_button.clicked.connect(self.cancel_clicked)
        self.verify_button.clicked.connect(self.verify_clicked)
        self.install_button.clicked.connect(self.install_clicked)

        self.resize(self.minimumSize())
        # self.setFixedSize(self.size())

    def execute(self):
        if self.silent:
            self.reject_close = False
            self.get_download_info()
        else:
            self.verify_clicked()
            self.show()

    def get_options(self):
        self.dl_item.options.base_path = self.install_dir_edit.text() if not self.update else None
        self.dl_item.options.max_workers = self.max_workers_spin.value()
        self.dl_item.options.force = self.force_download_check.isChecked()
        self.dl_item.options.ignore_space_req = self.ignore_space_check.isChecked()
        self.dl_item.options.no_install = self.download_only_check.isChecked()
        self.dl_item.options.platform = self.platform_combo_box.currentText()
        self.dl_item.options.sdl_list = ['']
        for cb in self.sdl_list_checks:
            if data := cb.isChecked():
                # noinspection PyTypeChecker
                self.dl_item.options.sdl_list.extend(data)

    def get_download_info(self):
        self.dl_item.download = None
        info_worker = InstallInfoWorker(self.core, self.dl_item)
        info_worker.setAutoDelete(True)
        info_worker.signals.result.connect(self.on_worker_result)
        info_worker.signals.failed.connect(self.on_worker_failed)
        info_worker.signals.finished.connect(self.on_worker_finished)
        self.worker_running = True
        self.threadpool.start(info_worker)

    def verify_clicked(self):
        message = self.tr("Updating...")
        self.download_size_info_label.setText(message)
        self.download_size_info_label.setStyleSheet("font-style: italic; font-weight: normal")
        self.install_size_info_label.setText(message)
        self.install_size_info_label.setStyleSheet("font-style: italic; font-weight: normal")
        self.cancel_button.setEnabled(False)
        self.verify_button.setEnabled(False)
        self.install_button.setEnabled(False)
        self.options_changed = False
        self.get_options()
        self.get_download_info()

    def option_changed(self, path):
        self.options_changed = True
        self.install_button.setEnabled(False)
        self.verify_button.setEnabled(not self.worker_running)
        return True, path

    def non_reload_option_changed(self, option: str):
        if option == "download_only":
            self.dl_item.options.no_install = self.download_only_check.isChecked()

    def cancel_clicked(self):
        self.dl_item.download = None
        self.reject_close = False
        self.close()

    def install_clicked(self):
        self.reject_close = False
        self.close()

    def on_worker_result(self, dl_item: InstallDownloadModel):
        self.dl_item.download = dl_item
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
        self.verify_button.setEnabled(self.options_changed)
        self.cancel_button.setEnabled(True)
        if self.silent:
            self.close()

    def on_worker_failed(self, message: str):
        error_text = self.tr("Error")
        self.download_size_info_label.setText(error_text)
        self.install_size_info_label.setText(error_text)
        QMessageBox.critical(self, self.windowTitle(), message)
        self.verify_button.setEnabled(self.options_changed)
        self.cancel_button.setEnabled(True)
        if self.silent:
            self.close()

    def on_worker_finished(self):
        self.worker_running = False

    # lk: happens when close() is called, also when top right 'X' is pressed.
    # lk: reject any events not coming from the buttons in case the WM
    # lk: doesn't honor the window hints
    def closeEvent(self, a0: QCloseEvent) -> None:
        if self.reject_close:
            a0.ignore()
        else:
            self.threadpool.clear()
            self.threadpool.waitForDone()
            self.result_ready.emit(self.dl_item)
            a0.accept()


class InstallInfoWorkerSignals(QObject):
    result = pyqtSignal(InstallDownloadModel)
    failed = pyqtSignal(str)
    finished = pyqtSignal()


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
                platform=self.dl_item.options.platform,
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
            if not download.res.failures:
                self.signals.result.emit(download)
            else:
                self.signals.failed.emit("\n".join(str(i) for i in download.res.failures))
        except Exception as e:
            self.signals.failed.emit(str(e))
        self.signals.finished.emit()


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
