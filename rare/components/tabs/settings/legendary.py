import re
from logging import getLogger
from typing import Tuple

from PyQt5.QtWidgets import QSizePolicy, QWidget, QFileDialog, QMessageBox

import rare.shared as shared
from rare.components.tabs.settings.ubisoft_activation import UbiActivationHelper
from rare.ui.components.tabs.settings.legendary import Ui_LegendarySettings
from rare.utils.extra_widgets import PathEdit, IndicatorLineEdit
from rare.utils.utils import get_size

logger = getLogger("LegendarySettings")


class LegendarySettings(QWidget, Ui_LegendarySettings):
    def __init__(self, parent=None):
        super(LegendarySettings, self).__init__(parent=parent)
        self.setupUi(self)

        self.core = shared.core

        # Default installation directory
        self.install_dir = PathEdit(self.core.get_default_install_dir(),
                                    file_type=QFileDialog.DirectoryOnly,
                                    save_func=self.path_save)
        self.install_dir_layout.addWidget(self.install_dir)

        # Max Workers
        max_workers = self.core.lgd.config['Legendary'].getint('max_workers', fallback=0)
        self.max_worker_spin.setValue(max_workers)
        self.max_worker_spin.valueChanged.connect(self.max_worker_save)
        # Max memory
        max_memory = self.core.lgd.config['Legendary'].getint('max_memory', fallback=0)
        self.max_memory_spin.setValue(max_memory)
        self.max_memory_spin.valueChanged.connect(self.max_memory_save)
        # Preferred CDN
        preferred_cdn = self.core.lgd.config['Legendary'].get('preferred_cdn', fallback="")
        self.preferred_cdn_line.setText(preferred_cdn)
        self.preferred_cdn_line.textChanged.connect(self.preferred_cdn_save)
        # Disable HTTPS
        disable_https = self.core.lgd.config['Legendary'].getboolean('disable_https', fallback=False)
        self.disable_https_check.setChecked(disable_https)
        self.disable_https_check.stateChanged.connect(self.disable_https_save)

        # Cleanup
        self.clean_button.clicked.connect(
            lambda: self.cleanup(False)
        )
        self.clean_keep_manifests_button.clicked.connect(
            lambda: self.cleanup(True)
        )

        self.locale_edit = IndicatorLineEdit(
            f"{self.core.language_code}-{self.core.country_code}",
            edit_func=self.locale_edit_cb,
            save_func=self.locale_save_cb,
            horiz_policy=QSizePolicy.Minimum,
            parent=self
        )
        self.locale_layout.addWidget(self.locale_edit)

        self.ubi_helper = UbiActivationHelper(self.ubisoft_gb)

    @staticmethod
    def locale_edit_cb(text: str) -> Tuple[bool, str]:
        if text:
            if re.match("^[a-zA-Z]{2,3}[-_][a-zA-Z]{2,3}$", text):
                language, country = text.replace("_", "-").split("-")
                text = "-".join([language.lower(), country.upper()])
            return bool(re.match("^[a-z]{2,3}-[A-Z]{2,3}$", text)), text
        else:
            return True, text

    def locale_save_cb(self, text: str):
        if text:
            self.core.egs.language_code, self.core.egs.country_code = text.split("-")
            self.core.lgd.config.set("Legendary", "locale", text)
        else:
            if self.core.lgd.config.has_option("Legendary", "locale"):
                self.core.lgd.config.remove_option("Legendary", "locale")
        self.core.lgd.save_config()

    def path_save(self, text: str):
        self.core.lgd.config["Legendary"]["install_dir"] = text
        if not text and "install_dir" in self.core.lgd.config["Legendary"].keys():
            self.core.lgd.config["Legendary"].pop("install_dir")
        else:
            logger.debug("Set config install_dir to " + text)
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
        self.core.lgd.config.set("Legendary", "disable_https", str(bool(checked)).lower())
        self.core.lgd.save_config()

    def cleanup(self, keep_manifests: bool):
        before = self.core.lgd.get_dir_size()
        logger.debug('Removing app metadata...')
        app_names = set(g.app_name for g in self.core.get_assets(update_assets=False))
        self.core.lgd.clean_metadata(app_names)

        if not keep_manifests:
            logger.debug('Removing manifests...')
            installed = [(ig.app_name, ig.version) for ig in self.core.get_installed_list()]
            installed.extend((ig.app_name, ig.version) for ig in self.core.get_installed_dlc_list())
            self.core.lgd.clean_manifests(installed)

        logger.debug('Removing tmp data')
        self.core.lgd.clean_tmp_data()

        after = self.core.lgd.get_dir_size()
        logger.info(f'Cleanup complete! Removed {(before - after) / 1024 / 1024:.02f} MiB.')
        if (before - after) > 0:
            QMessageBox.information(self, "Cleanup", self.tr("Cleanup complete! Successfully removed {}").format(
                get_size(before - after)))
        else:
            QMessageBox.information(self, "Cleanup", "Nothing to clean")
