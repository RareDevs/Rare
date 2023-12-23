import os
import platform
import time
from configparser import ConfigParser
from logging import getLogger
from typing import Union, Iterable, Mapping, List

from PyQt5.QtCore import pyqtSignal, QObject, QRunnable

from rare.lgndr.core import LegendaryCore
from rare.models.game import RareGame
from rare.models.pathspec import PathSpec
from rare.utils import config_helper as config
from rare.utils.misc import path_size, format_size
from .worker import Worker

if platform.system() == "Windows":
    # noinspection PyUnresolvedReferences
    import winreg  # pylint: disable=E0401
    from legendary.lfs import windows_helpers
else:
    from rare.utils import runners

logger = getLogger("WineResolver")


class WinePathResolver(Worker):
    class Signals(QObject):
        result_ready = pyqtSignal(str, str)

    def __init__(self, command: List[str], environ: Mapping, path: str):
        super(WinePathResolver, self). __init__()
        self.signals = WinePathResolver.Signals()
        self.command = command
        self.environ = environ
        self.path = path

    @staticmethod
    def _resolve_unix_path(cmd, env, path: str) -> str:
        logger.info("Resolving path '%s'", path)
        wine_path = runners.resolve_path(cmd, env, path)
        logger.debug("Resolved Wine path '%s'", path)
        unix_path = runners.convert_to_unix_path(cmd, env, wine_path)
        logger.debug("Resolved Unix path '%s'", unix_path)
        return unix_path

    def run_real(self):
        path = self._resolve_unix_path(self.command, self.environ, self.path)
        self.signals.result_ready.emit(path, "default")
        return


class WineSavePathResolver(WinePathResolver):

    def __init__(self, core: LegendaryCore, rgame: RareGame):
        cmd = core.get_app_launch_command(rgame.app_name)
        env = core.get_app_environment(rgame.app_name)
        env = runners.get_environment(env, silent=True)
        path = PathSpec(core, rgame.igame).resolve_egl_path_vars(rgame.raw_save_path)
        if not (cmd and env and path):
            raise RuntimeError(f"Cannot setup {type(self).__name__}, missing infomation")
        super(WineSavePathResolver, self).__init__(cmd, env, path)
        self.rgame = rgame

    def run_real(self):
        logger.info("Resolving save path for %s (%s)", self.rgame.app_title, self.rgame.app_name)
        path = self._resolve_unix_path(self.command, self.environ, self.path)
        # Clean wine output
        # pylint: disable=E1136
        if os.path.exists(path):
            self.rgame.save_path = path
        self.signals.result_ready.emit(path, self.rgame.app_name)
        return


class OriginWineWorker(QRunnable):
    def __init__(self, core: LegendaryCore, games: Union[Iterable[RareGame], RareGame]):
        super(OriginWineWorker, self).__init__()
        self.__cache: dict[str, ConfigParser] = {}
        self.core = core
        self.games = [games] if isinstance(games, RareGame) else games

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
                command = self.core.get_app_launch_command(rgame.app_name)
                environ = self.core.get_app_environment(rgame.app_name)
                environ = runners.get_environment(environ, silent=True)

                prefix = config.get_prefix(rgame.app_name)
                if not prefix:
                    return

                use_wine = False
                if not use_wine:
                    # lk: this is the original way of getting the path by parsing "system.reg"
                    reg = self.__cache.get(prefix, None) or runners.read_registry("system.reg", prefix)
                    self.__cache[prefix] = reg

                    reg_path = reg_path.replace("SOFTWARE", "Software").replace("WOW6432Node", "Wow6432Node")
                    # lk: split and rejoin the registry path to avoid slash expansion
                    reg_path = "\\\\".join([x for x in reg_path.split("\\") if bool(x)])

                    install_dir = reg.get(reg_path, f'"{reg_key}"', fallback=None)
                else:
                    # lk: this is the alternative way of getting the path by using wine itself
                    install_dir = runners.query_reg_key(command, environ, f"HKLM\\{reg_path}", reg_key)

                if install_dir:
                    logger.debug("Found Wine install directory %s", install_dir)
                    install_dir = runners.convert_to_unix_path(command, environ, install_dir)
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
