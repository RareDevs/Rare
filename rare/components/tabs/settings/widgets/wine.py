import os
import shutil
from logging import getLogger

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QFileDialog, QWidget, QFormLayout, QGroupBox

from rare.shared import LegendaryCoreSingleton, GlobalSignalsSingleton
from rare.ui.components.tabs.settings.widgets.wine import Ui_WineSettings
from rare.widgets.indicator_edit import PathEdit, IndicatorReasonsCommon
from rare.utils import config_helper

logger = getLogger("LinuxSettings")


class WineSettings(QGroupBox):
    # str: option key
    environ_changed = pyqtSignal(str)

    def __init__(self, name=None, parent=None):
        super(WineSettings, self).__init__(parent=parent)
        self.ui = Ui_WineSettings()
        self.ui.setupUi(self)

        self.core = LegendaryCoreSingleton()
        self.signals = GlobalSignalsSingleton()

        self.app_name: str = "default"

        # Wine prefix
        self.wine_prefix = PathEdit(
            self.load_prefix(),
            file_mode=QFileDialog.DirectoryOnly,
            edit_func=lambda path: (os.path.isdir(path) or not path, path, IndicatorReasonsCommon.DIR_NOT_EXISTS),
            save_func=self.save_prefix,
        )
        self.ui.main_layout.setWidget(
            self.ui.main_layout.getWidgetPosition(self.ui.prefix_label)[0],
            QFormLayout.FieldRole,
            self.wine_prefix
        )

        # Wine executable
        self.wine_exec = PathEdit(
            self.load_setting(self.app_name, "wine_executable"),
            file_mode=QFileDialog.ExistingFile,
            name_filters=["wine", "wine64"],
            edit_func=lambda text: (os.path.exists(text) or not text, text, IndicatorReasonsCommon.DIR_NOT_EXISTS),
            save_func=lambda text: self.save_setting(
                text, section=self.app_name, setting="wine_executable"
            ),
        )
        self.ui.main_layout.setWidget(
            self.ui.main_layout.getWidgetPosition(self.ui.exec_label)[0],
            QFormLayout.FieldRole,
            self.wine_exec
        )

    def load_prefix(self) -> str:
        return self.load_setting(
            f"{self.app_name}.env",
            "WINEPREFIX",
            fallback=self.load_setting(self.app_name, "wine_prefix"),
        )

    def save_prefix(self, text: str):
        self.save_setting(text, f"{self.app_name}.env", "WINEPREFIX")
        self.environ_changed.emit("WINEPREFIX")
        self.save_setting(text, self.app_name, "wine_prefix")
        self.signals.application.prefix_updated.emit()

    def load_setting(self, section: str, setting: str, fallback: str = ""):
        return self.core.lgd.config.get(section, setting, fallback=fallback)

    @staticmethod
    def save_setting(text: str, section: str, setting: str):
        if text:
            config_helper.add_option(section, setting, text)
            logger.debug(f"Set {setting} in {f'[{section}]'} to {text}")
        else:
            config_helper.remove_option(section, setting)
            logger.debug(f"Unset {setting} from {f'[{section}]'}")
        config_helper.save_config()
