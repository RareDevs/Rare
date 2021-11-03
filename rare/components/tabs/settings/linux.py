import os
from logging import getLogger

from PyQt5.QtWidgets import QFileDialog, QWidget, QMessageBox

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
            logger.info("Set config of wine_prefix to " + text)
        if self.core.lgd.config[self.name] == {}:
            self.core.lgd.config.remove_section(self.name)
        self.core.lgd.save_config()

        if setting_name == "wine_prefix":
            if not os.path.isdir(text) or not os.path.exists(os.path.join(text, "user.reg")):
                return
            if self.name != "default":  # if game
                game = self.core.get_game(self.name)
                if self.core.is_installed(self.name) and game.supports_cloud_saves:
                    try:
                        new_path = self.core.get_save_path(self.name)
                    except Exception as e:
                        QMessageBox.warning(self, "Error", self.tr("Could not compute save path for {}").format(
                            game.app_title) + "\n" + str(e))
                        return
                    igame = self.core.get_installed_game(self.name)
                    igame.save_path = new_path
                    self.core.lgd.set_installed_game(self.name, igame)
