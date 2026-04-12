from typing import Type

from PySide6.QtCore import Qt
from PySide6.QtGui import QHideEvent
from PySide6.QtWidgets import QVBoxLayout, QWidget

from rare.models.settings import RareAppSettings
from rare.shared import RareCore
from rare.utils import config_helper as config
from rare.widgets.side_tab import SideTabContents

from .widgets.launch import LaunchSettingsBase, LaunchSettingsType
from .widgets.wrappers import WrapperSettings


class GameSettingsBase(QWidget, SideTabContents):
    def __init__(
        self,
        settings: RareAppSettings,
        rcore: RareCore,
        launch_widget: Type[LaunchSettingsType],
        parent=None,
    ):
        super(GameSettingsBase, self).__init__(parent=parent)
        self.implements_scrollarea = True

        self.settings = settings
        self.app_name: str = "default"

        self.launch = launch_widget(rcore, self)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.launch, stretch=0)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    def hideEvent(self, a0: QHideEvent):
        if a0.spontaneous():
            return super().hideEvent(a0)
        config.save_config()
        return super().hideEvent(a0)


class GlobalLaunchSettings(LaunchSettingsBase):
    def __init__(self, rcore: RareCore, parent=None):
        super(GlobalLaunchSettings, self).__init__(rcore, WrapperSettings, parent=parent)


class GlobalGameSettings(GameSettingsBase):
    def __init__(self, settings: RareAppSettings, rcore: RareCore, parent=None):
        super(GlobalGameSettings, self).__init__(
            settings, rcore, launch_widget=GlobalLaunchSettings, parent=parent
        )
