from typing import Callable

from legendary.core import LegendaryCore
from legendary.utils.config import LGDConf

config: LGDConf = None
save_config: Callable[[], None] = None


def init_config_handler(core: LegendaryCore):
    global config, save_config
    config = core.lgd.config
    save_config = core.lgd.save_config


def add_option(app_name: str, option: str, value: str):
    value = value.replace("%%", "%").replace("%", "%%")
    if not config.has_section(app_name):
        config[app_name] = {}

    config.set(app_name, option, value)
    save_config()


def remove_option(app_name, option):
    if config.has_option(app_name, option):
        config.remove_option(app_name, option)

    if config.has_section(app_name) and not config[app_name]:
        config.remove_section(app_name)

    save_config()


def remove_section(app_name):
    if config.has_section(app_name):
        config.remove_section(app_name)
        save_config()
