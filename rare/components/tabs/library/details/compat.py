import platform as pf
from logging import getLogger

from PySide6.QtCore import Qt, Slot, QSignalBlocker
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QCheckBox, QFormLayout

from rare.components.tabs.settings.compat import CompatSettingsBase
from rare.components.tabs.settings.widgets.overlay import DxvkOverlaySettings, DxvkConfigSettings
from rare.components.tabs.settings.widgets.runner import RunnerSettingsBase
from rare.components.tabs.settings.widgets.wine import WineSettings
from rare.models.game import RareGame
from rare.utils import config_helper as config
from rare.utils.paths import compat_shaders_dir

if pf.system() in {"Linux", "FreeBSD"}:
    from rare.components.tabs.settings.widgets.proton import ProtonSettings
    from rare.components.tabs.settings.widgets.overlay import MangoHudSettings

logger = getLogger("LocalCompatSettings")


class LocalWineSettings(WineSettings):
    def load_settings(self, app_name):
        self.app_name = app_name


if pf.system() in {"Linux", "FreeBSD"}:
    class LocalProtonSettings(ProtonSettings):
        def load_settings(self, app_name: str):
            self.app_name = app_name

    class LocalMangoHudSettings(MangoHudSettings):
        def load_settings(self, app_name: str):
            self.app_name = app_name


class LocalRunnerSettings(RunnerSettingsBase):
    def __init__(self, parent=None):
        if pf.system() in {"Linux", "FreeBSD"}:
            super(LocalRunnerSettings, self).__init__(LocalWineSettings, LocalProtonSettings, parent=parent)
        else:
            super(LocalRunnerSettings, self).__init__(LocalWineSettings, parent=parent)

        self.rgame: RareGame = None

        font = self.font()
        font.setItalic(True)

        self.shader_cache_check = QCheckBox(self.tr("Use game-specific shader cache directory"), self)
        self.shader_cache_check.setFont(font)
        self.shader_cache_check.checkStateChanged.connect(self.__shader_cache_check_changed)

        form_layout = QFormLayout()
        form_layout.addRow(self.tr("Shader cache"), self.shader_cache_check)

        self.main_layout.addLayout(form_layout)

    def showEvent(self, a0: QShowEvent):
        if a0.spontaneous():
            return super().showEvent(a0)

        _ = QSignalBlocker(self.shader_cache_check)
        caches = all((config.get_envvar(self.app_name, envvar, False) for envvar in {
            "__GL_SHADER_DISK_CACHE_PATH", "MESA_SHADER_CACHE_DIR", "DXVK_STATE_CACHE_PATH", "VKD3D_SHADER_CACHE_PATH"
        }))
        self.shader_cache_check.setChecked(caches)

        return super().showEvent(a0)

    @Slot(Qt.CheckState)
    def __shader_cache_check_changed(self, state: Qt.CheckState):
        for envvar in {
            "__GL_SHADER_DISK_CACHE_PATH", "MESA_SHADER_CACHE_DIR", "DXVK_STATE_CACHE_PATH", "VKD3D_SHADER_CACHE_PATH"
        }:
            if state == Qt.CheckState.Checked:
                config.set_envvar(self.app_name, envvar, compat_shaders_dir(self.rgame.folder_name).as_posix())
            else:
                config.remove_envvar(self.app_name, envvar)
            self.environ_changed.emit(envvar)

    def load_settings(self, rgame: RareGame):
        self.rgame = rgame
        self.app_name = rgame.app_name
        self.wine.load_settings(rgame.app_name)
        if self.ctool:
            self.ctool.load_settings(rgame.app_name)


class LocalDxvkOverlaySettings(DxvkOverlaySettings):
    def load_settings(self, app_name: str):
        self.app_name = app_name


class LocalDxvkConfigSettings(DxvkConfigSettings):
    def load_settings(self, app_name: str):
        self.app_name = app_name


class LocalCompatSettings(CompatSettingsBase):
    def __init__(self, parent=None):
        if pf.system() in {"Linux", "FreeBSD"}:
            super(LocalCompatSettings, self).__init__(
                dxvk_overlay_widget=LocalDxvkOverlaySettings,
                dxvk_config_widget=LocalDxvkConfigSettings,
                runner_widget=LocalRunnerSettings,
                mangohud_widget=LocalMangoHudSettings,
                parent=parent
            )
        else:
            super(LocalCompatSettings, self).__init__(
                dxvk_overlay_widget=LocalDxvkOverlaySettings,
                dxvk_config_widget=LocalDxvkConfigSettings,
                runner_widget=LocalRunnerSettings,
                parent=parent
            )


    def load_settings(self, rgame: RareGame):
        self.set_title.emit(rgame.app_title)
        self.app_name = rgame.app_name
        self.runner.load_settings(rgame)
        if self.mangohud:
            self.mangohud.load_settings(rgame.app_name)
        self.dxvk_overlay.load_settings(rgame.app_name)
        self.dxvk_config.load_settings(rgame.app_name)
