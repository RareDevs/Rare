import os
import platform as pf
import re
from logging import getLogger
from typing import Set, Tuple

from PySide6.QtCore import QObject, Qt, QThreadPool, Signal, Slot
from PySide6.QtGui import QHideEvent, QShowEvent
from PySide6.QtWidgets import QFileDialog, QMessageBox, QSizePolicy, QWidget

from rare.lgndr.core import LegendaryCore
from rare.models.settings import RareAppSettings, app_settings
from rare.shared import RareCore
from rare.shared.workers.worker import Worker
from rare.ui.components.tabs.settings.legendary import Ui_LegendarySettings
from rare.utils.misc import format_size
from rare.widgets.indicator_edit import (
    IndicatorLineEdit,
    IndicatorReasonsCommon,
    PathEdit,
)

logger = getLogger("LegendarySettings")


class RefreshGameMetaWorkerSignals(QObject):
    finished = Signal()


class RefreshGameMetaWorker(Worker):

    def __init__(self, core: LegendaryCore, platforms: Set[str], include_unreal: bool):
        super(RefreshGameMetaWorker, self).__init__()
        self.core = core
        self.signals = RefreshGameMetaWorkerSignals()
        self.platforms = platforms if platforms else {"Windows"}
        self.skip_ue = not include_unreal

    def run_real(self) -> None:
        for platform in self.platforms:
            self.core.get_game_and_dlc_list(True, platform=platform, force_refresh=True, skip_ue=self.skip_ue)
        self.signals.finished.emit()


class LegendarySettings(QWidget):
    def __init__(self, settings: RareAppSettings, rcore: RareCore, parent=None):
        super(LegendarySettings, self).__init__(parent=parent)
        self.ui = Ui_LegendarySettings()
        self.ui.setupUi(self)

        self.settings = settings
        self.rcore = rcore
        self.core = rcore.core()

        # Platform specific installation directory for macOS games
        if pf.system() == "Darwin":
            self.mac_install_dir_edit = PathEdit(
                path=self.core.get_default_install_dir("Mac"),
                placeholder=self.tr("Default installation folder for macOS games"),
                file_mode=QFileDialog.FileMode.Directory,
                edit_func=self.__path_edit_callback,
                save_func=self._path_save_callback_mac,
            )
            self.ui.install_dir_layout.addWidget(self.mac_install_dir_edit)

        # Platform-independent installation directory
        self.install_dir_edit = PathEdit(
            path=self.core.get_default_install_dir(),
            placeholder=self.tr("Default installation folder for Windows games"),
            file_mode=QFileDialog.FileMode.Directory,
            edit_func=self.__path_edit_callback,
            save_func=self._path_save_callback_win,
        )
        self.ui.install_dir_layout.addWidget(self.install_dir_edit)

        # Max Workers
        self.ui.max_worker_spin.setValue(self.core.lgd.config["Legendary"].getint("max_workers", fallback=0))
        self.ui.max_worker_spin.valueChanged.connect(self.max_worker_save)

        # Max memory
        self.ui.max_memory_spin.setValue(self.core.lgd.config["Legendary"].getint("max_memory", fallback=0))
        self.ui.max_memory_spin.valueChanged.connect(self.max_memory_save)

        # Preferred CDN
        self.ui.preferred_cdn_line.setText(self.core.lgd.config["Legendary"].get("preferred_cdn", fallback=""))
        self.ui.preferred_cdn_line.textChanged.connect(self.preferred_cdn_save)

        # Disable HTTPS
        self.ui.disable_https_check.setChecked(self.core.lgd.config["Legendary"].getboolean("disable_https", fallback=False))
        self.ui.disable_https_check.checkStateChanged.connect(self.disable_https_save)

        # Clean metadata
        self.ui.clean_button.clicked.connect(self._on_clean_clicked)
        self.ui.clean_keep_manifests_button.clicked.connect(self._on_clean_keep_manifests_clicked)

        self.locale_edit = IndicatorLineEdit(
            f"{self.core.language_code}-{self.core.country_code}",
            edit_func=self.__locale_edit_callback,
            save_func=self.__locale_save_callback,
            horiz_policy=QSizePolicy.Policy.Minimum,
            parent=self,
        )
        self.ui.locale_layout.addWidget(self.locale_edit)

        self.ui.fetch_win32_check.setChecked(self.settings.get_value(app_settings.win32_meta))
        self.ui.fetch_win32_check.checkStateChanged.connect(self._on_fetch_win32_changed)

        self.ui.fetch_macos_check.setChecked(self.settings.get_value(app_settings.macos_meta))
        self.ui.fetch_macos_check.checkStateChanged.connect(self._on_fetch_macos_changed)
        self.ui.fetch_macos_check.setDisabled(pf.system() == "Darwin")

        self.ui.fetch_unreal_check.setChecked(self.settings.get_value(app_settings.unreal_meta))
        self.ui.fetch_unreal_check.checkStateChanged.connect(self._on_fetch_unreal_changed)

        self.ui.exclude_non_asset_check.setChecked(self.settings.get_value(app_settings.exclude_non_asset))
        self.ui.exclude_non_asset_check.checkStateChanged.connect(self._on_exclude_non_asset_changed)

        self.ui.exclude_entitlements_check.setChecked(self.settings.get_value(app_settings.exclude_entitlements))
        self.ui.exclude_entitlements_check.checkStateChanged.connect(self._on_exclude_entitlements_changed)

        self.ui.refresh_metadata_button.clicked.connect(self._refresh_metadata)
        # FIXME: Disable the button for now because it interferes with RareCore
        self.ui.refresh_metadata_button.setEnabled(False)
        self.ui.refresh_metadata_button.setVisible(False)

    def showEvent(self, a0: QShowEvent):
        if a0.spontaneous():
            return super().showEvent(a0)
        if pf.system() == "Darwin":
            self.mac_install_dir_edit.refresh()
        self.install_dir_edit.refresh()
        return super().showEvent(a0)

    def hideEvent(self, a0: QHideEvent):
        if a0.spontaneous():
            return super().hideEvent(a0)
        self.core.lgd.save_config()
        return super().hideEvent(a0)

    @Slot()
    def _on_refresh_worker_finished(self):
        self.ui.refresh_metadata_button.setDisabled(False)

    def _refresh_metadata(self):
        self.ui.refresh_metadata_button.setDisabled(True)
        platforms = set()
        if self.ui.fetch_win32_check.isChecked():
            platforms.add("Win32")
        if self.ui.fetch_macos_check.isChecked():
            platforms.add("Mac")
        worker = RefreshGameMetaWorker(self.core, platforms, self.ui.fetch_unreal_check.isChecked())
        worker.signals.finished.connect(self._on_refresh_worker_finished)
        QThreadPool.globalInstance().start(worker)

    @staticmethod
    def __locale_edit_callback(text: str) -> Tuple[bool, str, int]:
        if text:
            if re.match("^[a-zA-Z]{2,3}[-_][a-zA-Z]{2,3}$", text):
                language, country = text.split("-" if "-" in text else "_")
                text = "-".join([language.lower(), country.upper()])
            if bool(re.match("^[a-z]{2,3}-[A-Z]{2,3}$", text)):
                return True, text, IndicatorReasonsCommon.VALID
            else:
                return False, text, IndicatorReasonsCommon.WRONG_FORMAT
        else:
            return True, text, IndicatorReasonsCommon.VALID

    def __locale_save_callback(self, text: str):
        if text:
            self.core.egs.language_code, self.core.egs.country_code = text.split("-")
            self.core.lgd.config.set("Legendary", "locale", text)
        else:
            self.core.lgd.config.remove_option("Legendary", "locale")

    @staticmethod
    def __path_edit_callback(path: str) -> Tuple[bool, str, int]:
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

    @Slot(str)
    def _path_save_callback_mac(self, text: str) -> None:
        self._path_save(text, "mac_install_dir")

    @Slot(str)
    def _path_save_callback_win(self, text: str) -> None:
        self._path_save(text, "install_dir")
        if pf.system() != "Darwin":
            self._path_save_callback_mac(text)

    def _path_save(self, text: str, option: str):
        if text:
            self.core.lgd.config.set("Legendary", option, text)
        else:
            self.core.lgd.config.remove_option("Legendary", option)

    @Slot(int)
    def max_worker_save(self, workers: int):
        if workers:
            self.core.lgd.config.set("Legendary", "max_workers", str(workers))
        else:
            self.core.lgd.config.remove_option("Legendary", "max_workers")

    @Slot(int)
    def max_memory_save(self, memory: int):
        if memory:
            self.core.lgd.config.set("Legendary", "max_memory", str(memory))
        else:
            self.core.lgd.config.remove_option("Legendary", "max_memory")

    @Slot(str)
    def preferred_cdn_save(self, cdn: str):
        if cdn:
            self.core.lgd.config.set("Legendary", "preferred_cdn", cdn.strip())
        else:
            self.core.lgd.config.remove_option("Legendary", "preferred_cdn")

    @Slot(Qt.CheckState)
    def disable_https_save(self, state: Qt.CheckState):
        self.core.lgd.config.set("Legendary", "disable_https", str(state != Qt.CheckState.Unchecked).lower())

    def clean_metadata(self, keep_manifests: bool):
        before = self.core.lgd.get_dir_size()
        logger.debug("Removing app metadata...")
        app_names = {g.app_name for g in self.core.get_assets(update_assets=False)}
        self.core.lgd.clean_metadata(app_names)

        if not keep_manifests:
            logger.debug("Removing manifests...")
            installed = [(ig.app_name, ig.version, ig.platform) for ig in self.core.get_installed_list()]
            installed.extend((ig.app_name, ig.version, ig.platform) for ig in self.core.get_installed_dlc_list())
            self.core.lgd.clean_manifests(installed)

        logger.debug("Removing tmp data")
        self.core.lgd.clean_tmp_data()

        after = self.core.lgd.get_dir_size()
        logger.info(f"Cleanup complete! Removed {(before - after) / 1024 / 1024:.02f} MiB.")
        if (before - after) > 0:
            QMessageBox.information(
                self,
                self.tr("Cleanup"),
                self.tr("Cleanup complete! Successfully removed {}").format(format_size(before - after)),
            )
        else:
            QMessageBox.information(self, self.tr("Cleanup"), self.tr("Nothing to clean"))

    @Slot()
    def _on_clean_clicked(self):
        self.clean_metadata(keep_manifests=False)

    @Slot()
    def _on_clean_keep_manifests_clicked(self):
        self.clean_metadata(keep_manifests=True)

    @Slot(Qt.CheckState)
    def _on_fetch_win32_changed(self, state: Qt.CheckState):
        self.settings.set_value(app_settings.win32_meta, state != Qt.CheckState.Unchecked)

    @Slot(Qt.CheckState)
    def _on_fetch_macos_changed(self, state: Qt.CheckState):
        self.settings.set_value(app_settings.macos_meta, state != Qt.CheckState.Unchecked)

    @Slot(Qt.CheckState)
    def _on_fetch_unreal_changed(self, state: Qt.CheckState):
        self.settings.set_value(app_settings.unreal_meta, state != Qt.CheckState.Unchecked)

    @Slot(Qt.CheckState)
    def _on_exclude_non_asset_changed(self, state: Qt.CheckState):
        self.settings.set_value(app_settings.exclude_non_asset, state != Qt.CheckState.Unchecked)

    @Slot(Qt.CheckState)
    def _on_exclude_entitlements_changed(self, state: Qt.CheckState):
        self.settings.set_value(app_settings.exclude_entitlements, state != Qt.CheckState.Unchecked)
