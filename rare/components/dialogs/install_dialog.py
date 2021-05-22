import os

from PyQt5.QtCore import Qt, QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QDialog, QFileDialog, QCheckBox

from custom_legendary.core import LegendaryCore
from custom_legendary.utils.selective_dl import games
from rare.ui.components.dialogs.install_dialog import Ui_InstallDialog
from rare.utils.extra_widgets import PathEdit
from rare.utils.models import InstallOptions
from rare.utils.utils import get_size


class InstallDialog(QDialog, Ui_InstallDialog):
    options = False

    def __init__(self, app_name, core: LegendaryCore, update=False, parent=None):
        super(InstallDialog, self).__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setupUi(self)

        self.core = core
        self.app_name = app_name
        self.game = self.core.get_game(app_name)
        self.update_game = update

        self.threadpool = QThreadPool.globalInstance()

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
                                         edit_func=self.on_install_dir_text_changed)
        self.install_dir_layout.addWidget(self.install_dir_edit)

        if update:
            self.install_dir_label.setVisible(False)
            self.install_dir_edit.setVisible(False)

        if self.core.lgd.config.has_option("Legendary", "max_workers"):
            max_workers = self.core.lgd.config.get("Legendary", "max_workers")
        else:
            max_workers = 0
        self.max_workers_spin.setValue(int(max_workers))

        self.sdl_list_checks = list()
        self.tags = ['']
        try:
            for key, info in games[app_name].items():
                cb = QDataCheckBox(info['name'], info['tags'])
                if key == '__required':
                    self.tags.extend(info['tags'])
                    cb.setChecked(True)
                    cb.setDisabled(True)
                self.sdl_list_layout.addWidget(cb)
                self.sdl_list_checks.append(cb)
            self.sdl_list_frame.resize(self.sdl_list_frame.minimumSize())
            for cb in self.sdl_list_checks:
                cb.stateChanged.connect(self.on_sdl_checkbox_changed)
        except KeyError:
            self.sdl_list_frame.setVisible(False)
            self.sdl_list_label.setVisible(False)

        self.get_install_info(app_name, default_path, self.tags)

        self.install_button.clicked.connect(self.on_install_button_clicked)
        self.cancel_button.clicked.connect(self.on_cancel_button_clicked)

        self.resize(self.minimumSize())
        self.setFixedSize(self.size())

    def get_install_options(self, path=None):
        if path:
            self.install_dir_edit.setText(path)
        self.exec_()
        return self.options

    def get_install_info(self, app_name, path, tags):
        message = self.tr("Updating...")
        self.download_size_info_label.setText(message)
        self.download_size_info_label.setStyleSheet("font-style: italic; font-weight: normal")
        self.install_size_info_label.setText(message)
        self.install_size_info_label.setStyleSheet("font-style: italic; font-weight: normal")
        self.install_button.setEnabled(False)
        self.sdl_list_frame.setEnabled(False)
        info_worker = InstallInfoWorker(app_name, path, tags, self.core)
        info_worker.setAutoDelete(True)
        info_worker.signals.finished.connect(self.on_worker_finished)
        self.threadpool.start(info_worker)

    def on_sdl_checkbox_changed(self):
        self.tags = ['']
        for cb in self.sdl_list_checks:
            if data := cb.isChecked():
                self.tags.extend(data)
        self.get_install_info(self.app_name, self.install_dir_edit.text(), self.tags)

    def on_install_dir_text_changed(self, path: str):
        self.get_install_info(self.app_name, path, self.tags)

    def on_install_button_clicked(self):
        self.options = InstallOptions(
            app_name=self.app_name,
            path=self.install_dir_edit.text() if not self.update_game else None,
            max_workers=self.max_workers_spin.value(),
            force=self.force_download_check.isChecked(),
            ignore_free_space=self.ignore_space_check.isChecked(),
            download_only=self.download_only_check.isChecked(),
            sdl_list=self.tags
        )
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
        self.sdl_list_frame.setEnabled(True)


class InstallInfoWorkerSignals(QObject):
    finished = pyqtSignal(tuple)


class InstallInfoWorker(QRunnable):

    def __init__(self, app_name, path, tags, core: LegendaryCore):
        super(InstallInfoWorker, self).__init__()
        self.signals = InstallInfoWorkerSignals()
        self.core = core
        self.app_name = app_name
        self.path = path
        self.tags = tags

    @pyqtSlot()
    def run(self):
        try:
            dlm, analysis, game, igame, repair, repair_file = self.core.prepare_download(
                app_name=self.app_name,
                base_path=self.path,
                sdl_prompt=lambda app_name, title: self.tags
            )
            self.signals.finished.emit((analysis.dl_size, analysis.install_size))
        except:
            self.signals.finished.emit((None, None))
        return


class QDataCheckBox(QCheckBox):

    def __init__(self, text, data=None):
        super(QDataCheckBox, self).__init__()
        self.setText(text)
        self.data = data

    def isChecked(self):
        if super(QDataCheckBox, self).isChecked():
            return self.data
        else:
            return False
