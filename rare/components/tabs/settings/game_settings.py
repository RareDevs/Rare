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
from rare.ui.components.tabs.settings.game_settings import Ui_GameSettings

logger = getLogger("GameSettings")


class DefaultGameSettings(QWidget):
    # variable to no update when changing game
    change = False
    app_name: str

    def __init__(self, is_default, parent=None):
        super(DefaultGameSettings, self).__init__(parent=parent)
        self.ui = Ui_GameSettings()
        self.ui.setupUi(self)
        self.core = LegendaryCoreSingleton()
        self.settings = QSettings()

        self.wrapper_settings = WrapperSettings()

        self.ui.launch_settings_group.layout().addRow(
            QLabel("Wrapper"), self.wrapper_settings
        )

        self.env_vars = EnvVars(self)
        self.ui.game_settings_layout.addWidget(self.env_vars)

        if platform.system() != "Windows":
            self.linux_settings = LinuxAppSettings()
            self.proton_settings = ProtonSettings(self.linux_settings, self.wrapper_settings)
            self.ui.proton_layout.addWidget(self.proton_settings)

            # FIXME: Remove the spacerItem and margins from the linux settings
            # FIXME: This should be handled differently at soem point in the future
            # NOTE: specerItem has been removed
            self.linux_settings.layout().setContentsMargins(0, 0, 0, 0)
            # FIXME: End of FIXME
            self.ui.linux_settings_layout.addWidget(self.linux_settings)
            self.ui.linux_settings_layout.setAlignment(Qt.AlignTop)

            self.ui.game_settings_layout.setAlignment(Qt.AlignTop)

            self.linux_settings.mangohud.set_wrapper_activated.connect(
                lambda active: self.wrapper_settings.add_wrapper("mangohud")
                if active else self.wrapper_settings.delete_wrapper("mangohud"))
            self.linux_settings.environ_changed.connect(self.env_vars.reset_model)
            self.proton_settings.environ_changed.connect(self.env_vars.reset_model)

        else:
            self.ui.linux_settings_widget.setVisible(False)

        if is_default:
            self.ui.launch_settings_layout.removeRow(self.ui.skip_update)
            self.ui.launch_settings_layout.removeRow(self.ui.offline)
            self.ui.launch_settings_layout.removeRow(self.ui.launch_params)

            self.load_settings("default")

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
                self.linux_settings.ui.wine_groupbox.setEnabled(False)
            else:
                self.linux_settings.ui.wine_groupbox.setEnabled(True)
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
