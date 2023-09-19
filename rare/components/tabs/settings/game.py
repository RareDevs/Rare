import platform as pf
from logging import getLogger

from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QShowEvent
from PyQt5.QtWidgets import (
    QWidget,
    QLabel, QFormLayout
)

from components.tabs.settings.widgets.dxvk import DxvkSettings
from components.tabs.settings.widgets.mangohud import MangoHudSettings
from rare.components.tabs.settings.widgets.env_vars import EnvVars
from rare.components.tabs.settings.widgets.wine import LinuxSettings
from rare.components.tabs.settings.widgets.proton import ProtonSettings
from rare.components.tabs.settings.widgets.wrapper import WrapperSettings
from rare.shared import LegendaryCoreSingleton
from rare.ui.components.tabs.settings.game import Ui_GameSettings

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
        self.settings = QSettings(self)

        self.wrapper_settings = WrapperSettings(self)
        self.ui.launch_layout.setWidget(
            self.ui.launch_layout.getWidgetPosition(self.ui.wrapper_label)[0],
            QFormLayout.FieldRole,
            self.wrapper_settings
        )

        self.env_vars = EnvVars(self)
        # dxvk
        self.dxvk = DxvkSettings(self)
        self.dxvk.environ_changed.connect(self.env_vars.reset_model)
        self.dxvk.load_settings(self.app_name)

        self.mangohud = MangoHudSettings(self)
        self.mangohud.environ_changed.connect(self.environ_changed)
        self.mangohud.load_settings(self.name)

        if pf.system() != "Windows":
            self.linux_settings = LinuxAppSettings(self)
            self.ui.game_settings_layout.addWidget(self.linux_settings)

            self.linux_settings.mangohud.set_wrapper_activated.connect(
                lambda active: self.wrapper_settings.add_wrapper("mangohud")
                if active else self.wrapper_settings.delete_wrapper("mangohud"))
            self.linux_settings.environ_changed.connect(self.env_vars.reset_model)

            if pf.system() != "Darwin":
                self.proton_settings = ProtonSettings(self.linux_settings, self.wrapper_settings)
                self.linux_settings.ui.linux_settings_layout.insertWidget(0, self.proton_settings)
                self.proton_settings.environ_changed.connect(self.env_vars.reset_model)

            self.ui.game_settings_layout.setAlignment(Qt.AlignTop)

        self.ui.main_layout.addWidget(self.dxvk)
        self.ui.main_layout.addWidget(self.mangohud)
        self.ui.main_layout.addWidget(self.env_vars)

        if is_default:
            self.ui.launch_layout.removeRow(self.ui.skip_update_label)
            self.ui.launch_layout.removeRow(self.ui.offline_label)
            self.ui.launch_layout.removeRow(self.ui.launch_params_label)
            self.ui.launch_layout.removeRow(self.ui.override_exe_label)
            self.ui.launch_layout.removeRow(self.ui.pre_launch_label)
            self.load_settings("default")

    def load_settings(self, app_name):
        self.app_name = app_name
        self.wrapper_settings.load_settings(app_name)

        if pf.system() != "Windows":
            self.linux_settings.update_game(app_name)
            if pf.system() != "Darwin":
                proton = self.wrapper_settings.wrappers.get("proton", "")
                if proton:
                    proton = proton.text
                self.proton_settings.load_settings(app_name, proton)
            else:
                proton = ""
            self.linux_settings.ui.wine_groupbox.setDisabled(bool(proton))

        self.env_vars.update_game(app_name)
