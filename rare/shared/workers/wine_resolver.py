import os
import platform
import time
from configparser import ConfigParser
from logging import getLogger
from typing import Union, Iterable

from PyQt5.QtCore import pyqtSignal, QObject, QRunnable

import rare.utils.wine as wine
from rare.lgndr.core import LegendaryCore
from rare.models.game import RareGame
from rare.models.pathspec import PathSpec
from rare.utils.misc import path_size, format_size
from .worker import Worker

if platform.system() == "Windows":
    # noinspection PyUnresolvedReferences
    import winreg # pylint: disable=E0401
    from legendary.lfs import windows_helpers

logger = getLogger("WineResolver")


class WineResolver(Worker):
    class Signals(QObject):
        result_ready = pyqtSignal(str)

    def __init__(self, core: LegendaryCore, path: str, app_name: str):
        super(WineResolver, self).__init__()
        self.signals = WineResolver.Signals()
        self.wine_env = wine.environ(core, app_name)
        self.wine_exec = wine.wine(core, app_name)
        self.path = PathSpec(core, app_name).cook(path)

    def run_real(self):
        if "WINEPREFIX" not in self.wine_env or not os.path.exists(self.wine_env["WINEPREFIX"]):
            # pylint: disable=E1136
            self.signals.result_ready[str].emit("")
            return
        if not os.path.exists(self.wine_exec):
            # pylint: disable=E1136
            self.signals.result_ready[str].emit("")
            return
        path = wine.resolve_path(self.wine_exec, self.wine_env, self.path)
        # Clean wine output
        real_path = wine.convert_to_unix_path(self.wine_exec, self.wine_env, path)
        # pylint: disable=E1136
        self.signals.result_ready[str].emit(real_path)
        return


class OriginWineWorker(QRunnable):
    def __init__(self, core: LegendaryCore, games: Union[Iterable[RareGame], RareGame]):
        super(OriginWineWorker, self).__init__()
        self.__cache: dict[str, ConfigParser] = {}
        self.core = core
        if isinstance(games, RareGame):
            games = [games]
        self.games = games

    def run(self) -> None:
        t = time.time()

        for rgame in self.games:

            reg_path: str = rgame.game.metadata \
                .get("customAttributes", {}) \
                .get("RegistryPath", {}).get("value", None)
            if not reg_path:
                continue

            reg_key: str = rgame.game.metadata \
                .get("customAttributes", {}) \
                .get("RegistryKey", {}).get("value", None)
            if not reg_key:
                continue

            if platform.system() == "Windows":
                install_dir = windows_helpers.query_registry_value(winreg.HKEY_LOCAL_MACHINE, reg_path, reg_key)
            else:
                wine_env = wine.environ(self.core, rgame.app_name)
                wine_exec = wine.wine(self.core, rgame.app_name)

                use_wine = False
                if not use_wine:
                    # lk: this is the original way of getting the path by parsing "system.reg"
                    wine_prefix = wine.prefix(self.core, rgame.app_name)
                    reg = self.__cache.get(wine_prefix, None) or wine.read_registry("system.reg", wine_prefix)
                    self.__cache[wine_prefix] = reg

                    reg_path = reg_path.replace("SOFTWARE", "Software").replace("WOW6432Node", "Wow6432Node")
                    # lk: split and rejoin the registry path to avoid slash expansion
                    reg_path = "\\\\".join([x for x in reg_path.split("\\") if bool(x)])

                    install_dir = reg.get(reg_path, f'"{reg_key}"', fallback=None)
                else:
                    # lk: this is the alternative way of getting the path by using wine itself
                    install_dir = wine.query_reg_key(wine_exec, wine_env, f"HKLM\\{reg_path}", reg_key)

                if install_dir:
                    logger.debug("Found Wine install directory %s", install_dir)
                    install_dir = wine.convert_to_unix_path(wine_exec, wine_env, install_dir)
                    if install_dir:
                        logger.debug("Found Unix install directory %s", install_dir)
                    else:
                        logger.info("Could not find Unix install directory for %s", rgame.app_title)
                else:
                    logger.info("Could not find Wine install directory for %s", rgame.app_title)

            if install_dir:
                if os.path.isdir(install_dir):
                    install_size = path_size(install_dir)
                    rgame.set_origin_attributes(install_dir, install_size)
                    logger.info("Origin game %s (%s, %s)", rgame.app_title, install_dir, format_size(install_size))
                else:
                    logger.warning("Origin game %s (%s does not exist)", rgame.app_title, install_dir)
            else:
                logger.info("Origin game %s is not installed", rgame.app_title)
        logger.info("Origin worker finished in %ss", time.time() - t)
