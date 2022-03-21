import os
import shutil
from logging import getLogger

from PyQt5.QtWidgets import QFileDialog, QWidget

from rare.components.tabs.settings.widgets.dxvk import DxvkSettings
from rare.components.tabs.settings.widgets.mangohud import MangoHudSettings
from rare.shared import LegendaryCoreSingleton, GlobalSignalsSingleton

from rare.ui.components.tabs.settings.linux import Ui_LinuxSettings
from rare.utils.extra_widgets import PathEdit

logger = getLogger("LinuxSettings")


class LinuxSettings(QWidget, Ui_LinuxSettings):
    def __init__(self, name=None):
        super(LinuxSettings, self).__init__()
        self.setupUi(self)

        self.core = LegendaryCoreSingleton()
        self.signals = GlobalSignalsSingleton()

        self.name = name if name is not None else "default"

        # Wine prefix
        self.wine_prefix = PathEdit(
            self.load_prefix(),
            file_type=QFileDialog.DirectoryOnly,
            edit_func=lambda path: (os.path.isdir(path) or not path, path, PathEdit.reasons.dir_not_exist),
            save_func=self.save_prefix,
        )
        self.prefix_layout.addWidget(self.wine_prefix)

        # Wine executable
        self.wine_exec = PathEdit(
            self.load_setting(self.name, "wine_executable"),
            file_type=QFileDialog.ExistingFile,
            name_filter="Wine executable (wine wine64)",
            edit_func=lambda text: (os.path.exists(text) or not text, text, PathEdit.reasons.dir_not_exist),
            save_func=lambda text: self.save_setting(
                text, section=self.name, setting="wine_executable"
            ),
        )
        self.exec_layout.addWidget(self.wine_exec)

        # dxvk
        self.dxvk = DxvkSettings()
        self.overlay_layout.addWidget(self.dxvk)
        self.dxvk.load_settings(self.name)

        self.mangohud = MangoHudSettings()
        self.overlay_layout.addWidget(self.mangohud)
        self.mangohud.load_settings(self.name)

        if not shutil.which("mangohud"):
            self.mangohud.setDisabled(True)
            self.mangohud.setToolTip(self.tr("Mangohud is not installed or not in path"))

    def load_prefix(self) -> str:
        return self.load_setting(
            f"{self.name}.env",
            "WINEPREFIX",
            fallback=self.load_setting(self.name, "wine_prefix"),
        )

    def save_prefix(self, text: str):
        self.save_setting(text, f"{self.name}.env", "WINEPREFIX")
        self.save_setting(text, self.name, "wine_prefix")
        self.signals.wine_prefix_updated.emit()

    def load_setting(self, section: str, setting: str, fallback: str = str()):
        return self.core.lgd.config.get(section, setting, fallback=fallback)

    def save_setting(self, text: str, section: str, setting: str):
        if text:
            if section not in self.core.lgd.config.sections():
                self.core.lgd.config.add_section(section)
                logger.debug(f"Added {f'[{section}]'} configuration section")
            self.core.lgd.config.set(section, setting, text)
            logger.debug(f"Set {setting} in {f'[{section}]'} to {text}")

        else:
            if self.core.lgd.config.has_section(
                section
            ) and self.core.lgd.config.has_option(section, setting):
                self.core.lgd.config.remove_option(section, setting)
                logger.debug(f"Unset {setting} from {f'[{section}]'}")
                if not self.core.lgd.config[section]:
                    self.core.lgd.config.remove_section(section)
                    logger.debug(f"Removed {f'[{section}]'} configuration section")

        self.core.lgd.save_config()
