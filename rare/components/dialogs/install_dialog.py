import os
import platform as pf
import sys
from typing import Tuple, List, Union, Optional

from PyQt5.QtCore import Qt, QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QCloseEvent, QKeyEvent
from PyQt5.QtWidgets import QDialog, QFileDialog, QCheckBox
from legendary.models.downloading import ConditionCheckResult
from legendary.models.game import Game
from legendary.utils.selective_dl import get_sdl_appname

from rare.lgndr.api_arguments import LgndrInstallGameArgs
from rare.lgndr.api_exception import LgndrException
from rare.lgndr.api_monkeys import LgndrIndirectStatus
from rare.lgndr.core import LegendaryCore
from rare.shared import LegendaryCLISingleton, LegendaryCoreSingleton, ApiResultsSingleton, ArgumentsSingleton
from rare.ui.components.dialogs.install_dialog import Ui_InstallDialog
from rare.utils.extra_widgets import PathEdit
from rare.models.install import InstallDownloadModel, InstallQueueItemModel
from rare.utils.misc import get_size
from rare.utils import config_helper


class InstallDialog(QDialog, Ui_InstallDialog):
    result_ready = pyqtSignal(InstallQueueItemModel)

    def __init__(self, dl_item: InstallQueueItemModel, update=False, repair=False, silent=False, parent=None):
        super(InstallDialog, self).__init__(parent)
        self.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)

        self.core = LegendaryCoreSingleton()
        self.api_results = ApiResultsSingleton()
        self.dl_item = dl_item
        self.app_name = self.dl_item.options.app_name
        self.game = (
            self.core.get_game(self.app_name)
            if not self.dl_item.options.overlay
            else Game(app_name=self.app_name, app_title="Epic Overlay")
        )

        self.game_path = self.game.metadata.get("customAttributes", {}).get("FolderName", {}).get("value", "")

        self.update = update
        self.repair = repair
        self.silent = silent

        self.options_changed = False
        self.worker_running = False
        self.reject_close = True

        self.threadpool = QThreadPool(self)
        self.threadpool.setMaxThreadCount(1)

        header = self.tr("Update") if update else self.tr("Install")
        self.install_dialog_label.setText(f'<h3>{header} "{self.game.app_title}"</h3>')
        self.setWindowTitle(f'{self.windowTitle()} - {header} "{self.game.app_title}"')

        if not self.dl_item.options.base_path:
            self.dl_item.options.base_path = self.core.lgd.config.get(
                "Legendary", "install_dir", fallback=os.path.expanduser("~/legendary")
            )

        self.install_dir_edit = PathEdit(
            path=self.dl_item.options.base_path,
            file_type=QFileDialog.DirectoryOnly,
            edit_func=self.option_changed,
            parent=self,
        )
        self.install_dir_layout.addWidget(self.install_dir_edit)

        if self.update:
            self.install_dir_label.setVisible(False)
            self.install_dir_edit.setVisible(False)
            self.shortcut_lbl.setVisible(False)
            self.shortcut_cb.setVisible(False)
            self.shortcut_cb.setChecked(False)

        self.error_box()

        platforms = ["Windows"]
        if dl_item.options.app_name in self.api_results.bit32_games:
            platforms.append("Win32")
        if dl_item.options.app_name in self.api_results.mac_games:
            platforms.append("Mac")
        self.platform_combo_box.addItems(platforms)
        self.platform_combo_box.currentIndexChanged.connect(lambda: self.option_changed(None))
        self.platform_combo_box.currentIndexChanged.connect(lambda: self.error_box())
        self.platform_combo_box.currentIndexChanged.connect(
            lambda i: self.error_box(
                self.tr("Warning"),
                self.tr("You will not be able to run the game if you select <b>{}</b> as platform").format(
                    self.platform_combo_box.itemText(i)
                ),
            )
            if (self.platform_combo_box.currentText() == "Mac" and pf.system() != "Darwin")
            else None
        )
        self.platform_combo_box.currentTextChanged.connect(self.setup_sdl_list)

        if pf.system() == "Darwin" and "Mac" in platforms:
            self.platform_combo_box.setCurrentIndex(platforms.index("Mac"))

        self.max_workers_spin.setValue(self.core.lgd.config.getint("Legendary", "max_workers", fallback=0))
        self.max_workers_spin.valueChanged.connect(self.option_changed)

        self.max_memory_spin.setValue(self.core.lgd.config.getint("Legendary", "max_memory", fallback=0))
        self.max_memory_spin.valueChanged.connect(self.option_changed)

        self.dl_optimizations_check.stateChanged.connect(self.option_changed)
        self.force_download_check.stateChanged.connect(self.option_changed)
        self.ignore_space_check.stateChanged.connect(self.option_changed)
        self.download_only_check.stateChanged.connect(lambda: self.non_reload_option_changed("download_only"))
        self.shortcut_cb.stateChanged.connect(lambda: self.non_reload_option_changed("shortcut"))

        self.sdl_list_cbs: List[TagCheckBox] = []
        self.config_tags: Optional[List[str]] = None
        self.setup_sdl_list("Mac" if pf.system() == "Darwin" and "Mac" in platforms else "Windows")

        self.install_button.setEnabled(False)

        if self.dl_item.options.overlay:
            self.platform_label.setVisible(False)
            self.platform_combo_box.setVisible(False)
            self.ignore_space_check.setVisible(False)
            self.ignore_space_label.setVisible(False)
            self.download_only_check.setVisible(False)
            self.download_only_label.setVisible(False)
            self.shortcut_cb.setVisible(False)
            self.shortcut_lbl.setVisible(False)

        if pf.system() == "Darwin":
            self.shortcut_cb.setDisabled(True)
            self.shortcut_cb.setChecked(False)
            self.shortcut_cb.setToolTip(self.tr("Creating a shortcut is not supported on MacOS"))

        self.install_preqs_lbl.setVisible(False)
        self.install_preqs_check.setVisible(False)
        self.install_preqs_check.stateChanged.connect(lambda: self.non_reload_option_changed("install_preqs"))

        self.non_reload_option_changed("shortcut")

        self.cancel_button.clicked.connect(self.cancel_clicked)
        self.verify_button.clicked.connect(self.verify_clicked)
        self.install_button.clicked.connect(self.install_clicked)

        self.install_dialog_layout.setSizeConstraint(self.install_dialog_layout.SetFixedSize)

    def execute(self):
        if self.silent:
            self.reject_close = False
            self.get_download_info()
        else:
            self.verify_clicked()
            self.show()

    @pyqtSlot(str)
    def setup_sdl_list(self, platform="Windows"):
        for cb in self.sdl_list_cbs:
            cb.disconnect()
            cb.deleteLater()
        self.sdl_list_cbs.clear()

        if config_tags := self.core.lgd.config.get(self.game.app_name, 'install_tags', fallback=None):
            self.config_tags = config_tags.split(",")
        config_disable_sdl = self.core.lgd.config.getboolean(self.game.app_name, 'disable_sdl', fallback=False)
        sdl_name = get_sdl_appname(self.game.app_name)
        if not config_disable_sdl and sdl_name is not None:
            # FIXME: this should be updated whenever platform changes
            sdl_data = self.core.get_sdl_data(sdl_name, platform=platform)
            if sdl_data:
                for tag, info in sdl_data.items():
                    cb = TagCheckBox(info["name"], info["tags"])
                    if tag == "__required":
                        cb.setChecked(True)
                        cb.setDisabled(True)
                    if all(elem in self.config_tags for elem in info["tags"]):
                        cb.setChecked(True)
                    self.sdl_list_layout.addWidget(cb)
                    self.sdl_list_cbs.append(cb)
                self.sdl_list_frame.resize(self.sdl_list_frame.minimumSize())
                for cb in self.sdl_list_cbs:
                    cb.stateChanged.connect(self.option_changed)
        else:
            self.sdl_list_frame.setVisible(False)
            self.sdl_list_label.setVisible(False)

    def get_options(self):
        self.dl_item.options.base_path = self.install_dir_edit.text() if not self.update else None

        self.dl_item.options.max_workers = self.max_workers_spin.value()
        self.dl_item.options.shared_memory = self.max_memory_spin.value()
        self.dl_item.options.order_opt = self.dl_optimizations_check.isChecked()
        self.dl_item.options.force = self.force_download_check.isChecked()
        self.dl_item.options.ignore_space = self.ignore_space_check.isChecked()
        self.dl_item.options.no_install = self.download_only_check.isChecked()
        self.dl_item.options.platform = self.platform_combo_box.currentText()
        if self.sdl_list_cbs:
            self.dl_item.options.install_tag = [""]
            for cb in self.sdl_list_cbs:
                if data := cb.isChecked():
                    # noinspection PyTypeChecker
                    self.dl_item.options.install_tag.extend(data)

    def get_download_info(self):
        self.dl_item.download = None
        info_worker = InstallInfoWorker(self.core, self.dl_item, self.game)
        info_worker.setAutoDelete(True)
        info_worker.signals.result.connect(self.on_worker_result)
        info_worker.signals.failed.connect(self.on_worker_failed)
        info_worker.signals.finished.connect(self.on_worker_finished)
        self.worker_running = True
        self.threadpool.start(info_worker)

    def verify_clicked(self):
        self.error_box()
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

    def option_changed(self, path) -> Tuple[bool, str, str]:
        self.options_changed = True
        self.install_button.setEnabled(False)
        self.verify_button.setEnabled(not self.worker_running)
        return True, path, ""

    def non_reload_option_changed(self, option: str):
        if option == "download_only":
            self.dl_item.options.no_install = self.download_only_check.isChecked()
        elif option == "shortcut":
            self.dl_item.options.create_shortcut = self.shortcut_cb.isChecked()
        elif option == "install_preqs":
            self.dl_item.options.install_preqs = self.install_preqs_check.isChecked()

    def cancel_clicked(self):
        if self.config_tags:
            config_helper.add_option(self.game.app_name, 'install_tags', ','.join(self.config_tags))
        else:
            # lk: this is purely for cleaning any install tags we might have added erroneously to the config
            config_helper.remove_option(self.game.app_name, 'install_tags')

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
        if pf.system() == "Windows" or ArgumentsSingleton().debug:
            if dl_item.igame.prereq_info and not dl_item.igame.prereq_info.get("installed", False):
                self.install_preqs_check.setVisible(True)
                self.install_preqs_lbl.setVisible(True)
                self.install_preqs_check.setText(
                    self.tr("Also install: {}").format(dl_item.igame.prereq_info.get("name", ""))
                )

    def on_worker_failed(self, message: str):
        error_text = self.tr("Error")
        self.download_size_info_label.setText(error_text)
        self.install_size_info_label.setText(error_text)
        self.error_box(error_text, message)
        self.verify_button.setEnabled(self.options_changed)
        self.cancel_button.setEnabled(True)
        if self.silent:
            self.close()

    def error_box(self, label: str = "", message: str = ""):
        self.warn_label.setVisible(bool(label))
        self.warn_label.setText(label)
        self.warn_message.setVisible(bool(message))
        self.warn_message.setText(message)

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

    def keyPressEvent(self, e: QKeyEvent) -> None:
        if e.key() == Qt.Key_Escape:
            self.cancel_clicked()


class InstallInfoWorker(QRunnable):
    class Signals(QObject):
        result = pyqtSignal(InstallDownloadModel)
        failed = pyqtSignal(str)
        finished = pyqtSignal()

    def __init__(self, core: LegendaryCore, dl_item: InstallQueueItemModel, game: Game = None):
        sys.excepthook = sys.__excepthook__
        super(InstallInfoWorker, self).__init__()
        self.signals = InstallInfoWorker.Signals()
        self.core = core
        self.dl_item = dl_item
        self.game = game

    @pyqtSlot()
    def run(self):
        try:
            if not self.dl_item.options.overlay:
                cli = LegendaryCLISingleton()
                status = LgndrIndirectStatus()
                result = cli.install_game(
                    LgndrInstallGameArgs(**self.dl_item.options.as_install_kwargs(), indirect_status=status)
                )
                if result:
                    download = InstallDownloadModel(*result)
                else:
                    raise LgndrException(status.message)
            else:
                if not os.path.exists(path := self.dl_item.options.base_path):
                    os.makedirs(path)

                dlm, analysis, igame = self.core.prepare_overlay_install(
                    path=self.dl_item.options.base_path
                )

                download = InstallDownloadModel(
                    dlmanager=dlm,
                    analysis=analysis,
                    igame=igame,
                    game=self.game,
                    repair=False,
                    repair_file="",
                    res=ConditionCheckResult(),  # empty
                )

            if not download.res or not download.res.failures:
                self.signals.result.emit(download)
            else:
                self.signals.failed.emit("\n".join(str(i) for i in download.res.failures))
        except LgndrException as ret:
            self.signals.failed.emit(ret.message)
        except Exception as e:
            self.signals.failed.emit(str(e))
        self.signals.finished.emit()


class TagCheckBox(QCheckBox):
    def __init__(self, text, tags: List[str], parent=None):
        super(TagCheckBox, self).__init__(parent)
        self.setText(text)
        self.tags = tags

    def isChecked(self) -> Union[bool, List[str]]:
        if super(TagCheckBox, self).isChecked():
            return self.tags
        else:
            return False
