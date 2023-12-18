import platform as pf
from typing import Type

from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QHideEvent
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout
)

from rare.shared import LegendaryCoreSingleton
from rare.widgets.side_tab import SideTabContents
from rare.utils import config_helper as config
from .env_vars import EnvVars
from .launch import LaunchSettingsType
from .overlay import MangoHudSettings, DxvkSettings
from .proton import ProtonSettings
from .wine import WineSettings


class GameSettingsBase(QWidget, SideTabContents):

    def __init__(
        self,
        launch_widget: Type[LaunchSettingsType],
        wine_widget: Type[WineSettings],
        proton_widget: Type[ProtonSettings],
        dxvk_widget: Type[DxvkSettings],
        mangohud_widget: Type[MangoHudSettings],
        envvar_widget: Type[EnvVars],
        parent=None
    ):
        super(GameSettingsBase, self).__init__(parent=parent)

        self.core = LegendaryCoreSingleton()
        self.settings = QSettings(self)
        self.app_name: str = "default"

        self.launch = launch_widget(self)
        self.env_vars = envvar_widget(self)

        if pf.system() != "Windows":
            self.wine = wine_widget(self)
            self.wine.environ_changed.connect(self.env_vars.reset_model)

        if pf.system() == "Linux":
            self.proton_tool = proton_widget(self)
            self.proton_tool.environ_changed.connect(self.env_vars.reset_model)
            self.proton_tool.tool_enabled.connect(self.wine.tool_enabled)
            self.proton_tool.tool_enabled.connect(self.launch.tool_enabled)

            self.mangohud = mangohud_widget(self)
            self.mangohud.environ_changed.connect(self.env_vars.reset_model)

        self.dxvk = dxvk_widget(self)
        self.dxvk.environ_changed.connect(self.env_vars.reset_model)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.launch)
        if pf.system() != "Windows":
            self.main_layout.addWidget(self.wine)
        if pf.system() == "Linux":
            self.main_layout.addWidget(self.proton_tool)
            self.main_layout.addWidget(self.mangohud)
        self.main_layout.addWidget(self.dxvk)
        if pf.system() == "Linux":
            self.main_layout.addWidget(self.mangohud)
        self.main_layout.addWidget(self.env_vars)

        self.main_layout.setAlignment(Qt.AlignTop)

    def hideEvent(self, a0: QHideEvent):
        if a0.spontaneous():
            return super().hideEvent(a0)
        config.save_config()
        return super().hideEvent(a0)
