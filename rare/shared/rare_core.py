import configparser
import os
from argparse import Namespace
from itertools import chain
from logging import getLogger
from typing import Optional, Dict, Iterator, Callable

from PyQt5.QtCore import QObject
from legendary.lfs.eos import EOSOverlayApp
from legendary.models.game import Game, SaveGameFile

from rare.lgndr.core import LegendaryCore
from rare.models.apiresults import ApiResults
from rare.models.game import RareGame, RareEosOverlay
from rare.models.signals import GlobalSignals
from .image_manager import ImageManager

logger = getLogger("RareCore")


class RareCore(QObject):
    _instance: Optional['RareCore'] = None

    def __init__(self, args: Namespace):
        if self._instance is not None:
            raise RuntimeError("RareCore already initialized")
        super(RareCore, self).__init__()
        self.__args: Optional[Namespace] = None
        self.__signals: Optional[GlobalSignals] = None
        self.__core: Optional[LegendaryCore] = None
        self.__image_manager: Optional[ImageManager] = None
        self.__api_results: Optional[ApiResults] = None

        self.args(args)
        self.signals(init=True)
        self.core(init=True)
        self.image_manager(init=True)

        self.__games: Dict[str, RareGame] = {}

        self.__eos_overlay_rgame = RareEosOverlay(self.__core, self.__image_manager, EOSOverlayApp)

        RareCore._instance = self

    @staticmethod
    def instance() -> 'RareCore':
        if RareCore._instance is None:
            raise RuntimeError("Uninitialized use of RareCore")
        return RareCore._instance

    def signals(self, init: bool = False) -> GlobalSignals:
        if self.__signals is None and not init:
            raise RuntimeError("Uninitialized use of GlobalSignalsSingleton")
        if self.__signals is not None and init:
            raise RuntimeError("GlobalSignals already initialized")
        if init:
            self.__signals = GlobalSignals()
        return self.__signals

    def args(self, args: Namespace = None) -> Optional[Namespace]:
        if self.__args is None and args is None:
            raise RuntimeError("Uninitialized use of ArgumentsSingleton")
        if self.__args is not None and args is not None:
            raise RuntimeError("Arguments already initialized")
        if args is not None:
            self.__args = args
        return self.__args

    def core(self, init: bool = False) -> LegendaryCore:
        if self.__core is None and not init:
            raise RuntimeError("Uninitialized use of LegendaryCoreSingleton")
        if self.__core is not None and init:
            raise RuntimeError("LegendaryCore already initialized")
        if init:
            try:
                self.__core = LegendaryCore()
            except configparser.MissingSectionHeaderError as e:
                logger.warning(f"Config is corrupt: {e}")
                if config_path := os.environ.get("XDG_CONFIG_HOME"):
                    path = os.path.join(config_path, "legendary")
                else:
                    path = os.path.expanduser("~/.config/legendary")
                with open(os.path.join(path, "config.ini"), "w") as config_file:
                    config_file.write("[Legendary]")
                self.__core = LegendaryCore()
            if "Legendary" not in self.__core.lgd.config.sections():
                self.__core.lgd.config.add_section("Legendary")
                self.__core.lgd.save_config()
            # workaround if egl sync enabled, but no programdata_path
            # programdata_path might be unset if logging in through the browser
            if self.__core.egl_sync_enabled:
                if self.__core.egl.programdata_path is None:
                    self.__core.lgd.config.remove_option("Legendary", "egl_sync")
                    self.__core.lgd.save_config()
                else:
                    if not os.path.exists(self.__core.egl.programdata_path):
                        self.__core.lgd.config.remove_option("Legendary", "egl_sync")
                        self.__core.lgd.save_config()
        return self.__core

    def image_manager(self, init: bool = False) -> ImageManager:
        if self.__image_manager is None and not init:
            raise RuntimeError("Uninitialized use of ImageManagerSingleton")
        if self.__image_manager is not None and init:
            raise RuntimeError("ImageManager already initialized")
        if self.__image_manager is None:
            self.__image_manager = ImageManager(self.signals(), self.core())
        return self.__image_manager

    def api_results(self, res: ApiResults = None) -> Optional[ApiResults]:
        if self.__api_results is None and res is None:
            raise RuntimeError("Uninitialized use of ApiResultsSingleton")
        if self.__api_results is not None and res is not None:
            raise RuntimeError("ApiResults already initialized")
        if res is not None:
            self.__api_results = res
        return self.__api_results

    def deleteLater(self) -> None:
        del self.__api_results
        self.__api_results = None

        self.__image_manager.deleteLater()
        del self.__image_manager
        self.__image_manager = None

        self.__core.exit()
        del self.__core
        self.__core = None

        self.__signals.deleteLater()
        del self.__signals
        self.__signals = None

        del self.__args
        self.__args = None

        RareCore._instance = None

        super(RareCore, self).deleteLater()

    def get_game(self, app_name: str) -> RareGame:
        if app_name == EOSOverlayApp.app_name:
            return self.__eos_overlay_rgame
        return self.__games[app_name]

    def add_game(self, rgame: RareGame) -> None:
        rgame.signals.download.enqueue.connect(self.__signals.download.enqueue)
        rgame.signals.download.dequeue.connect(self.__signals.download.dequeue)
        rgame.signals.game.install.connect(self.__signals.game.install)
        rgame.signals.game.installed.connect(self.__signals.game.installed)
        rgame.signals.game.uninstall.connect(self.__signals.game.uninstall)
        rgame.signals.game.uninstalled.connect(self.__signals.game.uninstalled)
        rgame.signals.game.finished.connect(self.__signals.application.update_tray)
        rgame.signals.game.finished.connect(lambda: self.__signals.discord_rpc.set_title.emit(""))
        self.__games[rgame.app_name] = rgame

    def __filter_games(self, condition: Callable[[RareGame], bool]) -> Iterator[RareGame]:
        return filter(condition, self.__games.values())

    @property
    def games_and_dlcs(self) -> Iterator[RareGame]:
        for app_name in self.__games:
            yield self.__games[app_name]

    @property
    def games(self) -> Iterator[RareGame]:
        return self.__filter_games(lambda game: not game.is_dlc)

    @property
    def installed_games(self) -> Iterator[RareGame]:
        return self.__filter_games(lambda game: game.is_installed and not game.is_dlc)

    @property
    def game_list(self) -> Iterator[Game]:
        for game in self.games:
            yield game.game

    @property
    def dlcs(self) -> Dict[str, Game]:
        """!
        RareGames that ARE DLCs themselves
        """
        return {game.game.catalog_item_id: game.owned_dlcs for game in self.has_dlcs}
        # return self.__filter_games(lambda game: game.is_dlc)

    @property
    def has_dlcs(self) -> Iterator[RareGame]:
        """!
        RareGames that HAVE DLCs associated with them
        """
        return self.__filter_games(lambda game: bool(game.owned_dlcs))

    @property
    def bit32_games(self) -> Iterator[RareGame]:
        return self.__filter_games(lambda game: game.is_win32)

    @property
    def mac_games(self) -> Iterator[RareGame]:
        return self.__filter_games(lambda game: game.is_mac)

    @property
    def no_asset_games(self) -> Iterator[RareGame]:
        return self.__filter_games(lambda game: game.is_non_asset)

    @property
    def unreal_engine(self) -> Iterator[RareGame]:
        return self.__filter_games(lambda game: game.is_unreal)

    @property
    def updates(self) -> Iterator[RareGame]:
        return self.__filter_games(lambda game: game.has_update)

    @property
    def saves(self) -> Iterator[SaveGameFile]:
        """!
        SaveGameFiles across games
        """
        return chain.from_iterable([game.saves for game in self.has_saves])

    @property
    def has_saves(self) -> Iterator[RareGame]:
        """!
        RareGames that have SaveGameFiles associated with them
        """
        return self.__filter_games(lambda game: bool(game.saves))

