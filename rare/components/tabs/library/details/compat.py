import platform as pf
from logging import getLogger
from typing import Tuple

from PySide6.QtCore import QSignalBlocker, Qt, Slot
from PySide6.QtGui import QShowEvent

from rare.components.tabs.settings.compat import CompatSettingsBase
from rare.components.tabs.settings.widgets.overlay import (
    DxvkConfigSettings,
    DxvkHudSettings,
    DxvkNvapiDrsSettings,
)
from rare.components.tabs.settings.widgets.runner import RunnerSettingsBase
from rare.components.tabs.settings.widgets.wine import WineSettings
from rare.models.game import RareGame
from rare.models.settings import app_settings
from rare.shared import RareCore
from rare.utils import config_helper as config
from rare.utils import steam_grades
from rare.utils.paths import compat_shaders_dir, proton_compat_dir, wine_prefix_dir
from rare.widgets.indicator_edit import (
    ColumnCompleter,
    IndicatorLineEdit,
    IndicatorReasonsCommon,
)

if pf.system() in {"Linux", "FreeBSD"}:
    from rare.components.tabs.settings.widgets.overlay import MangoHudSettings
    from rare.components.tabs.settings.widgets.proton import ProtonSettings

logger = getLogger("LocalCompatSettings")


class LocalWineSettings(WineSettings):
    def load_settings(self, app_name):
        self.app_name = app_name


if pf.system() in {"Linux", "FreeBSD"}:

    class LocalProtonSettings(ProtonSettings):
        def load_settings(self, app_name: str):
            self.app_name = app_name

        def _get_compat_path(self, compat_location: ProtonSettings.CompatLocation):
            folder_name = "default"
            local_folder_name = RareCore.instance().get_game(self.app_name).folder_name
            if compat_location == ProtonSettings.CompatLocation.NONE:
                if wine_prefix_dir(local_folder_name).joinpath("system.reg").is_file():
                    compat_location = ProtonSettings.CompatLocation.ISOLATED
            if compat_location == ProtonSettings.CompatLocation.ISOLATED:
                folder_name = local_folder_name
            compat_path = proton_compat_dir(folder_name)
            return compat_path

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

        self.steam_appid_edit = IndicatorLineEdit(
            placeholder=self.tr("Use in case the SteamAppID was not found automatically"),
            edit_func=self.__steam_appid_edit_callback,
            save_func=self.__steam_appid_save_callback,
            parent=self,
        )
        self.__steam_appids, self.__steam_titles = steam_grades.load_steam_appids()
        self.steam_appid_edit.setCompleter(ColumnCompleter(items=self.__steam_appids.items()))
        self.form_layout.addRow(self.tr("Steam AppID"), self.steam_appid_edit)

    def showEvent(self, a0: QShowEvent):
        if a0.spontaneous():
            return super().showEvent(a0)
        _ = QSignalBlocker(self.shader_cache_check)
        is_local_cache_enabled = self.settings.get_with_global(app_settings.local_shader_cache, self.rgame.app_name)
        has_local_cache_path = bool(config.get_envvar(self.app_name, "STEAM_COMPAT_SHADER_PATH", False))
        self.shader_cache_check.setChecked(is_local_cache_enabled or has_local_cache_path)
        self.shader_cache_check.setChecked(is_local_cache_enabled or has_local_cache_path)
        _ = QSignalBlocker(self.steam_appid_edit)
        self.steam_appid_edit.setText(self.rgame.steam_appid if self.rgame.steam_appid else "")
        self.steam_appid_edit.setInfo(self.__steam_titles.get(self.rgame.steam_appid, ""))
        return super().showEvent(a0)

    def __steam_appid_edit_callback(self, text: str) -> Tuple[bool, str, int]:
        self.steam_appid_edit.setInfo("")
        if not text:
            return True, text, IndicatorReasonsCommon.UNDEFINED
        if text in self.__steam_appids.keys():
            return True, self.__steam_appids[text], IndicatorReasonsCommon.VALID
        if text in self.__steam_titles.keys():
            return True, text, IndicatorReasonsCommon.VALID
        else:
            return False, text, IndicatorReasonsCommon.GAME_NOT_EXISTS

    def __steam_appid_save_callback(self, text: str) -> None:
        self.steam_appid_edit.setInfo(self.__steam_titles.get(text, ""))
        if text == self.rgame.steam_appid:
            return
        self.rgame.steam_appid = text
        self.rgame.reset_steam_date()

    @Slot(Qt.CheckState)
    def _shader_cache_check_changed(self, state: Qt.CheckState):
        if checked := (state != Qt.CheckState.Unchecked):
            config.set_envvar(
                self.rgame.app_name,
                "STEAM_COMPAT_SHADER_PATH",
                compat_shaders_dir(self.rgame.folder_name).as_posix(),
            )
        else:
            config.remove_envvar(self.rgame.app_name, "STEAM_COMPAT_SHADER_PATH")
        self.settings.set_with_global(app_settings.local_shader_cache, checked, self.rgame.app_name)
        self.environ_changed.emit("STEAM_COMPAT_SHADER_PATH")

    def load_settings(self, rgame: RareGame):
        self.rgame = rgame
        self.app_name = rgame.app_name
        self.wine.load_settings(rgame.app_name)
        if self.ctool:
            self.ctool.load_settings(rgame.app_name)


class LocalDxvkHudSettings(DxvkHudSettings):
    def load_settings(self, app_name: str):
        self.app_name = app_name


class LocalDxvkConfigSettings(DxvkConfigSettings):
    def load_settings(self, app_name: str):
        self.app_name = app_name


class LocalDxvkNvapiDrsSettings(DxvkNvapiDrsSettings):
    def load_settings(self, app_name: str):
        self.app_name = app_name


class LocalCompatSettings(CompatSettingsBase):
    def __init__(self, parent=None):
        if pf.system() in {"Linux", "FreeBSD"}:
            super(LocalCompatSettings, self).__init__(
                dxvk_hud_widget=LocalDxvkHudSettings,
                dxvk_config_widget=LocalDxvkConfigSettings,
                dxvk_nvapi_drs_widget=LocalDxvkNvapiDrsSettings,
                runner_widget=LocalRunnerSettings,
                mangohud_widget=LocalMangoHudSettings,
                parent=parent,
            )
        else:
            super(LocalCompatSettings, self).__init__(
                dxvk_hud_widget=LocalDxvkHudSettings,
                dxvk_config_widget=LocalDxvkConfigSettings,
                dxvk_nvapi_drs_widget=LocalDxvkNvapiDrsSettings,
                runner_widget=LocalRunnerSettings,
                parent=parent,
            )

    def load_settings(self, rgame: RareGame):
        self.set_title.emit(rgame.app_title)
        self.app_name = rgame.app_name
        self.runner.load_settings(rgame)
        if self.mangohud:
            self.mangohud.load_settings(rgame.app_name)
        self.dxvk_hud.load_settings(rgame.app_name)
        self.dxvk_config.load_settings(rgame.app_name)
        self.dxvk_nvapi_drs.load_settings(rgame.app_name)
