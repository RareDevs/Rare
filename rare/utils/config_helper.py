import os
from typing import Callable, Optional, List, Set

from legendary.core import LegendaryCore
from legendary.models.config import LGDConf

_config: Optional[LGDConf] = None
_save_config: Optional[Callable[[], None]] = None


def init_config_handler(core: LegendaryCore):
    global _config, _save_config
    _config = core.lgd.config
    _save_config = core.lgd.save_config


def save_config():
    if _save_config is None:
        raise RuntimeError("Uninitialized use of config_helper")
    _save_config()


def add_option(app_name: str, option: str, value: str):
    value = value.replace("%%", "%").replace("%", "%%")
    if not _config.has_section(app_name):
        _config[app_name] = {}

    _config.set(app_name, option, value)
    save_config()


def remove_option(app_name, option):
    if _config.has_option(app_name, option):
        _config.remove_option(app_name, option)

    # if _config.has_section(app_name) and not _config[app_name]:
    #     _config.remove_section(app_name)

    save_config()


def remove_section(app_name):
    return
    # Disabled due to env variables implementation
    if _config.has_section(app_name):
        _config.remove_section(app_name)
        save_config()


def get_wine_prefixes() -> Set[str]:
    prefixes = ["~/.wine"]

    for name, section in _config.items():
        pfx = section.get("WINEPREFIX") or section.get("wine_prefix")
        if pfx:
            prefixes.append(pfx)

    return {prefix for prefix in prefixes if os.path.isdir(os.path.expanduser(prefix))}


def get_wine_prefix(app_name: Optional[str] = None) -> str:
    if app_name is None:
        prefix = "~/.wine"
        prefix = _config.get("default.env", "WINEPREFIX", fallback=prefix)
        prefix = _config.get("default", "wine_prefix", fallback=prefix)
    else:
        prefix = get_wine_prefix()
        prefix = _config.get(f'{app_name}.env', 'WINEPREFIX', fallback=prefix)
        prefix = _config.get(app_name, 'wine_prefix', fallback=prefix)
    return os.path.abspath(os.path.expanduser(prefix))
