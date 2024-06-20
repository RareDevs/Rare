import os
import platform
import time
from configparser import ConfigParser
from logging import getLogger
from typing import Union, Iterable, List, Tuple, Dict

from PySide6.QtCore import Signal, QObject

from rare.lgndr.core import LegendaryCore
from rare.models.game import RareGame
from rare.models.pathspec import PathSpec
from rare.shared.wrappers import Wrappers
from rare.utils import config_helper as config
from rare.utils.misc import path_size, format_size
from .worker import Worker

if platform.system() == "Windows":
    # noinspection PyUnresolvedReferences
    import winreg  # pylint: disable=E0401
    from legendary.lfs import windows_helpers
else:
    from rare.utils.compat import utils as compat_utils, steam

logger = getLogger("WineResolver")


class WinePathResolver(Worker):
    class Signals(QObject):
        result_ready = Signal(str, str)

    def __init__(self, core: LegendaryCore, app_name: str, path: str):
        super(WinePathResolver, self). __init__()
        self.signals = WinePathResolver.Signals()
        self.core = core
        self.app_name = app_name
        self.path = path

    @staticmethod
    def _configure_process(core: LegendaryCore, app_name: str) -> Tuple[List, Dict]:
        tool: steam.CompatibilityTool = None

        if config.get_boolean(app_name, "no_wine"):
            wrappers = Wrappers()
            for w in wrappers.get_game_wrapper_list(app_name):
                if w.is_compat_tool:
                    for t in steam.find_tools():
                        if t.checksum == w.checksum:
                            tool = t
                            break

        cmd = core.get_app_launch_command(
            app_name,
            wrapper=tool.as_str(steam.SteamVerb.RUN_IN_PREFIX) if tool is not None else None,
            disable_wine=config.get_boolean(app_name, "no_wine")
        )
        env = core.get_app_environment(app_name, disable_wine=config.get_boolean(app_name, "no_wine"))
        # pylint: disable=E0606
        env = compat_utils.get_host_environment(env, silent=True)

        return cmd, env

    @staticmethod
    def _resolve_unix_path(cmd, env, path: str) -> str:
        logger.info("Resolving path '%s'", path)
        wine_path = compat_utils.resolve_path(cmd, env, path)
        logger.info("Resolved Wine path '%s'", wine_path)
        unix_path = compat_utils.convert_to_unix_path(cmd, env, wine_path)
        logger.info("Resolved Unix path '%s'", unix_path)
        return unix_path

    def run_real(self):
        command, environ = self._configure_process(self.core, self.app_name)
        if not (command and environ):
            logger.error("Cannot setup %s, missing infomation", {type(self).__name__})
            self.signals.result_ready.emit("", self.app_name)

        path = self._resolve_unix_path(command, environ, self.path)
        self.signals.result_ready.emit(path, self.app_name)
        return


class WineSavePathResolver(WinePathResolver):

    def __init__(self, core: LegendaryCore, rgame: RareGame):
        path = PathSpec(core, rgame.igame).resolve_egl_path_vars(rgame.raw_save_path)
        super(WineSavePathResolver, self).__init__(rgame.core, rgame.app_name, str(path))
        self.rgame = rgame

    def run_real(self):
        logger.info("Resolving save path for %s (%s)", self.rgame.app_title, self.rgame.app_name)
        command, environ = self._configure_process(self.core, self.rgame.app_name)
        if not (command and environ):
            logger.error("Cannot setup %s, missing infomation", {type(self).__name__})
            self.signals.result_ready.emit("", self.rgame.app_name)

        path = self._resolve_unix_path(command, environ, self.path)
        # Clean wine output
        # pylint: disable=E1136
        if os.path.exists(path):
            self.rgame.save_path = path
        self.signals.result_ready.emit(path, self.rgame.app_name)
        return


class OriginWineWorker(WinePathResolver):
    def __init__(self, core: LegendaryCore, games: Union[Iterable[RareGame], RareGame]):
        super(OriginWineWorker, self).__init__(core, "", "")
        self.__cache: dict[str, ConfigParser] = {}
        self.core = core
        self.games = [games] if isinstance(games, RareGame) else games

    def run_real(self) -> None:
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
                command, environ = self._configure_process(self.core, rgame.app_name)

                prefix = config.get_prefix(rgame.app_name)
                if not prefix:
                    return

                use_wine = True
                if not use_wine:
                    # lk: this is the original way of getting the path by parsing "system.reg"
                    reg = self.__cache.get(prefix, None) or compat_utils.read_registry("system.reg", prefix)
                    self.__cache[prefix] = reg

                    reg_path = reg_path.replace("SOFTWARE", "Software").replace("WOW6432Node", "Wow6432Node")
                    # lk: split and rejoin the registry path to avoid slash expansion
                    reg_path = "\\\\".join([x for x in reg_path.split("\\") if bool(x)])

                    install_dir = reg.get(reg_path, f'"{reg_key}"', fallback=None)
                else:
                    # lk: this is the alternative way of getting the path by using wine itself
                    install_dir = compat_utils.query_reg_key(command, environ, f"HKLM\\{reg_path}", reg_key)

                if install_dir:
                    logger.debug("Found Wine install directory %s", install_dir)
                    install_dir = compat_utils.convert_to_unix_path(command, environ, install_dir)
                    if install_dir:
                        logger.debug("Found Unix install directory %s", install_dir)
                    else:
                        logger.info("Could not find Unix install directory for '%s'", rgame.app_title)
                else:
                    logger.info("Could not find Wine install directory for '%s'", rgame.app_title)

            if install_dir:
                if os.path.isdir(install_dir):
                    install_size = path_size(install_dir)
                    rgame.set_origin_attributes(install_dir, install_size)
                    logger.info("Origin game '%s' (%s, %s)", rgame.app_title, install_dir, format_size(install_size))
                else:
                    logger.warning("Origin game '%s' (%s does not exist)", rgame.app_title, install_dir)
            else:
                logger.info("Origin game '%s' is not installed", rgame.app_title)
        logger.info("Origin worker finished in %ss", time.time() - t)
