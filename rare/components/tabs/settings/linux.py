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

        # Wine prefix
        self.wine_prefix = PathEdit(
            self.load_prefix(),
            file_type=QFileDialog.DirectoryOnly,
            save_func=self.save_prefix)
        self.prefix_layout.addWidget(self.wine_prefix)

        # Wine executable
        self.wine_exec = PathEdit(
            self.load_setting(self.name, "wine_executable"),
            file_type=QFileDialog.ExistingFile,
            name_filter="Wine executable (wine wine64)",
            save_func=lambda text: self.save_setting(text, section=self.name, setting="wine_executable"))
        self.exec_layout.addWidget(self.wine_exec)

        # dxvk
        self.dxvk = DxvkSettings(self.name)
        self.dxvk_layout.addWidget(self.dxvk)

    def load_prefix(self) -> str:
        return self.load_setting(f'{self.name}.env',
                                 'WINEPREFIX',
                                 fallback=self.load_setting(self.name, 'wine_prefix'))

    def save_prefix(self, text: str):
        self.save_setting(text, f'{self.name}.env', 'WINEPREFIX')
        self.save_setting(text, self.name, 'wine_prefix')

    @staticmethod
    def load_setting(section: str, setting: str, fallback: str = str()):
        return shared.core.lgd.config.get(section, setting, fallback=fallback)

    @staticmethod
    def save_setting(text: str, section: str, setting: str):
        if text:
            if section not in shared.core.lgd.config.sections():
                shared.core.lgd.config.add_section(section)
                logger.debug(f"Added {f'[{section}]'} configuration section")
            shared.core.lgd.config.set(section, setting, text)
            logger.debug(f"Set {setting} in {f'[{section}]'} to {text}")

        else:
            if shared.core.lgd.config.has_section(section) and shared.core.lgd.config.has_option(section, setting):
                shared.core.lgd.config.remove_option(section, setting)
                logger.debug(f"Unset {setting} from {f'[{section}]'}")
                if not shared.core.lgd.config[section]:
                    shared.core.lgd.config.remove_section(section)
                    logger.debug(f"Removed {f'[{section}]'} configuration section")

        shared.core.lgd.save_config()
