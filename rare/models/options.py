import locale
import platform as pf
from argparse import Namespace
from typing import Any, Type, Optional

from PySide6.QtCore import QSettings

from .enumerations import LibraryFilter, LibraryOrder, LibraryView, DiscordRPCMode

class Value(Namespace):
    key: str
    default: Any
    dtype: Type

    def __len__(self):
        return len(self.__dict__)

    def __iter__(self):
        yield from self.__dict__.values()


# They key names are set to the existing option name
class RareSettings:
    win32_meta = Value(key="win32_meta", default=False, dtype=bool)
    macos_meta = Value(key="macos_meta", default=pf.system() == "Darwin", dtype=bool)
    unreal_meta = Value(key="unreal_meta", default=False, dtype=bool)
    exclude_non_asset = Value(key="exclude_non_asset", default=False, dtype=bool)
    exclude_entitlements = Value(key="exclude_entitlements", default=False, dtype=bool)

    language = Value(key="language", default=locale.getlocale()[0], dtype=str)

    sys_tray_close = Value(key="sys_tray", default=True, dtype=bool)
    sys_tray_start = Value(key="sys_tray_start", default=False, dtype=bool)

    auto_update = Value(key="auto_update", default=False, dtype=bool)
    auto_sync_cloud = Value(key="auto_sync_cloud", default=False, dtype=bool)
    confirm_start = Value(key="confirm_start", default=False, dtype=bool)
    restore_window = Value(key="save_size", default=False, dtype=bool)
    window_width = Value(key="window_width", default=1280, dtype=int)
    window_height = Value(key="window_height", default=720, dtype=int)
    notification = Value(key="notification", default=True, dtype=bool)
    log_games = Value(key="show_console", default=False, dtype=bool)

    color_scheme = Value(key="color_scheme", default="", dtype=str)
    style_sheet = Value(key="style_sheet", default="RareStyle", dtype=str)

    library_view = Value(key="library_view", default=int(LibraryView.COVER), dtype=int)
    library_filter = Value(
        key="library_filter",
        default=int(LibraryFilter.MAC if pf.system() == "Darwin" else LibraryFilter.ALL), dtype=int
    )
    library_order = Value(key="library_order", default=int(LibraryOrder.TITLE), dtype=int)

    discord_rpc_mode = Value(key="discord_rpc_mode", default=int(DiscordRPCMode.GAME_ONLY), dtype=int)
    discord_rpc_game = Value(key="discord_rpc_game", default=True, dtype=bool)
    discord_rpc_time = Value(key="discord_rpc_time", default=True, dtype=bool)
    discord_rpc_os = Value(key="discord_rpc_os", default=True, dtype=bool)

    local_shader_cache = Value(key="local_shader_cache", default=False, dtype=bool)

    @staticmethod
    def get_value(settings: QSettings, option: Value, prefix: str = None):
        if prefix:
            return settings.value(f"{prefix}/{option.key}", defaultValue=option.default, type=option.dtype)
        else:
            return settings.value(option.key, defaultValue=option.default, type=option.dtype)

    @staticmethod
    def set_value(settings: QSettings, option: Value, value: Any, prefix: str = None):
        if prefix:
            settings.setValue(f"{prefix}/{option.key}", option.dtype(value))
        else:
            settings.setValue(option.key, option.dtype(value))

    @staticmethod
    def get_with_global(settings: QSettings, option: Value, prefix: str):
        _global = RareSettings.get_value(settings, option, None)
        return settings.value(f"{prefix}/{option.key}", defaultValue=_global, type=option.dtype)

    @staticmethod
    def set_with_global(settings: QSettings, option: Value, value: Any, prefix: str):
        _global = RareSettings.get_value(settings, option, None)
        if _global == option.dtype(value):
            settings.remove(f"{prefix}/{option.key}")
        else:
            RareSettings.set_value(settings, option, value, prefix)


options = RareSettings()


__all__ = ['options', 'LibraryFilter', 'LibraryOrder', 'LibraryView', 'DiscordRPCMode']
