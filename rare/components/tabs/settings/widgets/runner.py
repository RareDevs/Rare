import os.path
import platform as pf
from getpass import getuser
from typing import Type, TypeVar

from PySide6.QtCore import Qt, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QCheckBox, QFormLayout, QGroupBox, QHBoxLayout, QPushButton, QVBoxLayout

from rare.models.settings import RareAppSettings, app_settings
from rare.shared import RareCore
from rare.utils import config_helper as lgd_config

from .wine import WineSettings

if pf.system() in {"Linux", "FreeBSD"}:
    from .proton import ProtonSettings


class RunnerSettingsBase(QGroupBox):
    # str: option key
    environ_changed: Signal = Signal(str)
    # # bool: state, str: path
    # compat_tool_enabled: Signal = Signal(bool, str)

    def __init__(
        self,
        settings: RareAppSettings,
        rcore: RareCore,
        wine_widget: Type["WineSettings"],
        proton_widget: Type["ProtonSettings"] = None,
        parent=None,
    ):
        super().__init__(parent=parent)
        self.settings = settings
        self.app_name: str = "default"

        self.setTitle(self.tr("Compatibility"))

        self.main_layout = QVBoxLayout(self)

        self.wine = wine_widget(settings, rcore, self)
        self.wine.environ_changed.connect(self.environ_changed)
        self.main_layout.addWidget(self.wine)

        self.ctool = False
        if proton_widget is not None:
            self.ctool = proton_widget(rcore, self)
            self.ctool.environ_changed.connect(self.environ_changed)
            self.ctool.compat_tool_enabled.connect(self.wine.compat_tool_enabled)
            self.ctool.compat_path_changed.connect(self.wine.compat_path_changed)
            self.main_layout.addWidget(self.ctool)

        self.pfx_folder_button = QPushButton(self.tr("Open prefix folder"), self)
        self.pfx_folder_button.clicked.connect(self._open_pfx_folder)
        self.usr_folder_button = QPushButton(self.tr("Open user folder"), self)
        self.usr_folder_button.clicked.connect(self._open_usr_folder)
        self.winetricks_button = QPushButton(self.tr("Run winetricks"), self)

        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.pfx_folder_button)
        self.button_layout.addWidget(self.usr_folder_button)
        self.button_layout.addWidget(self.winetricks_button)
        self.button_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        font = self.font()
        font.setItalic(True)
        self.shader_cache_check = QCheckBox(self.tr("Use game-specific shader cache directory"), self)
        self.shader_cache_check.setFont(font)
        self.shader_cache_check.setChecked(self.settings.get_value(app_settings.local_shader_cache))
        self.shader_cache_check.checkStateChanged.connect(self._shader_cache_check_changed)

        self.form_layout = QFormLayout()
        self.form_layout.addRow(self.tr(""), self.button_layout)
        self.form_layout.addRow(self.tr("Shader cache"), self.shader_cache_check)
        self.form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.form_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignVCenter)
        self.main_layout.addLayout(self.form_layout)

    @Slot(Qt.CheckState)
    def _shader_cache_check_changed(self, state: Qt.CheckState):
        self.settings.set_value(app_settings.local_shader_cache, state != Qt.CheckState.Unchecked)

    @Slot()
    def _open_pfx_folder(self):
        QDesktopServices.openUrl(
            QUrl.fromLocalFile(lgd_config.get_wine_prefix_with_global(self.app_name))
        )

    @Slot()
    def _open_usr_folder(self):
        path = os.path.join(
            lgd_config.get_wine_prefix_with_global(self.app_name), "drive_c", "users", getuser()
        )
        if not os.path.exists(path):
            path = os.path.join(
                lgd_config.get_wine_prefix_with_global(self.app_name), "drive_c", "users", "steamuser"
            )
        QDesktopServices.openUrl(path)

    @Slot()
    def _run_winetricks(self):
        pass


RunnerSettingsType = TypeVar("RunnerSettingsType", bound=RunnerSettingsBase)
