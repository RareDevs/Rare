import os
import platform as pf
import sys
from typing import Tuple, List, Union, Optional

from PyQt5.QtCore import Qt, QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot, QSettings
from PyQt5.QtGui import QCloseEvent, QKeyEvent
from PyQt5.QtWidgets import QDialog, QFileDialog, QCheckBox, QLayout, QWidget, QVBoxLayout, QApplication
from legendary.models.downloading import ConditionCheckResult
from legendary.models.game import Game
from legendary.utils.selective_dl import get_sdl_appname

from rare.lgndr.cli import LegendaryCLI
from rare.lgndr.core import LegendaryCore
from rare.lgndr.glue.arguments import LgndrInstallGameArgs
from rare.lgndr.glue.exception import LgndrException
from rare.lgndr.glue.monkeys import LgndrIndirectStatus
from rare.models.install import InstallDownloadModel, InstallQueueItemModel
from rare.shared import LegendaryCoreSingleton, ApiResultsSingleton, ArgumentsSingleton
from rare.ui.components.dialogs.install_dialog import Ui_InstallDialog
from rare.ui.components.dialogs.install_dialog_advanced import Ui_InstallDialogAdvanced
from rare.utils import config_helper
from rare.utils.extra_widgets import PathEdit
from rare.utils.misc import get_size
from rare.widgets.collapsible_widget import CollapsibleFrame


class InstallDialogAdvanced(CollapsibleFrame):
    def __init__(self, parent=None):
        widget = QWidget()
        title = widget.tr("Advanced Options")
        self.ui = Ui_InstallDialogAdvanced()
        self.ui.setupUi(widget)
        super(InstallDialogAdvanced, self).__init__(widget=widget, title=title, parent=parent)


class InstallDialog(QDialog):
    result_ready = pyqtSignal(InstallQueueItemModel)

    def __init__(self, dl_item: InstallQueueItemModel, update=False, repair=False, silent=False, parent=None):
        super(InstallDialog, self).__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.ui = Ui_InstallDialog()
        self.ui.setupUi(self)

        self.core = LegendaryCoreSingleton()
        self.api_results = ApiResultsSingleton()
        self.dl_item = dl_item
        self.app_name = self.dl_item.options.app_name
        self.game = (
            self.core.get_game(self.app_name)
            if not self.dl_item.options.overlay
            else Game(app_name=self.app_name, app_title="Epic Overlay")
        )

        self.advanced = InstallDialogAdvanced(parent=self)
        self.ui.advanced_layout.addWidget(self.advanced)

        self.selectable = CollapsibleFrame(widget=None, title=self.tr("Optional downloads"), parent=self)
        self.ui.selectable_layout.addWidget(self.selectable)

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
        self.ui.install_dialog_label.setText(f'<h3>{header} "{self.game.app_title}"</h3>')
        self.setWindowTitle(f'{QApplication.instance().applicationName()} - {header} "{self.game.app_title}"')

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
        self.ui.install_dir_layout.addWidget(self.install_dir_edit)

        if self.update:
            self.ui.install_dir_label.setEnabled(False)
            self.install_dir_edit.setEnabled(False)
            self.ui.shortcut_label.setEnabled(False)
            self.ui.shortcut_check.setEnabled(False)
        else:
            self.ui.shortcut_check.setChecked(QSettings().value("create_shortcut", True, bool))

        self.error_box()

        platforms = ["Windows"]
        if dl_item.options.app_name in self.api_results.bit32_games:
            platforms.append("Win32")
        if dl_item.options.app_name in self.api_results.mac_games:
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

        if self.dl_item.options.overlay:
            self.ui.platform_label.setVisible(False)
            self.ui.platform_combo.setVisible(False)
            self.advanced.ui.ignore_space_label.setVisible(False)
            self.advanced.ui.ignore_space_check.setVisible(False)
            self.advanced.ui.download_only_label.setVisible(False)
            self.advanced.ui.download_only_check.setVisible(False)
            self.ui.shortcut_label.setVisible(False)
            self.ui.shortcut_check.setVisible(False)
            self.selectable.setVisible(False)

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

        self.advanced.ui.install_prereqs_check.setChecked(self.dl_item.options.install_prereqs)

        self.ui.install_dialog_layout.setSizeConstraint(QLayout.SetFixedSize)

    def execute(self):
        if self.silent:
            self.reject_close = False
            self.get_download_info()
        else:
            self.verify_clicked()
            self.show()

    @pyqtSlot(str)
    def setup_sdl_list(self, platform="Windows"):
        for cb in self.selectable_checks:
            cb.disconnect()
            cb.deleteLater()
        self.selectable_checks.clear()

        if config_tags := self.core.lgd.config.get(self.game.app_name, 'install_tags', fallback=None):
            self.config_tags = config_tags.split(",")
        config_disable_sdl = self.core.lgd.config.getboolean(self.game.app_name, 'disable_sdl', fallback=False)
        sdl_name = get_sdl_appname(self.game.app_name)
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
        self.dl_item.options.base_path = self.install_dir_edit.text() if not self.update else None

        self.dl_item.options.max_workers = self.advanced.ui.max_workers_spin.value()
        self.dl_item.options.shared_memory = self.advanced.ui.max_memory_spin.value()
        self.dl_item.options.order_opt = self.advanced.ui.dl_optimizations_check.isChecked()
        self.dl_item.options.force = self.advanced.ui.force_download_check.isChecked()
        self.dl_item.options.ignore_space = self.advanced.ui.ignore_space_check.isChecked()
        self.dl_item.options.no_install = self.advanced.ui.download_only_check.isChecked()
        self.dl_item.options.platform = self.ui.platform_combo.currentText()
        self.dl_item.options.install_prereqs = self.advanced.ui.install_prereqs_check.isChecked()
        self.dl_item.options.create_shortcut = self.ui.shortcut_check.isChecked()
        if self.selectable_checks:
            self.dl_item.options.install_tag = [""]
            for cb in self.selectable_checks:
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

    def option_changed(self, path) -> Tuple[bool, str, str]:
        self.options_changed = True
        self.ui.install_button.setEnabled(False)
        self.ui.verify_button.setEnabled(not self.worker_running)
        return True, path, ""

    def non_reload_option_changed(self, option: str):
        if option == "download_only":
            self.dl_item.options.no_install = self.advanced.ui.download_only_check.isChecked()
        elif option == "shortcut":
            QSettings().setValue("create_shortcut", self.ui.shortcut_check.isChecked())
            self.dl_item.options.create_shortcut = self.ui.shortcut_check.isChecked()
        elif option == "install_prereqs":
            self.dl_item.options.install_prereqs = self.advanced.ui.install_prereqs_check.isChecked()

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
            self.ui.download_size_text.setText("{}".format(get_size(download_size)))
            self.ui.download_size_text.setStyleSheet("font-style: normal; font-weight: bold")
            self.ui.install_button.setEnabled(not self.options_changed)
        else:
            self.ui.install_size_text.setText(self.tr("Game already installed"))
            self.ui.install_size_text.setStyleSheet("font-style: italics; font-weight: normal")
        self.ui.install_size_text.setText("{}".format(get_size(install_size)))
        self.ui.install_size_text.setStyleSheet("font-style: normal; font-weight: bold")
        self.ui.verify_button.setEnabled(self.options_changed)
        self.ui.cancel_button.setEnabled(True)
        if pf.system() == "Windows" or ArgumentsSingleton().debug:
            if dl_item.igame.prereq_info and not dl_item.igame.prereq_info.get("installed", False):
                self.advanced.ui.install_prereqs_check.setEnabled(True)
                self.advanced.ui.install_prereqs_label.setEnabled(True)
                self.advanced.ui.install_prereqs_check.setChecked(True)
                prereq_name = dl_item.igame.prereq_info.get("name", "")
                prereq_path = os.path.split(dl_item.igame.prereq_info.get("path", ""))[-1]
                prereq_desc = prereq_name if prereq_name else prereq_path
                self.advanced.ui.install_prereqs_check.setText(
                    self.tr("Also install: {}").format(prereq_desc)
                )
        if self.silent:
            self.close()

    def on_worker_failed(self, message: str):
        error_text = self.tr("Error")
        self.ui.download_size_text.setText(error_text)
        self.ui.install_size_text.setText(error_text)
        self.error_box(error_text, message)
        self.ui.verify_button.setEnabled(self.options_changed)
        self.ui.cancel_button.setEnabled(True)
        if self.silent:
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
            self.result_ready.emit(self.dl_item)
            super(InstallDialog, self).closeEvent(a0)

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
                cli = LegendaryCLI(self.core)
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
                    dlm=dlm,
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
        return self.tags if super(TagCheckBox, self).isChecked() else False
