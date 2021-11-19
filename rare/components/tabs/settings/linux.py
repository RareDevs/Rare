from logging import getLogger

from PyQt5.QtWidgets import QFileDialog, QWidget

from rare import shared
from rare.components.tabs.settings.dxvk import DxvkSettings
from rare.ui.components.tabs.settings.linux import Ui_LinuxSettings
from rare.utils.extra_widgets import PathEdit

logger = getLogger("LinuxSettings")


class LinuxSettings(QWidget, Ui_LinuxSettings):
    def __init__(self, name=None):
        super(LinuxSettings, self).__init__()
        self.setupUi(self)

        self.name = name if name is not None else "default"
        self.core = shared.core

        # Wine prefix
        self.wine_prefix = PathEdit(self.core.lgd.config.get(self.name, "wine_prefix", fallback=""),
                                    file_type=QFileDialog.DirectoryOnly,
                                    save_func=lambda text: self.save_setting(text, "wine_prefix"))
        self.prefix_layout.addWidget(self.wine_prefix)

        # Wine executable
        self.wine_exec = PathEdit(self.core.lgd.config.get(self.name, "wine_executable", fallback=""),
                                  file_type=QFileDialog.ExistingFile,
                                  name_filter="Wine executable (wine wine64)",
                                  save_func=lambda text: self.save_setting(text, "wine_executable"))
        self.exec_layout.addWidget(self.wine_exec)

        # dxvk
        self.dxvk = DxvkSettings(self.name)
        self.dxvk_layout.addWidget(self.dxvk)

    def save_setting(self, text: str, setting_name: str):
        if self.name not in self.core.lgd.config.sections():
            self.core.lgd.config.add_section(self.name)

        self.core.lgd.config.set(self.name, setting_name, text)
        if not text:
            self.core.lgd.config.remove_option(self.name, setting_name)
        else:
            logger.debug("Set config of wine_prefix to " + text)
        if self.core.lgd.config[self.name] == {}:
            self.core.lgd.config.remove_section(self.name)
        self.core.lgd.save_config()
