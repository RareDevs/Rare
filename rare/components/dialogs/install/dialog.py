import os
import platform as pf
import shutil
from typing import Optional, Tuple, Union

from PySide6.QtCore import Qt, QThreadPool, Signal, Slot
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QFileDialog, QFormLayout, QLabel, QWidget

from rare.models.game import RareGame
from rare.models.install import (
    InstallDownloadModel,
    InstallOptionsModel,
    InstallQueueItemModel,
)
from rare.models.settings import RareAppSettings, app_settings
from rare.shared.workers import InstallInfoWorker
from rare.ui.components.dialogs.install.dialog import Ui_InstallDialog
from rare.utils.misc import format_size, qta_icon
from rare.widgets.dialogs import ActionDialog, game_title
from rare.widgets.indicator_edit import IndicatorReasonsCommon, PathEdit

from .advanced import InstallDialogAdvanced
from .selective import InstallDialogSelective


class InstallDialog(ActionDialog):
    result_ready = Signal(InstallQueueItemModel)

    def __init__(self, settings: RareAppSettings, rgame: "RareGame", options: InstallOptionsModel, parent=None):
        super(InstallDialog, self).__init__(parent=parent)
        self.settings = settings

        header = self.tr("Install")
        bicon = qta_icon("ri.install-line")
        if options.repair_mode:
            header = self.tr("Repair")
            bicon = qta_icon("fa.wrench", "mdi.progress-wrench")
            if options.repair_and_update:
                header = self.tr("Repair and update")
        elif options.update:
            header = self.tr("Update")
        elif options.reset_sdl:
            header = self.tr("Modify")
            bicon = qta_icon("fa.gear", "mdi.content-save-edit-outline")
        self.setWindowTitle(game_title(header, rgame.app_title))
        self.setSubtitle(game_title(header, rgame.app_title))

        install_widget = QWidget(self)
        self.ui = Ui_InstallDialog()
        self.ui.setupUi(install_widget)

        self.core = rgame.core
        self.rgame = rgame
        self.__options: InstallOptionsModel = options
        self.__download: Optional[InstallDownloadModel] = None
        self.__queue_item: Optional[InstallQueueItemModel] = None

        self.selectable = InstallDialogSelective(rgame, parent=self)
        self.selectable.stateChanged.connect(self._on_option_changed)
        self.ui.main_layout.insertRow(
            self.ui.main_layout.getWidgetPosition(self.ui.shortcut_label)[0] + 1,
            # self.tr("Optional"),
            self.selectable,
        )

        self.advanced = InstallDialogAdvanced(parent=self)
        self.ui.main_layout.insertRow(
            self.ui.main_layout.getWidgetPosition(self.ui.shortcut_label)[0] + 2,
            # self.tr("Advanced"),
            self.advanced,
        )

        # self.file_filters = InstallDialogFileFilters(parent=self)
        # self.ui.main_layout.insertRow(
        #     self.ui.main_layout.getWidgetPosition(self.ui.shortcut_label)[0] + 3,
        #     # self.tr("Filters"),
        #     self.file_filters,
        # )

        self.options_changed = False

        self.threadpool = QThreadPool(self)
        self.threadpool.setMaxThreadCount(1)

        self.install_dir_edit = PathEdit(
            path=options.base_path,
            file_mode=QFileDialog.FileMode.Directory,
            edit_func=self.__install_dir_edit_callback,
            save_func=self.__install_dir_save_callback,
            parent=self,
        )
        self.install_dir_edit.validationFinished.connect(self.__on_install_dir_validation)
        self.ui.main_layout.setWidget(
            self.ui.main_layout.getWidgetPosition(self.ui.install_dir_label)[0],
            QFormLayout.ItemRole.FieldRole,
            self.install_dir_edit,
        )

        self.install_dir_edit.setDisabled(rgame.is_installed or rgame.is_dlc)
        self.ui.install_dir_label.setDisabled(rgame.is_installed or rgame.is_dlc)
        self.ui.shortcut_label.setDisabled(rgame.is_installed or rgame.is_dlc)
        self.ui.shortcut_check.setDisabled(rgame.is_installed or rgame.is_dlc)
        self.ui.shortcut_check.setChecked(not rgame.is_installed and self.settings.get_value(app_settings.create_shortcut))
        self.ui.shortcut_check.checkStateChanged.connect(self._on_option_changed_no_reload)

        self.set_error_labels()

        self.ui.platform_combo.addItems(reversed(rgame.platforms))
        self.ui.platform_combo.setCurrentIndex(self.ui.platform_combo.findText(options.platform))
        self.ui.platform_combo.currentIndexChanged.connect(self._on_option_changed)
        self.ui.platform_combo.currentIndexChanged.connect(self.check_incompatible_platform)
        self.ui.platform_combo.currentIndexChanged.connect(self.reset_install_dir)
        self.ui.platform_combo.currentTextChanged.connect(self.selectable.update_list)

        self.ui.platform_label.setDisabled(rgame.is_installed or rgame.is_dlc)
        self.ui.platform_combo.setDisabled(rgame.is_installed or rgame.is_dlc)

        # if we are repairing, disable the SDL selection and open the dialog frame to be visible
        self.selectable.setDisabled(options.repair_mode and not options.repair_and_update)
        if options.repair_mode and not options.repair_and_update:
            self.selectable.click()

        self.advanced.ui.max_workers_spin.setValue(self.core.lgd.config.getint("Legendary", "max_workers", fallback=0))
        self.advanced.ui.max_workers_spin.valueChanged.connect(self._on_option_changed)

        self.advanced.ui.max_memory_spin.setValue(self.core.lgd.config.getint("Legendary", "max_memory", fallback=0))
        self.advanced.ui.max_memory_spin.valueChanged.connect(self._on_option_changed)

        self.advanced.ui.read_files_check.setChecked(options.read_files)
        self.advanced.ui.read_files_check.checkStateChanged.connect(self._on_option_changed)

        self.advanced.ui.use_signed_urls_check.setChecked(options.always_use_signed_urls)
        self.advanced.ui.use_signed_urls_check.checkStateChanged.connect(self._on_option_changed)

        self.advanced.ui.dl_optimizations_check.setChecked(options.order_opt)
        self.advanced.ui.dl_optimizations_check.checkStateChanged.connect(self._on_option_changed)

        self.advanced.ui.force_download_check.setChecked(options.force)
        self.advanced.ui.force_download_check.checkStateChanged.connect(self._on_option_changed)

        self.advanced.ui.ignore_space_check.setChecked(options.ignore_space)
        self.advanced.ui.ignore_space_check.checkStateChanged.connect(self._on_option_changed)

        self.advanced.ui.download_only_check.setChecked(options.no_install)
        self.advanced.ui.download_only_check.checkStateChanged.connect(self._on_option_changed_no_reload)

        self.reset_install_dir(self.ui.platform_combo.currentIndex())
        self.selectable.update_list(self.ui.platform_combo.currentText())
        self.check_incompatible_platform(self.ui.platform_combo.currentIndex())

        self.accept_button.setEnabled(False)

        if self.__options.overlay:
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
            self.ui.shortcut_label.setDisabled(True)
            self.ui.shortcut_check.setDisabled(True)
            self.ui.shortcut_check.setChecked(False)
            self.ui.shortcut_check.setToolTip(self.tr("Creating a shortcut is not supported on macOS"))

        self.advanced.ui.install_prereqs_label.setEnabled(False)
        self.advanced.ui.install_prereqs_check.setEnabled(False)
        self.advanced.ui.install_prereqs_check.checkStateChanged.connect(self._on_option_changed_no_reload)
        self.advanced.ui.install_prereqs_check.setChecked(self.__options.install_prereqs)

        # lk: set object names for CSS properties
        self.accept_button.setText(header)
        self.accept_button.setIcon(bicon)
        self.accept_button.setObjectName("InstallButton")

        self.action_button.setText(self.tr("Validate"))
        self.action_button.setIcon(qta_icon("fa.check", "fa5s.check"))

        self.setCentralWidget(install_widget)

    def showEvent(self, a0: QShowEvent) -> None:
        if a0.spontaneous():
            return super().showEvent(a0)
        self.install_dir_edit.refresh()
        return super().showEvent(a0)

    def execute(self):
        if self.__options.silent:
            self.get_download_info()
        else:
            self.action_handler()
            self.open()

    @Slot(int)
    def reset_install_dir(self, index: int):
        if not self.rgame.is_installed and not self.rgame.is_dlc:
            platform = self.ui.platform_combo.itemText(index)
            default_dir = self.core.get_default_install_dir(platform)
            self.install_dir_edit.setText(default_dir)

    @Slot(int)
    def check_incompatible_platform(self, index: int):
        platform = self.ui.platform_combo.itemText(index)
        if platform == "Mac" and pf.system() != "Darwin":
            self.set_error_labels(
                self.tr("Warning"),
                self.tr("You will not be able to run the game if you select <b>{}</b> as platform").format(platform),
            )
        else:
            self.set_error_labels()

    def get_options(self):
        base_path = os.path.join(self.install_dir_edit.text(), ".overlay" if self.__options.overlay else "")
        # TODO: investigate if this check is needed
        if self.rgame.is_installed or self.rgame.is_dlc:
            self.__options.base_path = ""
        else:
            self.__options.base_path = base_path
        self.__options.platform = self.ui.platform_combo.currentText()
        self.__options.create_shortcut = self.ui.shortcut_check.isChecked()
        self.__options.max_workers = self.advanced.ui.max_workers_spin.value()
        self.__options.shared_memory = self.advanced.ui.max_memory_spin.value()
        self.__options.read_files = self.advanced.ui.read_files_check.isChecked()
        self.__options.always_use_signed_urls = self.advanced.ui.use_signed_urls_check.isChecked()
        self.__options.order_opt = self.advanced.ui.dl_optimizations_check.isChecked()
        self.__options.force = self.advanced.ui.force_download_check.isChecked()
        self.__options.ignore_space = self.advanced.ui.ignore_space_check.isChecked()
        self.__options.no_install = self.advanced.ui.download_only_check.isChecked()
        self.__options.install_prereqs = self.advanced.ui.install_prereqs_check.isChecked()
        self.__options.install_tag = self.selectable.enabled_tags()
        self.__options.reset_sdl = True

    def get_download_info(self):
        self.__download = None
        info_worker = InstallInfoWorker(self.core, self.__options)
        info_worker.signals.result.connect(self.__on_worker_result)
        info_worker.signals.failed.connect(self.__on_worker_failed)
        self.threadpool.start(info_worker)

    def action_handler(self):
        self.set_error_labels()
        message = self.tr("Updating...")
        self.set_size_labels(message, message)
        self.setActive(True)
        self.options_changed = False
        self.get_options()
        self.get_download_info()

    @Slot()
    def _on_option_changed(self):
        self.options_changed = True
        self.accept_button.setEnabled(False)
        self.action_button.setEnabled(not self.active())

    @Slot(Qt.CheckState)
    def _on_option_changed_no_reload(self, state: Qt.CheckState):
        if self.sender() is self.advanced.ui.download_only_check:
            self.__options.no_install = state != Qt.CheckState.Unchecked
        elif self.sender() is self.ui.shortcut_check:
            self.settings.set_value(app_settings.create_shortcut, state != Qt.CheckState.Unchecked)
            self.__options.create_shortcut = state != Qt.CheckState.Unchecked
        elif self.sender() is self.advanced.ui.install_prereqs_check:
            self.__options.install_prereqs = state != Qt.CheckState.Unchecked

    @staticmethod
    def __install_dir_edit_callback(path: str) -> Tuple[bool, str, int]:
        if not path:
            return False, path, IndicatorReasonsCommon.IS_EMPTY
        try:
            perms_path = os.path.join(path, ".rare_perms")
            open(perms_path, "w").close()
            os.unlink(perms_path)
        except PermissionError:
            return False, path, IndicatorReasonsCommon.PERM_NO_WRITE
        except FileNotFoundError:
            return False, path, IndicatorReasonsCommon.DIR_NOT_EXISTS
        return True, path, IndicatorReasonsCommon.VALID

    def __install_dir_save_callback(self, path: str):
        if not os.path.exists(path):
            return
        _, _, free_space = shutil.disk_usage(path)
        self.ui.available_space_text.setText(format_size(free_space))

    @Slot(bool, str)
    def __on_install_dir_validation(self, is_valid: bool, reason: str):
        self.accept_button.setEnabled(False)
        self.action_button.setEnabled(is_valid and not self.active())
        if not is_valid:
            self.set_error_labels(self.tr("Error"), reason)
        else:
            self.set_error_labels()

    @staticmethod
    def same_platform(download: InstallDownloadModel) -> bool:
        platform = download.igame.platform
        if pf.system() == "Windows":
            return platform in {"Windows", "Win32"}
        elif pf.system() == "Darwin":
            return platform == "Mac"
        else:
            return False

    @Slot(InstallDownloadModel)
    def __on_worker_result(self, download: InstallDownloadModel):
        self.setActive(False)
        self.__download = download
        download_size = download.analysis.dl_size
        install_size = download.analysis.install_size
        # install_size = self.dl_item.download.analysis.disk_space_delta
        self.set_size_labels(download_size, install_size)
        if download_size or (not download_size and (download.game.is_dlc or download.repair)):
            self.accept_button.setEnabled(not self.options_changed)
        self.action_button.setEnabled(self.options_changed)
        has_prereqs = bool(download.igame.prereq_info) and not download.igame.prereq_info.get("installed", False)
        if has_prereqs:
            prereq_name = download.igame.prereq_info.get("name", "")
            prereq_path = os.path.split(download.igame.prereq_info.get("path", ""))[-1]
            prereq_desc = prereq_name if prereq_name else prereq_path
            self.advanced.ui.install_prereqs_check.setText(self.tr("Also install: {}").format(prereq_desc))
        else:
            self.advanced.ui.install_prereqs_check.setText("")
        # Offer to install prerequisites only on same platforms
        self.advanced.ui.install_prereqs_label.setEnabled(has_prereqs)
        self.advanced.ui.install_prereqs_check.setEnabled(has_prereqs)
        self.advanced.ui.install_prereqs_check.setChecked(has_prereqs and self.same_platform(download))

        # new_manifest_data, _, _ = self.core.get_cdn_manifest(download.game, download.igame.platform, self.__options.disable_https)
        # new_manifest = self.core.load_manifest(new_manifest_data)
        # self.file_filters.clear()
        # for e in new_manifest.file_manifest_list.elements:
        #     self.file_filters.add_item(e.filename.lower())

        if self.__options.silent:
            self.accept()

    @Slot(str)
    def __on_worker_failed(self, message: str):
        self.setActive(False)
        error_text = self.tr("Error")
        self.set_size_labels(error_text, error_text)
        self.set_error_labels(error_text, message)
        self.action_button.setEnabled(self.options_changed)
        self.accept_button.setEnabled(False)
        if self.__options.silent:
            self.open()

    @staticmethod
    def __set_size_label(label: QLabel, value: Union[int, float, str]):
        is_numeric = isinstance(value, (int, float))
        font = label.font()
        font.setBold(is_numeric)
        font.setItalic(not is_numeric)
        label.setFont(font)
        text = format_size(value) if is_numeric else value
        label.setText(text)

    def set_size_labels(self, download: Union[int, float, str], install: Union[int, float, str]):
        self.__set_size_label(self.ui.download_size_text, download)
        self.__set_size_label(self.ui.install_size_text, install)

    def set_error_labels(self, label: str = "", message: str = ""):
        self.ui.warning_label.setVisible(bool(label))
        self.ui.warning_label.setText(label)
        self.ui.warning_text.setVisible(bool(message))
        self.ui.warning_text.setText(message)

    def done_handler(self):
        self.threadpool.clear()
        self.threadpool.waitForDone()
        self.result_ready.emit(self.__queue_item)

    # lk: __download is already set at this point so just do nothing.
    def accept_handler(self):
        self.__queue_item = InstallQueueItemModel(options=self.__options, download=self.__download)

    def reject_handler(self):
        self.__queue_item = InstallQueueItemModel(options=self.__options, download=None)
