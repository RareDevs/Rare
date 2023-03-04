import configparser
import os
import platform
import time
from argparse import Namespace
from itertools import chain
from logging import getLogger
from typing import Dict, Iterator, Callable, Tuple, Optional, List, Union

from PyQt5.QtCore import QObject, pyqtSignal, QSettings, pyqtSlot, QThreadPool
from legendary.lfs.eos import EOSOverlayApp
from legendary.models.game import Game, SaveGameFile

from rare.lgndr.core import LegendaryCore
from rare.models.game import RareGame, RareEosOverlay
from rare.models.signals import GlobalSignals
from .image_manager import ImageManager
from .workers import (
    QueueWorker,
    VerifyWorker,
    MoveWorker,
    SavesWorker,
    GamesWorker,
    NonAssetWorker,
    EntitlementsWorker,
    Win32Worker,
    MacOSWorker,
    FetchWorker,
)
from .workers.uninstall import uninstall_game
from .workers.worker import QueueWorkerInfo, QueueWorkerState

logger = getLogger("RareCore")


class RareCore(QObject):
    progress = pyqtSignal(int, str)
    completed = pyqtSignal()

    # lk: special case class attribute, this has to be here
    __instance: Optional['RareCore'] = None

    def __init__(self, args: Namespace):
        if self.__instance is not None:
            raise RuntimeError("RareCore already initialized")
        super(RareCore, self).__init__()
        self.__args: Optional[Namespace] = None
        self.__signals: Optional[GlobalSignals] = None
        self.__core: Optional[LegendaryCore] = None
        self.__image_manager: Optional[ImageManager] = None

        self.__games_fetched: bool = False
        self.__non_asset_fetched: bool = False
        self.__win32_fetched: bool = False
        self.__macos_fetched: bool = False
        self.__saves_fetched: bool = False
        self.__entitlements_fetched: bool = False

        self.args(args)
        self.signals(init=True)
        self.core(init=True)
        self.image_manager(init=True)

        self.settings = QSettings()

        self.queue_workers: List[QueueWorker] = []
        self.queue_threadpool = QThreadPool()
        self.queue_threadpool.setMaxThreadCount(2)

        self.__games: Dict[str, RareGame] = {}

        self.__eos_overlay_rgame = RareEosOverlay(self.__core, EOSOverlayApp)

        RareCore.__instance = self

    def enqueue_worker(self, rgame: RareGame, worker: QueueWorker):
        if isinstance(worker, VerifyWorker):
            rgame.state = RareGame.State.VERIFYING
        if isinstance(worker, MoveWorker):
            rgame.state = RareGame.State.MOVING
        rgame.set_worker(worker)
        worker.feedback.started.connect(self.__signals.application.update_statusbar)
        worker.feedback.finished.connect(lambda: rgame.set_worker(None))
        worker.feedback.finished.connect(lambda: self.queue_workers.remove(worker))
        worker.feedback.finished.connect(self.__signals.application.update_statusbar)
        self.queue_workers.append(worker)
        self.queue_threadpool.start(worker, priority=0)
        self.__signals.application.update_statusbar.emit()

    def dequeue_worker(self, worker: QueueWorker):
        rgame = self.__games[worker.worker_info().app_name]
        rgame.set_worker(None)
        self.queue_workers.remove(worker)
        self.__signals.application.update_statusbar.emit()

    def active_workers(self) -> Iterator[QueueWorker]:
        return list(filter(lambda w: w.state == QueueWorkerState.ACTIVE, self.queue_workers))

    def queued_workers(self) -> Iterator[QueueWorker]:
        return list(filter(lambda w: w.state == QueueWorkerState.QUEUED, self.queue_workers))

    def queue_info(self) -> List[QueueWorkerInfo]:
        return [w.worker_info() for w in self.queue_workers]

    @staticmethod
    def instance() -> 'RareCore':
        if RareCore.__instance is None:
            raise RuntimeError("Uninitialized use of RareCore")
        return RareCore.__instance

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

    def deleteLater(self) -> None:
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

        RareCore.__instance = None

        super(RareCore, self).deleteLater()

    def __validate_installed(self):
        filter_lambda = lambda rg: rg.is_installed and not (rg.is_dlc or rg.is_non_asset)
        length = len(list(self.__filter_games(filter_lambda)))
        for i, rgame in enumerate(self.__filter_games(filter_lambda)):
            self.progress.emit(
                int(i / length * 25) + 75,
                self.tr("Validating install for <b>{}</b>").format(rgame.app_title)
            )
            if not os.path.exists(rgame.igame.install_path):
                # lk: since install_path is lost anyway, set keep_files to True
                # lk: to avoid spamming the log with "file not found" errors
                for dlc in rgame.owned_dlcs:
                    if dlc.is_installed:
                        logger.info(f'Uninstalling DLC "{dlc.app_name}" ({dlc.app_title})...')
                        uninstall_game(self.__core, dlc.app_name, keep_files=True)
                        dlc.igame = None
                logger.info(
                    f'Removing "{rgame.app_title}" because "{rgame.igame.install_path}" does not exist...'
                )
                uninstall_game(self.__core, rgame.app_name, keep_files=True)
                logger.info(f"Uninstalled {rgame.app_title}, because no game files exist")
                rgame.igame = None
                continue
            # lk: games that don't have an override and can't find their executable due to case sensitivity
            # lk: will still erroneously require verification. This might need to be removed completely
            # lk: or be decoupled from the verification requirement
            if override_exe := self.__core.lgd.config.get(rgame.app_name, "override_exe", fallback=""):
                igame_executable = override_exe
            else:
                igame_executable = rgame.igame.executable
            # lk: Case-insensitive search for the game's executable (example: Brothers - A Tale of two Sons)
            executable_path = os.path.join(rgame.igame.install_path, igame_executable.replace("\\", "/").lstrip("/"))
            file_list = map(str.lower, os.listdir(os.path.dirname(executable_path)))
            if not os.path.basename(executable_path).lower() in file_list:
                rgame.igame.needs_verification = True
                self.__core.lgd.set_installed_game(rgame.app_name, rgame.igame)
                rgame.update_igame()
                logger.info(f"{rgame.app_title} needs verification")

    def get_game(self, app_name: str) -> Union[RareEosOverlay, RareGame]:
        if app_name == EOSOverlayApp.app_name:
            return self.__eos_overlay_rgame
        return self.__games[app_name]

    def __add_game(self, rgame: RareGame) -> None:
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

    def __create_or_update_rgame(self, game: Game) -> RareGame:
        if rgame := self.__games.get(game.app_name, False):
            logger.warning(f"{rgame.app_name} already present in {type(self).__name__}")
            logger.info(f"Updating Game for {rgame.app_name}")
            rgame.update_rgame()
        else:
            rgame = RareGame(self.__core, self.__image_manager, game)
        return rgame

    def __add_games_and_dlcs(self, games: List[Game], dlcs_dict: Dict[str, List]) -> None:
        for game in games:
            rgame = self.__create_or_update_rgame(game)
            if game_dlcs := dlcs_dict.get(rgame.game.catalog_item_id, False):
                for dlc in game_dlcs:
                    rdlc = self.__create_or_update_rgame(dlc)
                    # lk: plug dlc progress signals to the game's
                    rdlc.signals.progress.start.connect(rgame.signals.progress.start)
                    rdlc.signals.progress.update.connect(rgame.signals.progress.update)
                    rdlc.signals.progress.finish.connect(rgame.signals.progress.finish)
                    rgame.owned_dlcs.append(rdlc)
                    self.__add_game(rdlc)
            self.__add_game(rgame)

    @pyqtSlot(object, int)
    def handle_result(self, result: Tuple, res_type: int):
        status = ""
        if res_type == FetchWorker.Result.GAMES:
            games, dlc_dict = result
            self.__add_games_and_dlcs(games, dlc_dict)
            self.__games_fetched = True
            status = "Loaded games for Windows"
        if res_type == FetchWorker.Result.NON_ASSET:
            games, dlc_dict = result
            self.__add_games_and_dlcs(games, dlc_dict)
            self.__non_asset_fetched = True
            status = "Loaded games without assets"
        if res_type == FetchWorker.Result.WIN32:
            self.__win32_fetched = True
            status = "Loaded games for Windows (32bit)"
        if res_type == FetchWorker.Result.MACOS:
            self.__macos_fetched = True
            status = "Loaded games for MacOS"
        if res_type == FetchWorker.Result.SAVES:
            saves, _ = result
            for save in saves:
                self.__games[save.app_name].saves.append(save)
            self.__saves_fetched = True
            status = "Loaded save games"
        if res_type == FetchWorker.Result.ENTITLEMENTS:
            self.__core.lgd.entitlements = result
            self.__entitlements_fetched = True
            status = "Loaded game entitlements"
        logger.debug(f"Got API results for {FetchWorker.Result(res_type).name}")

        fetched = [
            self.__games_fetched,
            self.__non_asset_fetched,
            self.__win32_fetched,
            self.__macos_fetched,
            self.__saves_fetched,
            self.__entitlements_fetched,
        ]

        self.progress.emit(sum(fetched) * 10, status)

        if all(fetched):
            self.progress.emit(75, self.tr("Validating game installations"))
            self.__validate_installed()
            self.progress.emit(100, self.tr("Launching Rare"))
            logger.debug(f"Fetch time {time.time() - self.start_time} seconds")
            self.completed.emit()

    def fetch(self):
        self.__games_fetched: bool = False
        self.__non_asset_fetched: bool = False
        self.__win32_fetched: bool = False
        self.__macos_fetched: bool = False
        self.__saves_fetched: bool = False
        self.__entitlements_fetched: bool = False

        self.start_time = time.time()
        games_worker = GamesWorker(self.__core, self.__args)
        games_worker.signals.result.connect(self.handle_result)
        games_worker.signals.finished.connect(self.fetch_saves)
        games_worker.signals.finished.connect(self.fetch_extra)
        QThreadPool.globalInstance().start(games_worker)

    def fetch_saves(self):
        if not self.__args.offline:
            saves_worker = SavesWorker(self.__core, self.__args)
            saves_worker.signals.result.connect(self.handle_result)
            QThreadPool.globalInstance().start(saves_worker)
        else:
            self.__saves_fetched = True

    def fetch_extra(self):
        non_asset_worker = NonAssetWorker(self.__core, self.__args)
        non_asset_worker.signals.result.connect(self.handle_result)
        QThreadPool.globalInstance().start(non_asset_worker)

        entitlements_worker = EntitlementsWorker(self.__core, self.__args)
        entitlements_worker.signals.result.connect(self.handle_result)
        QThreadPool.globalInstance().start(entitlements_worker)

        if self.settings.value("win32_meta", False, bool) and not self.__win32_fetched:
            win32_worker = Win32Worker(self.__core, self.__args)
            win32_worker.signals.result.connect(self.handle_result)
            QThreadPool.globalInstance().start(win32_worker)
        else:
            self.__win32_fetched = True

        if self.settings.value("mac_meta", platform.system() == "Darwin", bool) and not self.__macos_fetched:
            macos_worker = MacOSWorker(self.__core, self.__args)
            macos_worker.signals.result.connect(self.handle_result)
            QThreadPool.globalInstance().start(macos_worker)
        else:
            self.__macos_fetched = True

    def load_pixmaps(self) -> None:
        """
        Load pixmaps for all games

        This exists here solely to fight signal and possibly threading issues.
        The initial image loading at startup should not be done in the RareGame class
        for two reasons. It will delay startup due to widget updates and the image
        might become availabe before the UI is brought up. In case of the second, we
        will get both a long queue of signals to be serviced and some of them might
        be not connected yet so the widget won't be updated. So do the loading here
        by calling this after the MainWindow has finished initializing.

        @return: None
        """
        QThreadPool.globalInstance().start(self.__load_pixmaps)

    def __load_pixmaps(self) -> None:
        # time.sleep(0.1)
        for rgame in self.__games.values():
            rgame.set_pixmap()
            # time.sleep(0.0001)

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

