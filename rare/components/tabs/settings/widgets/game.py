import platform as pf
from typing import Type

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QHideEvent
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    # QStackedWidget,
    QGroupBox,
    # QComboBox,
    # QFormLayout,
    # QLabel,
)

from rare.shared import LegendaryCoreSingleton
from rare.utils import config_helper as config
from rare.widgets.side_tab import SideTabContents
from .env_vars import EnvVars
from .launch import LaunchSettingsType
from .overlay import DxvkSettings

if pf.system() != "Windows":
    from .wine import WineSettings

if pf.system() in {"Linux", "FreeBSD"}:
    from .proton import ProtonSettings
    from .overlay import MangoHudSettings


class GameSettingsBase(QWidget, SideTabContents):

    def __init__(
        self,
        launch_widget: Type[LaunchSettingsType],
        dxvk_widget: Type[DxvkSettings],
        envvar_widget: Type[EnvVars],
        wine_widget: Type['WineSettings'] = None,
        proton_widget: Type['ProtonSettings'] = None,
        mangohud_widget: Type['MangoHudSettings'] = None,
        parent=None
    ):
        super(GameSettingsBase, self).__init__(parent=parent)

        self.core = LegendaryCoreSingleton()
        self.settings = QSettings(self)
        self.app_name: str = "default"

        self.launch = launch_widget(self)
        self.env_vars = envvar_widget(self)

        if pf.system() != "Windows":
            self.compat = QGroupBox(self.tr("Compatibility"), parent=self)
        #     self.compat_label = QLabel(self.tr("Runner"))
        #     self.compat_combo = QComboBox(self)
        #     self.compat_stack = QStackedWidget(self)

            self.compat_layout = QVBoxLayout(self.compat)
        #     self.compat_layout = QFormLayout(self.compat)
        #     self.compat_layout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.compat_label)
        #     self.compat_layout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.compat_combo)
        #     self.compat_layout.setWidget(1, QFormLayout.ItemRole.SpanningRole, self.compat_stack)
        #     self.compat_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        #
            self.wine = wine_widget(self)
            self.wine.environ_changed.connect(self.env_vars.reset_model)
            self.compat_layout.addWidget(self.wine)
        #     wine_index = self.compat_stack.addWidget(self.wine)
        #     self.compat_combo.addItem("Wine", wine_index)

            if pf.system() in {"Linux", "FreeBSD"}:
                self.proton_tool = proton_widget(self)
                self.proton_tool.environ_changed.connect(self.env_vars.reset_model)
                self.proton_tool.tool_enabled.connect(self.wine.tool_enabled)
                self.proton_tool.tool_enabled.connect(self.launch.tool_enabled)
                self.compat_layout.addWidget(self.proton_tool)
        #         proton_index = self.compat_stack.addWidget(self.proton_tool)
        #         self.compat_combo.addItem("Proton", proton_index)

        #     self.compat_combo.currentIndexChanged.connect(
        #         lambda: self.compat_stack.setCurrentIndex(self.compat_combo.currentData(Qt.ItemDataRole.UserRole))
        #     )

        self.dxvk = dxvk_widget(self)
        self.dxvk.environ_changed.connect(self.env_vars.reset_model)

        if pf.system() in {"Linux", "FreeBSD"}:
            self.mangohud = mangohud_widget(self)
            self.mangohud.environ_changed.connect(self.env_vars.reset_model)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.launch)
        if pf.system() != "Windows":
            self.main_layout.addWidget(self.compat)
        self.main_layout.addWidget(self.dxvk)
        if pf.system() in {"Linux", "FreeBSD"}:
            self.main_layout.addWidget(self.mangohud)
        self.main_layout.addWidget(self.env_vars)

        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    def hideEvent(self, a0: QHideEvent):
        if a0.spontaneous():
            return super().hideEvent(a0)
        config.save_config()
        return super().hideEvent(a0)
