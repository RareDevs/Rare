import os
from typing import Callable, Optional, Set, Any, Tuple

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


def set_option(app_name: str, option: str, value: str) -> None:
    value = value.replace("%%", "%").replace("%", "%%")
    if not _config.has_section(app_name):
        _config[app_name] = {}
    _config.set(app_name, option, value)
    # save_config()


def set_boolean(app_name: str, option: str, value: bool) -> None:
    set_option(app_name, option, str(value).lower())


def set_envvar(app_name: str, envvar: str, value: str) -> None:
    set_option(f"{app_name}.env", envvar, value)


def remove_section(app_name: str) -> None:
    return
    # Disabled due to env variables implementation
    # if _config.has_section(app_name):
    #     _config.remove_section(app_name)
    #     save_config()


def remove_option(app_name: str, option: str) -> None:
    if _config.has_option(app_name, option):
        _config.remove_option(app_name, option)
    # if _config.has_section(app_name) and not _config[app_name]:
    #     _config.remove_section(app_name)
    # save_config()


def remove_envvar(app_name: str, option: str) -> None:
    remove_option(f"{app_name}.env", option)


def save_option(app_name: str, option: str, value: str) -> None:
    if value:
        set_option(app_name, option, value)
    else:
        remove_option(app_name, option)


def get_option(app_name: str, option: str, fallback: Any = None) -> str:
    return _config.get(app_name, option, fallback=fallback)


def get_option_fallback(app_name: str, option: str, fallback: Any = None) -> str:
    _option = get_option("default", option, fallback=fallback)
    _option = get_option(app_name, option, fallback=_option)
    return _option


def get_boolean(app_name: str, option: str, fallback: bool = False) -> bool:
    return _config.getboolean(app_name, option, fallback=fallback)


def save_envvar(app_name: str, option: str, value: str) -> None:
    if value:
        set_envvar(app_name, option, value)
    else:
        remove_envvar(app_name, option)


def get_envvar(app_name: str, option: str, fallback: Any = None) -> str:
    return get_option(f"{app_name}.env", option, fallback=fallback)


def get_envvar_fallback(app_name: str, option: str, fallback: Any = None) -> str:
    _option = _config.get("default.env", option, fallback=fallback)
    _option = _config.get(f'{app_name}.env', option, fallback=_option)
    return _option


def save_wine_prefix(app_name: str, value: str) -> None:
    save_envvar(app_name, "WINEPREFIX", value)
    save_option(app_name, "wine_prefix", value)


def get_wine_prefix(app_name: str, fallback: Any = None):
    _prefix = get_envvar(app_name, 'WINEPREFIX', fallback=fallback)
    _prefix = get_option(app_name, 'wine_prefix', fallback=_prefix)
    return _prefix


def get_wine_prefix_fallback(app_name: str, fallback: Any = None) -> str:
    _prefix = get_wine_prefix("default", fallback)
    _prefix = get_wine_prefix(app_name, fallback=_prefix)
    return _prefix


def save_proton_compatdata(app_name: str, value: str) -> None:
    save_envvar(app_name, "STEAM_COMPAT_DATA_PATH", value)


def get_proton_compatdata(app_name: Optional[str] = None, fallback: Any = None) -> str:
    _compat = get_envvar(app_name, "STEAM_COMPAT_DATA_PATH", fallback=fallback)
    # return os.path.join(_compat, "pfx") if _compat else fallback
    return _compat


def get_proton_compatdata_fallback(app_name: Optional[str] = None, fallback: Any = None) -> str:
    _compat = get_envvar_fallback(app_name, "STEAM_COMPAT_DATA_PATH", fallback=fallback)
    # return os.path.join(_compat, "pfx") if _compat else fallback
    return _compat


def get_wine_prefixes() -> Set[Tuple[str, str]]:
    _prefixes: Set[Tuple[str, str]] = set()
    for name, section in _config.items():
        pfx = section.get("WINEPREFIX") or section.get("wine_prefix")
        if pfx:
            _prefixes.update([(pfx, name[:-len(".env")] if name.endswith(".env") else name)])
    _prefixes = {(os.path.expanduser(p), n) for p, n in _prefixes}
    return {(p, n) for p, n in _prefixes if os.path.isdir(p)}


def get_proton_prefixes() -> Set[Tuple[str, str]]:
    _prefixes: Set[Tuple[str, str]] = set()
    for name, section in _config.items():
        pfx = os.path.join(compatdata, "pfx") if (compatdata := section.get("STEAM_COMPAT_DATA_PATH")) else ""
        if pfx:
            _prefixes.update([(pfx, name[:-len(".env")] if name.endswith(".env") else name)])
    _prefixes = {(os.path.expanduser(p), n) for p, n in _prefixes}
    return {(p, n) for p, n in _prefixes if os.path.isdir(p)}


def get_prefixes() -> Set[Tuple[str, str]]:
    return get_wine_prefixes().union(get_proton_prefixes())


def prefix_exists(pfx: str) -> bool:
    return os.path.isdir(pfx) and os.path.isfile(os.path.join(pfx, "user.reg"))


def get_prefix(app_name: str = "default") -> Optional[str]:
    _compat_path = _config.get(f"{app_name}.env", "STEAM_COMPAT_DATA_PATH", fallback=None)
    if _compat_path and prefix_exists(_compat_prefix := os.path.join(_compat_path, "pfx")):
        return _compat_prefix

    _wine_prefix = _config.get(f"{app_name}.env", "WINEPREFIX", fallback=None)
    _wine_prefix = _config.get(app_name, "wine_prefix", fallback=_wine_prefix)
    if _wine_prefix and prefix_exists(_wine_prefix):
        return _wine_prefix

    _compat_path = _config.get("default.env", "STEAM_COMPAT_DATA_PATH", fallback=None)
    if _compat_path and prefix_exists(_compat_prefix := os.path.join(_compat_path, "pfx")):
        return _compat_prefix

    _wine_prefix = _config.get("default.env", "WINEPREFIX", fallback=None)
    _wine_prefix = _config.get("default", "wine_prefix", fallback=_wine_prefix)
    if _wine_prefix and prefix_exists(_wine_prefix):
        return _wine_prefix

    return None
