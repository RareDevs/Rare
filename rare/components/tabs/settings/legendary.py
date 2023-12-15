import platform as pf
import re
from logging import getLogger
from typing import Tuple, List

from PyQt5.QtCore import QObject, pyqtSignal, QThreadPool, QSettings
from PyQt5.QtWidgets import QSizePolicy, QWidget, QFileDialog, QMessageBox

from rare.shared import LegendaryCoreSingleton
from rare.shared.workers.worker import Worker
from rare.ui.components.tabs.settings.legendary import Ui_LegendarySettings
from rare.utils.misc import format_size
from rare.widgets.indicator_edit import PathEdit, IndicatorLineEdit, IndicatorReasonsCommon

logger = getLogger("LegendarySettings")


class RefreshGameMetaWorker(Worker):
    class Signals(QObject):
        finished = pyqtSignal()

    def __init__(self, platforms: List[str], include_unreal: bool):
        super(RefreshGameMetaWorker, self).__init__()
        self.signals = RefreshGameMetaWorker.Signals()
        self.core = LegendaryCoreSingleton()
        if platforms:
            self.platforms = platforms
        else:
            self.platforms = ["Windows"]
        self.skip_ue = not include_unreal

    def run_real(self) -> None:
        for platform in self.platforms:
            self.core.get_game_and_dlc_list(
                True, platform=platform, force_refresh=True, skip_ue=self.skip_ue
            )
        self.signals.finished.emit()


class LegendarySettings(QWidget, Ui_LegendarySettings):
    def __init__(self, parent=None):
        super(LegendarySettings, self).__init__(parent=parent)
        self.setupUi(self)
        self.settings = QSettings(self)

        self.core = LegendaryCoreSingleton()

        # Platform specific installation directory for macOS games
        if pf.system() == "Darwin":
            self.mac_install_dir = PathEdit(
                self.core.get_default_install_dir("Mac"),
                placeholder=self.tr("Default installation folder for macOS games"),
                file_mode=QFileDialog.DirectoryOnly,
                save_func=self.__mac_path_save,
            )
            self.install_dir_layout.addWidget(self.mac_install_dir)

        # Platform-independent installation directory
        self.install_dir = PathEdit(
            self.core.get_default_install_dir(),
            placeholder=self.tr("Default installation folder for Windows games"),
            file_mode=QFileDialog.DirectoryOnly,
            save_func=self.__win_path_save,
        )
        self.install_dir_layout.addWidget(self.install_dir)

        # Max Workers
        max_workers = self.core.lgd.config["Legendary"].getint(
            "max_workers", fallback=0
        )
        self.max_worker_spin.setValue(max_workers)
        self.max_worker_spin.valueChanged.connect(self.max_worker_save)
        # Max memory
        max_memory = self.core.lgd.config["Legendary"].getint("max_memory", fallback=0)
        self.max_memory_spin.setValue(max_memory)
        self.max_memory_spin.valueChanged.connect(self.max_memory_save)
        # Preferred CDN
        preferred_cdn = self.core.lgd.config["Legendary"].get(
            "preferred_cdn", fallback=""
        )
        self.preferred_cdn_line.setText(preferred_cdn)
        self.preferred_cdn_line.textChanged.connect(self.preferred_cdn_save)
        # Disable HTTPS
        disable_https = self.core.lgd.config["Legendary"].getboolean(
            "disable_https", fallback=False
        )
        self.disable_https_check.setChecked(disable_https)
        self.disable_https_check.stateChanged.connect(self.disable_https_save)

        # Cleanup
        self.clean_button.clicked.connect(lambda: self.cleanup(False))
        self.clean_keep_manifests_button.clicked.connect(lambda: self.cleanup(True))

        self.locale_edit = IndicatorLineEdit(
            f"{self.core.language_code}-{self.core.country_code}",
            edit_func=self.locale_edit_cb,
            save_func=self.locale_save_cb,
            horiz_policy=QSizePolicy.Minimum,
            parent=self,
        )
        self.locale_layout.addWidget(self.locale_edit)

        self.fetch_win32_check.setChecked(self.settings.value("win32_meta", False, bool))
        self.fetch_win32_check.stateChanged.connect(
            lambda: self.settings.setValue("win32_meta", self.fetch_win32_check.isChecked())
        )

        self.fetch_macos_check.setChecked(self.settings.value("macos_meta", pf.system() == "Darwin", bool))
        self.fetch_macos_check.stateChanged.connect(
            lambda: self.settings.setValue("macos_meta", self.fetch_macos_check.isChecked())
        )
        self.fetch_macos_check.setDisabled(pf.system() == "Darwin")

        self.fetch_unreal_check.setChecked(self.settings.value("unreal_meta", False, bool))
        self.fetch_unreal_check.stateChanged.connect(
            lambda: self.settings.setValue("unreal_meta", self.fetch_unreal_check.isChecked())
        )

        self.refresh_metadata_button.clicked.connect(self.refresh_metadata)
        # FIXME: Disable the button for now because it interferes with RareCore
        self.refresh_metadata_button.setEnabled(False)
        self.refresh_metadata_button.setVisible(False)

    def refresh_metadata(self):
        self.refresh_metadata_button.setDisabled(True)
        platforms = []
        if self.fetch_win32_check.isChecked():
            platforms.append("Win32")
        if self.fetch_macos_check.isChecked():
            platforms.append("Mac")
        worker = RefreshGameMetaWorker(platforms, self.fetch_unreal_check.isChecked())
        worker.signals.finished.connect(lambda: self.refresh_metadata_button.setDisabled(False))
        QThreadPool.globalInstance().start(worker)

    @staticmethod
    def locale_edit_cb(text: str) -> Tuple[bool, str, int]:
        if text:
            if re.match("^[a-zA-Z]{2,3}[-_][a-zA-Z]{2,3}$", text):
                language, country = text.replace("_", "-").split("-")
                text = "-".join([language.lower(), country.upper()])
            if bool(re.match("^[a-z]{2,3}-[A-Z]{2,3}$", text)):
                return True, text, IndicatorReasonsCommon.VALID
            else:
                return False, text, IndicatorReasonsCommon.WRONG_FORMAT
        else:
            return True, text, IndicatorReasonsCommon.VALID

    def locale_save_cb(self, text: str):
        if text:
            self.core.egs.language_code, self.core.egs.country_code = text.split("-")
            self.core.lgd.config.set("Legendary", "locale", text)
        else:
            if self.core.lgd.config.has_option("Legendary", "locale"):
                self.core.lgd.config.remove_option("Legendary", "locale")
        self.core.lgd.save_config()

    def __mac_path_save(self, text: str) -> None:
        self.__path_save(text, "mac_install_dir")

    def __win_path_save(self, text: str) -> None:
        self.__path_save(text, "install_dir")
        if pf.system() != "Darwin":
            self.__mac_path_save(text)

    def __path_save(self, text: str, option: str = "Windows"):
        self.core.lgd.config["Legendary"][option] = text
        if not text and option in self.core.lgd.config["Legendary"].keys():
            self.core.lgd.config["Legendary"].pop(option)
        else:
            logger.debug(f"Set %s option in config to %s", option, text)
        self.core.lgd.save_config()

    def max_worker_save(self, workers: str):
        if workers := int(workers):
            self.core.lgd.config.set("Legendary", "max_workers", str(workers))
        else:
            self.core.lgd.config.remove_option("Legendary", "max_workers")
        self.core.lgd.save_config()

    def max_memory_save(self, memory: str):
        if memory := int(memory):
            self.core.lgd.config.set("Legendary", "max_memory", str(memory))
        else:
            self.core.lgd.config.remove_option("Legendary", "max_memory")
        self.core.lgd.save_config()

    def preferred_cdn_save(self, cdn: str):
        if cdn:
            self.core.lgd.config.set("Legendary", "preferred_cdn", cdn.strip())
        else:
            self.core.lgd.config.remove_option("Legendary", "preferred_cdn")
        self.core.lgd.save_config()

    def disable_https_save(self, checked: int):
        self.core.lgd.config.set(
            "Legendary", "disable_https", str(bool(checked)).lower()
        )
        self.core.lgd.save_config()

    def cleanup(self, keep_manifests: bool):
        before = self.core.lgd.get_dir_size()
        logger.debug("Removing app metadata...")
        app_names = set(g.app_name for g in self.core.get_assets(update_assets=False))
        self.core.lgd.clean_metadata(app_names)

        if not keep_manifests:
            logger.debug("Removing manifests...")
            installed = [
                (ig.app_name, ig.version, ig.platform) for ig in self.core.get_installed_list()
            ]
            installed.extend(
                (ig.app_name, ig.version, ig.platform) for ig in self.core.get_installed_dlc_list()
            )
            self.core.lgd.clean_manifests(installed)

        logger.debug("Removing tmp data")
        self.core.lgd.clean_tmp_data()

        after = self.core.lgd.get_dir_size()
        logger.info(
            f"Cleanup complete! Removed {(before - after) / 1024 / 1024:.02f} MiB."
        )
        if (before - after) > 0:
            QMessageBox.information(
                self,
                "Cleanup",
                self.tr("Cleanup complete! Successfully removed {}").format(
                    format_size(before - after)
                ),
            )
        else:
            QMessageBox.information(self, "Cleanup", "Nothing to clean")
