import os
import shutil
from logging import getLogger

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QFileDialog, QWidget

from rare.components.tabs.settings.widgets.dxvk import DxvkSettings
from rare.components.tabs.settings.widgets.mangohud import MangoHudSettings
from rare.shared import LegendaryCoreSingleton, GlobalSignalsSingleton
from rare.ui.components.tabs.settings.linux import Ui_LinuxSettings
from rare.widgets.indicator_edit import PathEdit, IndicatorReasonsCommon
from rare.utils import config_helper

logger = getLogger("LinuxSettings")


class LinuxSettings(QWidget):
    # str: option key
    environ_changed = pyqtSignal(str)

    def __init__(self, name=None, parent=None):
        super(LinuxSettings, self).__init__(parent=parent)
        self.ui = Ui_LinuxSettings()
        self.ui.setupUi(self)

        self.core = LegendaryCoreSingleton()
        self.signals = GlobalSignalsSingleton()

        self.name = name if name is not None else "default"

        # Wine prefix
        self.wine_prefix = PathEdit(
            self.load_prefix(),
            file_mode=QFileDialog.DirectoryOnly,
            edit_func=lambda path: (os.path.isdir(path) or not path, path, IndicatorReasonsCommon.DIR_NOT_EXISTS),
            save_func=self.save_prefix,
        )
        self.ui.prefix_layout.addWidget(self.wine_prefix)

        # Wine executable
        self.wine_exec = PathEdit(
            self.load_setting(self.name, "wine_executable"),
            file_mode=QFileDialog.ExistingFile,
            name_filters=["wine", "wine64"],
            edit_func=lambda text: (os.path.exists(text) or not text, text, IndicatorReasonsCommon.DIR_NOT_EXISTS),
            save_func=lambda text: self.save_setting(
                text, section=self.name, setting="wine_executable"
            ),
        )
        self.ui.exec_layout.addWidget(self.wine_exec)

        # dxvk
        self.dxvk = DxvkSettings()
        self.dxvk.environ_changed.connect(self.environ_changed)
        self.ui.linux_layout.addWidget(self.dxvk)
        self.dxvk.load_settings(self.name)

        self.mangohud = MangoHudSettings()
        self.mangohud.environ_changed.connect(self.environ_changed)
        self.ui.linux_layout.addWidget(self.mangohud)
        self.mangohud.load_settings(self.name)


    def load_prefix(self) -> str:
        return self.load_setting(
            f"{self.name}.env",
            "WINEPREFIX",
            fallback=self.load_setting(self.name, "wine_prefix"),
        )

    def save_prefix(self, text: str):
        self.save_setting(text, f"{self.name}.env", "WINEPREFIX")
        self.environ_changed.emit("WINEPREFIX")
        self.save_setting(text, self.name, "wine_prefix")
        self.signals.application.prefix_updated.emit()

    def load_setting(self, section: str, setting: str, fallback: str = ""):
        return self.core.lgd.config.get(section, setting, fallback=fallback)

    def save_setting(self, text: str, section: str, setting: str):
        if text:
            config_helper.add_option(section, setting, text)
            logger.debug(f"Set {setting} in {f'[{section}]'} to {text}")
        else:
            config_helper.remove_option(section, setting)
            logger.debug(f"Unset {setting} from {f'[{section}]'}")
        config_helper.save_config()
