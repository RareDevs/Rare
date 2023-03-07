import os
import platform
import subprocess
import time
from argparse import Namespace
from configparser import ConfigParser
from logging import getLogger
from typing import Union, Iterator

from PyQt5.QtCore import pyqtSignal, QObject

from rare.lgndr.core import LegendaryCore
from rare.models.game import RareGame
from rare.models.pathspec import PathSpec
from rare.utils.misc import read_registry, path_size, format_size
from .fetch import FetchWorker
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
        self.wine_env = os.environ.copy()
        self.wine_env.update(core.get_app_environment(app_name))
        self.wine_env["WINEDLLOVERRIDES"] = "winemenubuilder=d;mscoree=d;mshtml=d;"
        self.wine_env["DISPLAY"] = ""

        self.wine_binary = core.lgd.config.get(
            app_name, "wine_executable", fallback=core.lgd.config.get(
                "default", "wine_executable", fallback="wine"
            )
        )
        self.winepath_binary = os.path.join(os.path.dirname(self.wine_binary), "winepath")
        self.path = PathSpec(core, app_name).cook(path)

    def run_real(self):
        if "WINEPREFIX" not in self.wine_env or not os.path.exists(self.wine_env["WINEPREFIX"]):
            # pylint: disable=E1136
            self.signals.result_ready[str].emit("")
            return
        if not os.path.exists(self.wine_binary) or not os.path.exists(self.winepath_binary):
            # pylint: disable=E1136
            self.signals.result_ready[str].emit("")
            return
        path = self.path.strip().replace("/", "\\")
        # lk: if path does not exist form
        cmd = [self.wine_binary, "cmd", "/c", "echo", path]
        # lk: if path exists and needs a case-sensitive interpretation form
        # cmd = [self.wine_binary, 'cmd', '/c', f'cd {path} & cd']
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self.wine_env,
            shell=False,
            text=True,
        )
        out, err = proc.communicate()
        # Clean wine output
        out = out.strip().strip('"')
        proc = subprocess.Popen(
            [self.winepath_binary, "-u", out],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self.wine_env,
            shell=False,
            text=True,
        )
        out, err = proc.communicate()
        real_path = os.path.realpath(out.strip())
        # pylint: disable=E1136
        self.signals.result_ready[str].emit(real_path)
        return


class OriginWineWorker(FetchWorker):
    def __init__(self, core: LegendaryCore, args: Namespace, games: Union[Iterator[RareGame], RareGame]):
        super(OriginWineWorker, self).__init__(core, args)
        self.__cache: dict[str, ConfigParser] = {}
        if isinstance(games, RareGame):
            games = [games]
        self.games = games

    def run_real(self) -> None:
        t = time.time()
        for rgame in self.games:
            if not rgame.is_origin:
                continue

            reg_path: str = rgame.game.metadata \
                .get("customAttributes", {}) \
                .get("RegistryPath", {}).get("value", None)
            if not reg_path:
                continue

            if platform.system() == "Windows":
                install_dir = windows_helpers.query_registry_value(winreg.HKEY_LOCAL_MACHINE, reg_path, "Install Dir")
            else:
                wine_prefix = self.core.lgd.config.get(
                    rgame.app_name, "wine_prefix", fallback=self.core.lgd.config.get(
                        "default", "wine_prefix", fallback=os.path.expanduser("~/.wine")
                    )
                )
                reg = self.__cache.get(wine_prefix, None) or read_registry("system.reg", wine_prefix)
                self.__cache[wine_prefix] = reg

                reg_path = reg_path.replace("SOFTWARE", "Software").replace("WOW6432Node", "Wow6432Node")
                # lk: split and rejoin the registry path to avoid slash expansion
                reg_path = "\\\\".join([x for x in reg_path.split("\\") if bool(x)])

                install_dir = reg.get(reg_path, '"Install Dir"', fallback=None)
                if install_dir:
                    wine = self.core.lgd.config.get(
                        rgame.app_name, "wine_executable", fallback=self.core.lgd.config.get(
                            "default", "wine_executable", fallback="wine"
                        )
                    )
                    winepath = os.path.join(os.path.dirname(wine), "winepath")
                    wine_env = os.environ.copy()
                    wine_env.update(self.core.get_app_environment(rgame.app_name))
                    wine_env["WINEDLLOVERRIDES"] = "winemenubuilder=d;mscoree=d;mshtml=d;"
                    wine_env["DISPLAY"] = ""
                    install_dir = install_dir.strip().strip('"')
                    proc = subprocess.Popen(
                        [winepath, "-u", install_dir],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        env=wine_env,
                        shell=False,
                        text=True,
                    )
                    out, err = proc.communicate()
                    install_dir = os.path.realpath(out.strip())
            if install_dir:
                if os.path.exists(install_dir):
                    size = path_size(install_dir)
                    rgame.set_origin_attributes(install_dir, size)
                    logger.debug(f"Found Origin game {rgame.title} ({install_dir}, {format_size(size)})")
                else:
                    logger.warning(f"Found Origin game {rgame.title} ({install_dir} does not exist)")
        self.signals.result.emit((), FetchWorker.Result.ORIGIN)
        logger.info(f"Origin registry worker finished in {time.time() - t}s")
