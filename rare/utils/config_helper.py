from typing import Callable, Optional

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
    if _config.has_section(app_name):
        _config.remove_section(app_name)
        save_config()
