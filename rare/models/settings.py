import locale
import platform as pf
from argparse import Namespace
from typing import Any, Optional, Type

from PySide6.QtCore import QSettings

from .enumerations import DiscordRPCMode, LibraryFilter, LibraryOrder, LibraryView


class Setting(Namespace):
    key: str
    default: Any
    dtype: Type

    def __len__(self):
        return len(self.__dict__)

    def __iter__(self):
        yield from self.__dict__.values()


# The key names are set to the existing option name
class Settings(Namespace):
    win32_meta = Setting(key="win32_meta", default=False, dtype=bool)
    macos_meta = Setting(key="macos_meta", default=pf.system() == "Darwin", dtype=bool)
    unreal_meta = Setting(key="unreal_meta", default=False, dtype=bool)
    exclude_non_asset = Setting(key="exclude_non_asset", default=False, dtype=bool)
    exclude_entitlements = Setting(key="exclude_entitlements", default=False, dtype=bool)

    language = Setting(key="language", default=locale.getlocale()[0], dtype=str)

    sys_tray_close = Setting(key="sys_tray", default=True, dtype=bool)
    sys_tray_start = Setting(key="sys_tray_start", default=False, dtype=bool)

    auto_update = Setting(key="auto_update", default=False, dtype=bool)
    auto_sync_cloud = Setting(key="auto_sync_cloud", default=False, dtype=bool)
    confirm_start = Setting(key="confirm_start", default=False, dtype=bool)
    restore_window = Setting(key="save_size", default=False, dtype=bool)
    window_width = Setting(key="window_width", default=1280, dtype=int)
    window_height = Setting(key="window_height", default=720, dtype=int)
    notification = Setting(key="notification", default=True, dtype=bool)
    log_games = Setting(key="show_console", default=pf.system() != "Windows", dtype=bool)

    color_scheme = Setting(key="color_scheme", default="", dtype=str)
    style_sheet = Setting(key="style_sheet", default="RareStyle", dtype=str)

    library_view = Setting(key="library_view", default=int(LibraryView.COVER), dtype=int)
    library_filter = Setting(
        key="library_filter",
        default=int(LibraryFilter.MAC if pf.system() == "Darwin" else LibraryFilter.ALL),
        dtype=int,
    )
    library_order = Setting(key="library_order", default=int(LibraryOrder.TITLE), dtype=int)

    discord_rpc_mode = Setting(key="discord_rpc_mode", default=int(DiscordRPCMode.GAME_ONLY), dtype=int)
    discord_rpc_game = Setting(key="discord_rpc_game", default=True, dtype=bool)
    discord_rpc_time = Setting(key="discord_rpc_time", default=True, dtype=bool)
    discord_rpc_os = Setting(key="discord_rpc_os", default=True, dtype=bool)

    local_shader_cache = Setting(key="local_shader_cache", default=False, dtype=bool)
    create_shortcut = Setting(key="create_shortcut", default=pf.system() == "Windows", dtype=bool)


app_settings = Settings()


class RareAppSettings(QSettings):
    __instance: Optional["RareAppSettings"] = None

    def __init__(self, parent=None):
        if RareAppSettings.__instance is not None:
            raise RuntimeError("RareSettings already initialized")
        super(RareAppSettings, self).__init__(parent)
        RareAppSettings.__instance = self

    @staticmethod
    def instance() -> "RareAppSettings":
        if RareAppSettings.__instance is None:
            raise RuntimeError("Uninitialized use of RareSettings")
        return RareAppSettings.__instance

    def get_value(self, option: Setting, prefix: str = None) -> Any:
        if prefix:
            return self.value(f"{prefix}/{option.key}", defaultValue=option.default, type=option.dtype)
        else:
            return self.value(option.key, defaultValue=option.default, type=option.dtype)

    def set_value(self, option: Setting, value: Any, prefix: str = None) -> None:
        if prefix:
            self.setValue(f"{prefix}/{option.key}", option.dtype(value))
        else:
            self.setValue(option.key, option.dtype(value))

    def rem_value(self, option: Setting, prefix: str = None) -> None:
        if prefix:
            self.remove(f"{prefix}/{option.key}")
        else:
            self.remove(option.key)

    def get_with_global(self, option: Setting, prefix: str) -> Any:
        _global = self.get_value(option, None)
        return self.value(f"{prefix}/{option.key}", defaultValue=_global, type=option.dtype)

    def set_with_global(self, option: Setting, value: Any, prefix: str) -> None:
        _global = self.get_value(option, None)
        if _global == option.dtype(value):
            self.rem_value(option, prefix)
        else:
            self.set_value(option, value, prefix)

    def deleteLater(self):
        RareAppSettings.__instance = None
        super(RareAppSettings, self).deleteLater()


__all__ = [
    "app_settings",
    "RareAppSettings",
    "LibraryFilter",
    "LibraryOrder",
    "LibraryView",
    "DiscordRPCMode",
]
