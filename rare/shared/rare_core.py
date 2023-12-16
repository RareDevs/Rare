import configparser
import os
import platform
import time
from argparse import Namespace
from itertools import chain
from logging import getLogger
from typing import Dict, Iterator, Callable, Optional, List, Union, Iterable, Tuple, Set

from PyQt5.QtCore import QObject, pyqtSignal, QSettings, pyqtSlot, QThreadPool, QRunnable, QTimer
from legendary.lfs.eos import EOSOverlayApp
from legendary.models.game import Game, SaveGameFile
from requests import HTTPError

from rare.lgndr.core import LegendaryCore
from rare.models.base_game import RareSaveGame
from rare.models.game import RareGame, RareEosOverlay
from rare.models.signals import GlobalSignals
from .image_manager import ImageManager
from .workers import (
    QueueWorker,
    VerifyWorker,
    MoveWorker,
    FetchWorker,
    OriginWineWorker,
)
from .workers.uninstall import uninstall_game
from .workers.worker import QueueWorkerInfo, QueueWorkerState
from rare.utils import config_helper

logger = getLogger("RareCore")


class RareCore(QObject):
    progress = pyqtSignal(int, str)
    completed = pyqtSignal()
    # lk: these are unused but remain if case they are become relevant
    # completed_saves = pyqtSignal()
    # completed_origin = pyqtSignal()
    # completed_entitlements = pyqtSignal()

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

        self.__start_time = time.time()

        self.args(args)
        self.signals(init=True)
        self.core(init=True)
        config_helper.init_config_handler(self.__core)
        self.image_manager(init=True)

        self.settings = QSettings(self)

        self.queue_workers: List[QueueWorker] = []
        self.queue_threadpool = QThreadPool()
        self.queue_threadpool.setMaxThreadCount(2)

        self.__library: Dict[str, RareGame] = {}
        self.__eos_overlay = RareEosOverlay(self.__core, EOSOverlayApp)

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
        rgame = self.__library[worker.worker_info().app_name]
        rgame.set_worker(None)
        self.queue_workers.remove(worker)
        self.__signals.application.update_statusbar.emit()

    def active_workers(self) -> Iterable[QueueWorker]:
        return list(filter(lambda w: w.state == QueueWorkerState.ACTIVE, self.queue_workers))

    def queued_workers(self) -> Iterable[QueueWorker]:
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
                logger.warning("Config is corrupt: %s", e)
                if config_path := os.environ.get('LEGENDARY_CONFIG_PATH'):
                    path = config_path
                elif config_path := os.environ.get('XDG_CONFIG_HOME'):
                    path = os.path.join(config_path, 'legendary')
                else:
                    path = os.path.expanduser('~/.config/legendary')
                logger.info("Creating config in path: %s", config_path)
                with open(os.path.join(path, "config.ini"), "w") as config_file:
                    config_file.write("[Legendary]")
                self.__core = LegendaryCore()

            # Initialize sections if they don't exist
            for section in ["Legendary", "default", "default.env"]:
                if section not in self.__core.lgd.config.sections():
                    self.__core.lgd.config.add_section(section)

            # Set some platform defaults if unset
            def check_config(option: str, accepted: Set = None) -> bool:
                _exists = self.__core.lgd.config.has_option("Legendary", option)
                _value = self.__core.lgd.config.get("Legendary", option, fallback="")
                _accepted = _value in accepted if accepted is not None else True
                return _exists and bool(_value) and _accepted

            if not check_config("default_platform", {"Windows", "Win32", "Mac"}):
                self.__core.lgd.config.set("Legendary", "default_platform", self.__core.default_platform)
            if not check_config("install_dir"):
                self.__core.lgd.config.set(
                    "Legendary", "install_dir", self.__core.get_default_install_dir()
                )
            if not check_config("mac_install_dir"):
                self.__core.lgd.config.set(
                    "Legendary", "mac_install_dir", self.__core.get_default_install_dir(self.__core.default_platform)
                )
            # Always set these options
            # Avoid falling back to Windows games on macOS
            self.__core.lgd.config.set("Legendary", "install_platform_fallback", 'false')

            # workaround if egl sync enabled, but no programdata_path
            # programdata_path might be unset if logging in through the browser
            if self.__core.egl_sync_enabled:
                if self.__core.egl.programdata_path is None:
                    self.__core.lgd.config.remove_option("Legendary", "egl_sync")
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

        del self.__eos_overlay
        RareCore.__instance = None
        super(RareCore, self).deleteLater()

    def __validate_install(self, rgame: RareGame):
        if not os.path.exists(rgame.igame.install_path):
            # lk: since install_path is lost anyway, set keep_files to True
            # lk: to avoid spamming the log with "file not found" errors
            for dlc in rgame.owned_dlcs:
                if dlc.is_installed:
                    logger.info(f'Uninstalling DLC "{dlc.app_name}" ({dlc.app_title})...')
                    uninstall_game(self.__core, dlc.app_name, keep_files=True, keep_config=True)
                    dlc.igame = None
            logger.info(
                f'Removing "{rgame.app_title}" because "{rgame.igame.install_path}" does not exist...'
            )
            uninstall_game(self.__core, rgame.app_name, keep_files=True, keep_config=True)
            logger.info(f"Uninstalled {rgame.app_title}, because no game files exist")
            rgame.igame = None
            return
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
            return self.__eos_overlay
        return self.__library[app_name]

    def __add_game(self, rgame: RareGame) -> None:
        rgame.signals.download.enqueue.connect(self.__signals.download.enqueue)
        rgame.signals.download.dequeue.connect(self.__signals.download.dequeue)
        rgame.signals.game.install.connect(self.__signals.game.install)
        rgame.signals.game.installed.connect(self.__signals.game.installed)
        rgame.signals.game.uninstall.connect(self.__signals.game.uninstall)
        rgame.signals.game.uninstalled.connect(self.__signals.game.uninstalled)
        rgame.signals.game.finished.connect(self.__signals.application.update_tray)
        rgame.signals.game.finished.connect(lambda: self.__signals.discord_rpc.set_title.emit(""))
        self.__library[rgame.app_name] = rgame

    def __filter_games(self, condition: Callable[[RareGame], bool]) -> Iterator[RareGame]:
        return filter(condition, self.__library.values())

    def __create_or_update_rgame(self, game: Game) -> RareGame:
        if rgame := self.__library.get(game.app_name, False):
            logger.warning(f"{rgame.app_name} already present in {type(self).__name__}")
            logger.info(f"Updating Game for {rgame.app_name}")
            rgame.update_rgame()
        else:
            rgame = RareGame(self.__core, self.__image_manager, game)
            self.__add_game(rgame)
        return rgame

    def __add_games_and_dlcs(self, games: List[Game], dlcs_dict: Dict[str, List]) -> None:
        length = len(games)
        for idx, game in enumerate(games):
            rgame = self.__create_or_update_rgame(game)
            if game_dlcs := dlcs_dict.get(rgame.game.catalog_item_id, False):
                for dlc in game_dlcs:
                    rdlc = self.__create_or_update_rgame(dlc)
                    if rdlc not in rgame.owned_dlcs:
                        rgame.add_dlc(rdlc)
            # lk: since loading has to know about game state,
            # validate installation just adding each RareGamesu
            # TODO: this should probably be moved into RareGame
            if rgame.is_installed and not (rgame.is_dlc or rgame.is_non_asset):
                try:
                    self.__validate_install(rgame)
                except FileNotFoundError as e:
                    logger.info(f'Marking "{rgame.app_title}" as not installed because an exception has occurred...')
                    logger.error(e)
                    rgame.set_installed(False)
            self.progress.emit(int(idx/length * 80) + 20, self.tr("Loaded <b>{}</b>").format(rgame.app_title))

    @pyqtSlot(object, int)
    def __on_fetch_result(self, result: Tuple[List, Dict], res_type: int):
        logger.info(f"Got API results for {FetchWorker.Result(res_type).name}")
        self.progress.emit(15, self.tr("Preparing library"))
        self.__add_games_and_dlcs(*result)
        self.progress.emit(100, self.tr("Launching Rare"))
        logger.debug(f"Fetch time {time.time() - self.__start_time} seconds")
        QTimer.singleShot(100, self.__post_init)
        self.completed.emit()

    def fetch(self):
        self.__start_time = time.time()
        fetch_worker = FetchWorker(self.__core, self.__args)
        fetch_worker.signals.progress.connect(self.progress)
        fetch_worker.signals.result.connect(self.__on_fetch_result)
        QThreadPool.globalInstance().start(fetch_worker)

    def fetch_saves(self):
        def __fetch() -> None:
            start_time = time.time()
            saves_dict: Dict[str, List[SaveGameFile]] = {}
            try:
                saves_list = self.__core.get_save_games()
                for s in saves_list:
                    if s.app_name not in saves_dict.keys():
                        saves_dict[s.app_name] = [s]
                    else:
                        saves_dict[s.app_name].append(s)
                for app_name, saves in saves_dict.items():
                    if app_name not in self.__library.keys():
                        continue
                    self.__library[app_name].load_saves(saves)
            except (HTTPError, ConnectionError) as e:
                logger.error(f"Exception while fetching saves from EGS: {e}")
                return
            logger.debug(f"Saves: {len(saves_dict)}")
            logger.debug(f"Request saves: {time.time() - start_time} seconds")

        saves_worker = QRunnable.create(__fetch)
        QThreadPool.globalInstance().start(saves_worker)

    def fetch_entitlements(self) -> None:
        def __fetch() -> None:
            start_time = time.time()
            try:
                entitlements = self.__core.egs.get_user_entitlements()
                self.__core.lgd.entitlements = entitlements
                for game in self.__library.values():
                    game.grant_date()
            except (HTTPError, ConnectionError) as e:
                logger.error(f"Failed to retrieve user entitlements from EGS: {e}")
                return
            logger.debug(f"Entitlements: {len(list(entitlements))}")
            logger.debug(f"Request Entitlements: {time.time() - start_time} seconds")

        entitlements_worker = QRunnable.create(__fetch)
        QThreadPool.globalInstance().start(entitlements_worker)

    def resolve_origin(self) -> None:
        origin_worker = OriginWineWorker(self.__core, list(self.origin_games))
        QThreadPool.globalInstance().start(origin_worker)

    def __post_init(self) -> None:
        if not self.__args.offline:
            self.fetch_saves()
            self.fetch_entitlements()
        self.resolve_origin()

    @property
    def games_and_dlcs(self) -> Iterator[RareGame]:
        for app_name in self.__library:
            yield self.__library[app_name]

    @property
    def games(self) -> Iterator[RareGame]:
        return self.__filter_games(lambda game: not game.is_dlc)

    @property
    def installed_games(self) -> Iterator[RareGame]:
        return self.__filter_games(lambda game: game.is_installed and not game.is_dlc)

    @property
    def origin_games(self) -> Iterator[RareGame]:
        return self.__filter_games(lambda game: game.is_origin and not game.is_dlc)

    @property
    def ubisoft_games(self) -> Iterator[RareGame]:
        return self.__filter_games(lambda game: game.is_ubisoft and not game.is_dlc)

    @property
    def game_list(self) -> Iterator[Game]:
        for game in self.games:
            yield game.game

    @property
    def dlcs(self) -> Dict[str, set[RareGame]]:
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
    def non_asset_games(self) -> Iterator[RareGame]:
        return self.__filter_games(lambda game: game.is_non_asset)

    @property
    def unreal_engine(self) -> Iterator[RareGame]:
        return self.__filter_games(lambda game: game.is_unreal)

    @property
    def updates(self) -> Iterator[RareGame]:
        return self.__filter_games(lambda game: game.has_update)

    @property
    def saves(self) -> Iterator[RareSaveGame]:
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

