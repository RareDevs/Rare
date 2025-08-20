import platform as pf
from logging import getLogger
from typing import Type

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QHideEvent
from PySide6.QtWidgets import QWidget, QVBoxLayout

from rare.shared import LegendaryCoreSingleton
from rare.utils import config_helper as config
from rare.widgets.side_tab import SideTabContents
from rare.models.settings import RareAppSettings
from .widgets.overlay import DxvkHudSettings, DxvkConfigSettings, DxvkNvapiDrsSettings
from .widgets.runner import RunnerSettingsBase, RunnerSettingsType
from .widgets.wine import WineSettings

if pf.system() in {"Linux", "FreeBSD"}:
    from .widgets.proton import ProtonSettings
    from .widgets.overlay import MangoHudSettings

logger = getLogger("GlobalCompatSettings")


class CompatSettingsBase(QWidget, SideTabContents):
    # str: option key
    environ_changed: Signal = Signal(str)
    # bool: state
    tool_enabled: Signal = Signal(bool)

    def __init__(
        self,
        dxvk_hud_widget: Type[DxvkHudSettings],
        dxvk_config_widget: Type[DxvkConfigSettings],
        dxvk_nvapi_drs_widget: Type[DxvkNvapiDrsSettings],
        runner_widget: Type["RunnerSettingsType"],
        mangohud_widget: Type["MangoHudSettings"] = None,
        parent=None,
    ):
        super(CompatSettingsBase, self).__init__(parent=parent)

        self.core = LegendaryCoreSingleton()
        self.settings = RareAppSettings.instance()
        self.app_name: str = "default"

        self.runner = runner_widget(self)
        self.runner.environ_changed.connect(self.environ_changed)
        self.runner.tool_enabled.connect(self.tool_enabled)

        self.dxvk_hud = dxvk_hud_widget(self)
        self.dxvk_hud.environ_changed.connect(self.environ_changed)

        self.dxvk_config = dxvk_config_widget(self)
        self.dxvk_config.environ_changed.connect(self.environ_changed)

        self.dxvk_nvapi_drs = dxvk_nvapi_drs_widget(self)
        self.dxvk_nvapi_drs.environ_changed.connect(self.environ_changed)

        self.mangohud = False
        if mangohud_widget is not None:
            self.mangohud = mangohud_widget(self)
            self.mangohud.environ_changed.connect(self.environ_changed)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.runner)
        self.main_layout.addWidget(self.dxvk_hud)
        self.main_layout.addWidget(self.dxvk_config)
        self.main_layout.addWidget(self.dxvk_nvapi_drs)
        if mangohud_widget is not None:
            self.main_layout.addWidget(self.mangohud)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    def hideEvent(self, a0: QHideEvent):
        if a0.spontaneous():
            return super().hideEvent(a0)
        config.save_config()
        return super().hideEvent(a0)


class GlobalRunnerSettings(RunnerSettingsBase):
    def __init__(self, parent=None):
        if pf.system() in {"Linux", "FreeBSD"}:
            super(GlobalRunnerSettings, self).__init__(WineSettings, ProtonSettings, parent=parent)
        else:
            super(GlobalRunnerSettings, self).__init__(WineSettings, parent=parent)


class GlobalCompatSettings(CompatSettingsBase):
    def __init__(self, parent=None):
        if pf.system() in {"Linux", "FreeBSD"}:
            super(GlobalCompatSettings, self).__init__(
                dxvk_hud_widget=DxvkHudSettings,
                dxvk_config_widget=DxvkConfigSettings,
                dxvk_nvapi_drs_widget=DxvkNvapiDrsSettings,
                runner_widget=GlobalRunnerSettings,
                mangohud_widget=MangoHudSettings,
                parent=parent,
            )
        else:
            super(GlobalCompatSettings, self).__init__(
                dxvk_hud_widget=DxvkHudSettings,
                dxvk_config_widget=DxvkConfigSettings,
                dxvk_nvapi_drs_widget=DxvkNvapiDrsSettings,
                runner_widget=GlobalRunnerSettings,
                parent=parent,
            )
