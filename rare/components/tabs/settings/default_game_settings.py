import platform
from logging import getLogger

from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtWidgets import (
    QWidget,
    QLabel
)

from rare.components.tabs.settings.widgets.env_vars import EnvVars
from rare.components.tabs.settings.widgets.linux import LinuxSettings
from rare.components.tabs.settings.widgets.proton import ProtonSettings
from rare.components.tabs.settings.widgets.wrapper import WrapperSettings
from rare.shared import LegendaryCoreSingleton
from rare.ui.components.tabs.games.game_info.game_settings import Ui_GameSettings
from rare.utils import config_helper

logger = getLogger("GameSettings")


class DefaultGameSettings(QWidget, Ui_GameSettings):
    # variable to no update when changing game
    change = False
    app_name: str

    def __init__(self, is_default, parent=None):
        super(DefaultGameSettings, self).__init__(parent=parent)
        self.setupUi(self)
        self.core = LegendaryCoreSingleton()
        self.settings = QSettings()

        self.wrapper_settings = WrapperSettings()

        self.launch_settings_group.layout().addRow(
            QLabel("Wrapper"), self.wrapper_settings
        )

        if platform.system() != "Windows":
            self.linux_settings = LinuxAppSettings()
            self.proton_settings = ProtonSettings(self.linux_settings, self.wrapper_settings)
            self.proton_layout.addWidget(self.proton_settings)

            # FIXME: Remove the spacerItem and margins from the linux settings
            # FIXME: This should be handled differently at soem point in the future
            self.linux_settings.layout().setContentsMargins(0, 0, 0, 0)
            for item in [
                self.linux_settings.layout().itemAt(idx)
                for idx in range(self.linux_settings.layout().count())
            ]:
                if item.spacerItem():
                    self.linux_settings.layout().removeItem(item)
                    del item
            # FIXME: End of FIXME
            self.linux_settings_layout.addWidget(self.linux_settings)
            self.linux_settings_layout.setAlignment(Qt.AlignTop)

            self.game_settings_layout.setAlignment(Qt.AlignTop)

            self.linux_settings.mangohud.set_wrapper_activated.connect(
                lambda active: self.wrapper_settings.add_wrapper("mangohud")
                if active else self.wrapper_settings.delete_wrapper("mangohud"))

        else:
            self.linux_settings_widget.setVisible(False)

        self.env_vars = EnvVars(self)
        self.game_settings_layout.addWidget(self.env_vars)

        if is_default:
            for i in range(4):  # remove some entries which are not supported by default
                self.launch_settings_layout.removeRow(0)

            self.cloud_group.deleteLater()
            self.load_settings("default")

    def save_line_edit(self, option, value):
        if value:
            config_helper.add_option(self.game.app_name, option, value)
        else:
            config_helper.remove_option(self.game.app_name, option)
        config_helper.save_config()

        if option == "wine_prefix":
            if self.game.supports_cloud_saves:
                self.compute_save_path()

    def update_combobox(self, i, option):
        if self.change:
            # remove section
            if i:
                if i == 1:
                    config_helper.add_option(self.game.app_name, option, "true")
                if i == 2:
                    config_helper.add_option(self.game.app_name, option, "false")
            else:
                config_helper.remove_option(self.game.app_name, option)
            config_helper.save_config()

    def load_settings(self, app_name):
        self.app_name = app_name
        self.wrapper_settings.load_settings(app_name)
        if platform.system() != "Windows":
            self.linux_settings.update_game(app_name)
            proton = self.wrapper_settings.wrappers.get("proton", "")
            if proton:
                proton = proton.text
            self.proton_settings.load_settings(app_name, proton)
            if proton:
                self.linux_settings.wine_groupbox.setEnabled(False)
            else:
                self.linux_settings.wine_groupbox.setEnabled(True)
        self.env_vars.update_game(app_name)


class LinuxAppSettings(LinuxSettings):
    def __init__(self):
        super(LinuxAppSettings, self).__init__()

    def update_game(self, app_name):
        self.name = app_name
        self.wine_prefix.setText(self.load_prefix())
        self.wine_exec.setText(self.load_setting(self.name, "wine_executable"))

        self.dxvk.load_settings(self.name)

        self.mangohud.load_settings(self.name)
