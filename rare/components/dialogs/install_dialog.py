import os

from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QDialog, QFileDialog

from custom_legendary.core import LegendaryCore
from rare.ui.components.dialogs.install_dialog import Ui_InstallDialog
from rare.utils.extra_widgets import PathEdit
from rare.utils.utils import get_size


class InstallDialog(QDialog, Ui_InstallDialog):
    infos = False

    def __init__(self, app_name, core: LegendaryCore, update=False):
        super(InstallDialog, self).__init__()
        self.setupUi(self)

        self.core = core
        self.app_name = app_name
        self.game = self.core.get_game(app_name)
        self.update_game = update

        self.threadpool = QThreadPool.globalInstance()

        header_text = self.tr("Update") if update else self.tr("Install")
        self.install_dialog_label.setText("<h3>{} \"{}\"</h3>".format(header_text, self.game.app_title))
        # TODO: Get application name from QApplication instance
        self.setWindowTitle("{} - {} \"{}\"".format("Rare", header_text, self.game.app_title))

        if self.core.lgd.config.has_option("Legendary", "install_dir"):
            default_path = self.core.lgd.config.get("Legendary", "install_dir")
        else:
            default_path = os.path.expanduser("~/legendary")
        if not default_path:
            default_path = os.path.expanduser("~/legendary")

        self.install_dir_path = PathEdit(text=default_path,
                                         file_type=QFileDialog.DirectoryOnly,
                                         edit_func=self.on_install_dir_text_changed)
        self.install_dir_layout.addWidget(self.install_dir_path)

        if update:
            self.install_dir_label.setVisible(False)
            self.install_dir_path.setVisible(False)

        if self.core.lgd.config.has_option("Legendary", "max_workers"):
            max_workers = self.core.lgd.config.get("Legendary", "max_workers")
        else:
            max_workers = 0
        self.max_workers_spin.setValue(int(max_workers))

        self.get_install_info(app_name, default_path)

        self.install_button.clicked.connect(self.on_install_button_clicked)
        self.cancel_button.clicked.connect(self.on_cancel_button_clicked)

        self.resize(self.minimumSizeHint())
        self.setFixedSize(self.size())

    def get_information(self, path=None):
        if path:
            self.install_dir_path.setText(path)
        self.exec_()
        return self.infos

    def get_install_info(self, app_name, default_path):
        updating_text = self.tr("Updating...")
        self.download_size_info_label.setText(updating_text)
        self.download_size_info_label.setStyleSheet("font-style: italic; font-weight: normal")
        self.install_size_info_label.setText(updating_text)
        self.install_size_info_label.setStyleSheet("font-style: italic; font-weight: normal")
        self.install_button.setEnabled(False)
        info_worker = InstallInfoWorker(app_name, default_path, self.core)
        info_worker.setAutoDelete(True)
        info_worker.signals.finished.connect(self.on_worker_finished)
        self.threadpool.start(info_worker)

    def on_install_dir_text_changed(self, path: str):
        self.get_install_info(self.app_name, path)

    def on_install_button_clicked(self):
        self.infos = self.install_dir_path.text() if not self.update_game else None, \
                     self.max_workers_spin.value(), \
                     self.force_download_check.isChecked(), \
                     self.ignore_space_check.isChecked(), \
                     self.download_only_check.isChecked()
        self.threadpool.clear()
        self.close()

    def on_cancel_button_clicked(self):
        self.threadpool.clear()
        self.close()

    def on_worker_finished(self, info: tuple):
        download_size, install_size = info

        # TODO: Check available size and act accordingly
        # TODO:     (show message in label | color it | disable install unless ignore)
        # TODO: Find a way to get the installation size delta and show it

        if download_size is not None and install_size is not None:
            if download_size:
                self.download_size_info_label.setText("{}".format(get_size(download_size)))
                self.download_size_info_label.setStyleSheet("font-style: normal; font-weight: bold")
                self.install_button.setEnabled(True)
            else:
                self.install_size_info_label.setText(self.tr("Game already installed"))
                self.install_size_info_label.setStyleSheet("font-style: italics; font-weight: normal")
            self.install_size_info_label.setText("{}".format(get_size(install_size)))
            self.install_size_info_label.setStyleSheet("font-style: normal; font-weight: bold")
        else:
            self.download_size_info_label.setText("Error")
            self.install_size_info_label.setText("Error")


class InstallInfoWorkerSignals(QObject):
    finished = pyqtSignal(tuple)


class InstallInfoWorker(QRunnable):

    def __init__(self, app_name, path, core: LegendaryCore):
        super(InstallInfoWorker, self).__init__()
        self.signals = InstallInfoWorkerSignals()
        self.core = core
        self.app_name = app_name
        self.path = path

    @pyqtSlot()
    def run(self):
        try:
            dlm, analysis, game, igame, repair, repair_file = self.core.prepare_download(
                app_name=self.app_name,
                base_path=self.path,
            )
            self.signals.finished.emit((analysis.dl_size, analysis.install_size))
        except:
            self.signals.finished.emit((None, None))
        return
