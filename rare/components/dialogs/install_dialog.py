import os
import platform as pf
import shutil
from typing import Tuple, List, Union, Optional

from PyQt5.QtCore import Qt, QThreadPool, QSettings, QCoreApplication
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtGui import QCloseEvent, QKeyEvent
from PyQt5.QtWidgets import QDialog, QFileDialog, QCheckBox, QLayout, QWidget, QVBoxLayout
from legendary.utils.selective_dl import get_sdl_appname

from rare.models.game import RareGame
from rare.models.install import InstallDownloadModel, InstallQueueItemModel, InstallOptionsModel
from rare.shared import LegendaryCoreSingleton, ArgumentsSingleton
from rare.shared.workers.install_info import InstallInfoWorker
from rare.ui.components.dialogs.install_dialog import Ui_InstallDialog
from rare.ui.components.dialogs.install_dialog_advanced import Ui_InstallDialogAdvanced
from rare.utils import config_helper
from rare.utils.misc import format_size
from rare.widgets.collapsible_widget import CollapsibleFrame
from rare.widgets.indicator_edit import PathEdit, IndicatorReasonsCommon


class InstallDialogAdvanced(CollapsibleFrame):
    def __init__(self, parent=None):
        widget = QWidget()
        title = widget.tr("Advanced options")
        self.ui = Ui_InstallDialogAdvanced()
        self.ui.setupUi(widget)
        super(InstallDialogAdvanced, self).__init__(widget=widget, title=title, parent=parent)


class InstallDialog(QDialog):
    result_ready = pyqtSignal(InstallQueueItemModel)

    def __init__(self, rgame: RareGame, options: InstallOptionsModel, parent=None):
        super(InstallDialog, self).__init__(parent=parent)
        self.ui = Ui_InstallDialog()
        self.ui.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        # lk: set object names for CSS properties
        self.ui.install_button.setObjectName("InstallButton")

        self.core = LegendaryCoreSingleton()
        self.rgame = rgame
        self.options = options
        self.__download: Optional[InstallDownloadModel] = None

        self.advanced = InstallDialogAdvanced(parent=self)
        self.ui.advanced_layout.addWidget(self.advanced)

        self.selectable = CollapsibleFrame(widget=None, title=self.tr("Optional downloads"), parent=self)
        self.ui.selectable_layout.addWidget(self.selectable)

        self.options_changed = False
        self.worker_running = False
        self.reject_close = True

        self.threadpool = QThreadPool(self)
        self.threadpool.setMaxThreadCount(1)

        if options.repair_mode:
            header = self.tr("Repair")
            if options.repair_and_update:
                header = self.tr("Repair and update")
        elif options.update:
            header = self.tr("Update")
        else:
            header = self.tr("Install")
        self.ui.install_dialog_label.setText(f'<h3>{header} "{self.rgame.app_title}"</h3>')
        self.setWindowTitle(f'{header} "{self.rgame.app_title}" - {QCoreApplication.instance().applicationName()}')

        if not self.options.base_path:
            self.options.base_path = self.core.lgd.config.get(
                "Legendary", "install_dir", fallback=os.path.expanduser("~/legendary")
            )

        self.install_dir_edit = PathEdit(
            path=self.options.base_path,
            file_mode=QFileDialog.DirectoryOnly,
            edit_func=self.option_changed,
            save_func=self.save_install_edit,
            parent=self,
        )
        self.ui.install_dir_layout.addWidget(self.install_dir_edit)

        if self.options.update:
            self.ui.install_dir_label.setEnabled(False)
            self.install_dir_edit.setEnabled(False)
            self.ui.shortcut_label.setEnabled(False)
            self.ui.shortcut_check.setEnabled(False)
        else:
            self.ui.shortcut_check.setChecked(QSettings().value("create_shortcut", True, bool))

        self.error_box()

        platforms = ["Windows"]
        if self.rgame.is_win32:
            platforms.append("Win32")
        if self.rgame.is_mac:
            platforms.append("Mac")
        self.ui.platform_combo.addItems(platforms)
        self.ui.platform_combo.currentIndexChanged.connect(lambda: self.option_changed(None))
        self.ui.platform_combo.currentIndexChanged.connect(lambda: self.error_box())
        self.ui.platform_combo.currentIndexChanged.connect(
            lambda i: self.error_box(
                self.tr("Warning"),
                self.tr("You will not be able to run the game if you select <b>{}</b> as platform").format(
                    self.ui.platform_combo.itemText(i)
                ),
            )
            if (self.ui.platform_combo.currentText() == "Mac" and pf.system() != "Darwin")
            else None
        )
        if pf.system() == "Darwin" and "Mac" in platforms:
            self.ui.platform_combo.setCurrentIndex(platforms.index("Mac"))
        self.ui.platform_combo.currentTextChanged.connect(self.setup_sdl_list)

        self.advanced.ui.max_workers_spin.setValue(self.core.lgd.config.getint("Legendary", "max_workers", fallback=0))
        self.advanced.ui.max_workers_spin.valueChanged.connect(self.option_changed)

        self.advanced.ui.max_memory_spin.setValue(self.core.lgd.config.getint("Legendary", "max_memory", fallback=0))
        self.advanced.ui.max_memory_spin.valueChanged.connect(self.option_changed)

        self.advanced.ui.dl_optimizations_check.stateChanged.connect(self.option_changed)
        self.advanced.ui.force_download_check.stateChanged.connect(self.option_changed)
        self.advanced.ui.ignore_space_check.stateChanged.connect(self.option_changed)
        self.advanced.ui.download_only_check.stateChanged.connect(
            lambda: self.non_reload_option_changed("download_only")
        )
        self.ui.shortcut_check.stateChanged.connect(
            lambda: self.non_reload_option_changed("shortcut")
        )

        self.selectable_checks: List[TagCheckBox] = []
        self.config_tags: Optional[List[str]] = None
        self.setup_sdl_list("Mac" if pf.system() == "Darwin" and "Mac" in platforms else "Windows")

        self.ui.install_button.setEnabled(False)

        if self.options.overlay:
            self.ui.platform_label.setEnabled(False)
            self.ui.platform_combo.setEnabled(False)
            self.advanced.ui.ignore_space_label.setEnabled(False)
            self.advanced.ui.ignore_space_check.setEnabled(False)
            self.advanced.ui.download_only_label.setEnabled(False)
            self.advanced.ui.download_only_check.setEnabled(False)
            self.ui.shortcut_label.setEnabled(False)
            self.ui.shortcut_check.setEnabled(False)
            self.selectable.setEnabled(False)

        if pf.system() == "Darwin":
            self.ui.shortcut_check.setDisabled(True)
            self.ui.shortcut_check.setChecked(False)
            self.ui.shortcut_check.setToolTip(self.tr("Creating a shortcut is not supported on MacOS"))

        self.advanced.ui.install_prereqs_label.setEnabled(False)
        self.advanced.ui.install_prereqs_check.setEnabled(False)
        self.advanced.ui.install_prereqs_check.stateChanged.connect(
            lambda: self.non_reload_option_changed("install_prereqs")
        )

        self.non_reload_option_changed("shortcut")

        self.ui.cancel_button.clicked.connect(self.cancel_clicked)
        self.ui.verify_button.clicked.connect(self.verify_clicked)
        self.ui.install_button.clicked.connect(self.install_clicked)

        self.advanced.ui.install_prereqs_check.setChecked(self.options.install_prereqs)

        self.ui.install_dialog_layout.setSizeConstraint(QLayout.SetFixedSize)

    def execute(self):
        if self.options.silent:
            self.reject_close = False
            self.get_download_info()
        else:
            self.setModal(True)
            self.verify_clicked()
            self.show()

    @pyqtSlot(str)
    def setup_sdl_list(self, platform="Windows"):
        for cb in self.selectable_checks:
            cb.disconnect()
            cb.deleteLater()
        self.selectable_checks.clear()

        if config_tags := self.core.lgd.config.get(self.rgame.app_name, 'install_tags', fallback=None):
            self.config_tags = config_tags.split(",")
        config_disable_sdl = self.core.lgd.config.getboolean(self.rgame.app_name, 'disable_sdl', fallback=False)
        sdl_name = get_sdl_appname(self.rgame.app_name)
        if not config_disable_sdl and sdl_name is not None:
            # FIXME: this should be updated whenever platform changes
            sdl_data = self.core.get_sdl_data(sdl_name, platform=platform)
            if sdl_data:
                widget = QWidget(self.selectable)
                layout = QVBoxLayout(widget)
                layout.setSpacing(0)
                for tag, info in sdl_data.items():
                    cb = TagCheckBox(info["name"], info["tags"])
                    if tag == "__required":
                        cb.setChecked(True)
                        cb.setDisabled(True)
                    if self.config_tags is not None:
                        if all(elem in self.config_tags for elem in info["tags"]):
                            cb.setChecked(True)
                    layout.addWidget(cb)
                    self.selectable_checks.append(cb)
                for cb in self.selectable_checks:
                    cb.stateChanged.connect(self.option_changed)
                self.selectable.setWidget(widget)
        else:
            self.selectable.setDisabled(True)

    def get_options(self):
        self.options.base_path = self.install_dir_edit.text() if not self.options.update else None
        self.options.max_workers = self.advanced.ui.max_workers_spin.value()
        self.options.shared_memory = self.advanced.ui.max_memory_spin.value()
        self.options.order_opt = self.advanced.ui.dl_optimizations_check.isChecked()
        self.options.force = self.advanced.ui.force_download_check.isChecked()
        self.options.ignore_space = self.advanced.ui.ignore_space_check.isChecked()
        self.options.no_install = self.advanced.ui.download_only_check.isChecked()
        self.options.platform = self.ui.platform_combo.currentText()
        self.options.install_prereqs = self.advanced.ui.install_prereqs_check.isChecked()
        self.options.create_shortcut = self.ui.shortcut_check.isChecked()
        if self.selectable_checks:
            self.options.install_tag = [""]
            for cb in self.selectable_checks:
                if data := cb.isChecked():
                    # noinspection PyTypeChecker
                    self.options.install_tag.extend(data)

    def get_download_info(self):
        self.__download = None
        info_worker = InstallInfoWorker(self.core, self.options)
        info_worker.signals.result.connect(self.on_worker_result)
        info_worker.signals.failed.connect(self.on_worker_failed)
        info_worker.signals.finished.connect(self.on_worker_finished)
        self.worker_running = True
        self.threadpool.start(info_worker)

    def verify_clicked(self):
        self.error_box()
        message = self.tr("Updating...")
        self.ui.download_size_text.setText(message)
        self.ui.download_size_text.setStyleSheet("font-style: italic; font-weight: normal")
        self.ui.install_size_text.setText(message)
        self.ui.install_size_text.setStyleSheet("font-style: italic; font-weight: normal")
        self.ui.cancel_button.setEnabled(False)
        self.ui.verify_button.setEnabled(False)
        self.ui.install_button.setEnabled(False)
        self.options_changed = False
        self.get_options()
        self.get_download_info()

    def option_changed(self, path) -> Tuple[bool, str, int]:
        self.options_changed = True
        self.ui.install_button.setEnabled(False)
        self.ui.verify_button.setEnabled(not self.worker_running)
        return True, path, IndicatorReasonsCommon.VALID

    def save_install_edit(self, path: str):
        if not os.path.exists(path):
            return
        _, _, free_space = shutil.disk_usage(path)
        self.ui.avail_space.setText(format_size(free_space))

    def non_reload_option_changed(self, option: str):
        if option == "download_only":
            self.options.no_install = self.advanced.ui.download_only_check.isChecked()
        elif option == "shortcut":
            QSettings().setValue("create_shortcut", self.ui.shortcut_check.isChecked())
            self.options.create_shortcut = self.ui.shortcut_check.isChecked()
        elif option == "install_prereqs":
            self.options.install_prereqs = self.advanced.ui.install_prereqs_check.isChecked()

    def cancel_clicked(self):
        if self.config_tags is not None:
            config_helper.add_option(self.rgame.app_name, 'install_tags', ','.join(self.config_tags))
        else:
            # lk: this is purely for cleaning any install tags we might have added erroneously to the config
            config_helper.remove_option(self.rgame.app_name, 'install_tags')

        self.__download = None
        self.reject_close = False
        self.close()

    def install_clicked(self):
        self.reject_close = False
        self.close()

    @pyqtSlot(InstallDownloadModel)
    def on_worker_result(self, download: InstallDownloadModel):
        self.__download = download
        download_size = download.analysis.dl_size
        install_size = download.analysis.install_size
        # install_size = self.dl_item.download.analysis.disk_space_delta
        if download_size or (not download_size and (download.game.is_dlc or download.repair)):
            self.ui.download_size_text.setText(format_size(download_size))
            self.ui.download_size_text.setStyleSheet("font-style: normal; font-weight: bold")
            self.ui.install_button.setEnabled(not self.options_changed)
        else:
            self.ui.install_size_text.setText(self.tr("Game already installed"))
            self.ui.install_size_text.setStyleSheet("font-style: italics; font-weight: normal")
        self.ui.install_size_text.setText(format_size(install_size))
        self.ui.install_size_text.setStyleSheet("font-style: normal; font-weight: bold")
        self.ui.verify_button.setEnabled(self.options_changed)
        self.ui.cancel_button.setEnabled(True)
        if pf.system() == "Windows" or ArgumentsSingleton().debug:
            if download.igame.prereq_info and not download.igame.prereq_info.get("installed", False):
                self.advanced.ui.install_prereqs_check.setEnabled(True)
                self.advanced.ui.install_prereqs_label.setEnabled(True)
                self.advanced.ui.install_prereqs_check.setChecked(True)
                prereq_name = download.igame.prereq_info.get("name", "")
                prereq_path = os.path.split(download.igame.prereq_info.get("path", ""))[-1]
                prereq_desc = prereq_name if prereq_name else prereq_path
                self.advanced.ui.install_prereqs_check.setText(
                    self.tr("Also install: {}").format(prereq_desc)
                )
        if self.options.silent:
            self.close()

    def on_worker_failed(self, message: str):
        error_text = self.tr("Error")
        self.ui.download_size_text.setText(error_text)
        self.ui.install_size_text.setText(error_text)
        self.error_box(error_text, message)
        self.ui.verify_button.setEnabled(self.options_changed)
        self.ui.cancel_button.setEnabled(True)
        if self.options.silent:
            self.show()

    def error_box(self, label: str = "", message: str = ""):
        self.ui.warning_label.setVisible(bool(label))
        self.ui.warning_label.setText(label)
        self.ui.warning_text.setVisible(bool(message))
        self.ui.warning_text.setText(message)

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
            self.result_ready.emit(InstallQueueItemModel(options=self.options, download=self.__download))
            super(InstallDialog, self).closeEvent(a0)

    def keyPressEvent(self, e: QKeyEvent) -> None:
        if e.key() == Qt.Key_Escape:
            self.cancel_clicked()


class TagCheckBox(QCheckBox):
    def __init__(self, text, tags: List[str], parent=None):
        super(TagCheckBox, self).__init__(parent)
        self.setText(text)
        self.tags = tags

    def isChecked(self) -> Union[bool, List[str]]:
        return self.tags if super(TagCheckBox, self).isChecked() else False



