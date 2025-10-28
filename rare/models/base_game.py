from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from logging import getLogger
from typing import List, Optional, Tuple

from legendary.lfs import eos
from legendary.models.game import Game, InstalledGame, SaveGameFile, SaveGameStatus
from legendary.utils.selective_dl import get_sdl_appname
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal

from rare.lgndr.core import LegendaryCore
from rare.models.install import InstallOptionsModel, UninstallOptionsModel
from rare.models.settings import RareAppSettings, app_settings

logger = getLogger("RareGameBase")


@dataclass
class RareSaveGame:
    file: Optional[SaveGameFile]
    status: SaveGameStatus = SaveGameStatus.NO_SAVE
    dt_local: Optional[datetime] = None
    dt_remote: Optional[datetime] = None
    description: Optional[str] = ""


class RareGameSignals(QObject):
    class Progress(QObject):
        start = Signal()
        update = Signal(int)
        finish = Signal(bool)

    class Widget(QObject):
        update = Signal()

    class Download(QObject):
        enqueue = Signal(str)
        dequeue = Signal(str)

    class Game(QObject):
        install = Signal(InstallOptionsModel)
        installed = Signal(str)
        uninstall = Signal(UninstallOptionsModel)
        uninstalled = Signal(str)
        launched = Signal(str)
        finished = Signal(str)

    def __init__(self, /):
        super(RareGameSignals, self).__init__()
        self.progress = RareGameSignals.Progress()
        self.widget = RareGameSignals.Widget()
        self.download = RareGameSignals.Download()
        self.game = RareGameSignals.Game()


class RareGameBase(QObject):
    class State(IntEnum):
        IDLE = 0
        RUNNING = 1
        DOWNLOADING = 2
        VERIFYING = 3
        MOVING = 4
        UNINSTALLING = 5
        SYNCING = 6

    def __init__(self, legendary_core: LegendaryCore, game: Game):
        super(RareGameBase, self).__init__()
        self.signals = RareGameSignals()
        self.core = legendary_core
        self.game: Game = game
        self.igame: InstalledGame = None
        self._state = RareGameBase.State.IDLE

    @property
    def state(self) -> "RareGameBase.State":
        return self._state

    @state.setter
    def state(self, state: "RareGameBase.State"):
        if state != self._state:
            self._state = state
            self.signals.widget.update.emit()

    @property
    def is_idle(self):
        return self.state == RareGameBase.State.IDLE

    @property
    def app_name(self) -> str:
        return self.game.app_name

    @property
    def app_title(self) -> str:
        return self.game.app_title

    @property
    @abstractmethod
    def is_installed(self) -> bool:
        pass

    @abstractmethod
    def set_installed(self, installed: bool) -> None:
        pass

    @property
    def platforms(self) -> Tuple:
        """!
        @brief Property that holds the platforms a game is available for

        @return Tuple
        """
        return tuple(self.game.asset_infos.keys())

    @property
    def default_platform(self) -> str:
        return self.core.default_platform if self.core.default_platform in self.platforms else "Windows"

    @property
    def is_mac(self) -> bool:
        """!
        @brief Property to report if Game has a mac version

        @return bool
        """
        return "Mac" in self.game.asset_infos.keys()

    @property
    def is_win32(self) -> bool:
        """!
        @brief Property to report if Game is 32bit game

        @return bool
        """
        return "Win32" in self.game.asset_infos.keys()

    @property
    def is_origin(self) -> bool:
        """!
        @brief Property to report if a Game is an Origin game

        Legendary and by extenstion Rare can't launch Origin games directly,
        it just launches the Origin client and thus requires a bit of a special
        handling to let the user know.

        @return bool If the game is an Origin game
        """
        return self.game.third_party_store in {"Origin", "the EA app"}

    @property
    def is_android(self) -> bool:
        release_info = self.game.metadata.get("releaseInfo")
        if not release_info:
            return False
        return "Android" in release_info[0]["platform"]

    @property
    def is_overlay(self):
        return self.app_name == eos.EOSOverlayApp.app_name

    @property
    def is_dlc(self) -> bool:
        """!
        @brief Property to report if Game is a dlc

        @return bool
        """
        return self.game.is_dlc

    @property
    def is_launchable_addon(self) -> bool:
        # lk: the attribute doesn't exist in the currently released version
        # FIXME: remove after legendary >= 0.20.35
        try:
            return self.game.is_launchable_addon
        except AttributeError:
            return False

    @property
    def sdl_name(self) -> Optional[str]:
        return get_sdl_appname(self.app_name)

    @property
    def version(self) -> str:
        """!
        @brief Reports the currently installed version of the Game

        If InstalledGame reports the currently installed version, which might be
        different from the remote version available from EGS. For not installed Games
        it reports the already known version.

        @return str The current version of the game
        """
        return self.igame.version if self.igame is not None else self.game.app_version(self.default_platform)

    @property
    def install_path(self) -> Optional[str]:
        if self.igame:
            return self.igame.install_path
        return None


class RareGameSlim(RareGameBase):
    def __init__(self, settings: RareAppSettings, legendary_core: LegendaryCore, game: Game):
        super(RareGameSlim, self).__init__(legendary_core, game)
        self.settings = settings
        # None if origin or not installed
        self.igame: Optional[InstalledGame] = self.core.get_installed_game(game.app_name)
        self.saves: List[RareSaveGame] = []

    @property
    def is_installed(self) -> bool:
        if self.is_origin:
            return True
        return self.igame is not None

    def set_installed(self, installed: bool) -> None:
        pass

    @property
    def auto_sync_saves(self):
        auto_sync_cloud = self.settings.get_with_global(app_settings.auto_sync_cloud, self.app_name)
        return self.supports_cloud_saves and auto_sync_cloud

    @property
    def save_path(self) -> Optional[str]:
        if self.igame is not None:
            return self.igame.save_path
        return None

    @property
    def latest_save(self) -> RareSaveGame:
        if self.saves:
            saves = sorted(self.saves, key=lambda s: s.file.datetime, reverse=True)
            return saves[0]
        return RareSaveGame(None)

    @property
    def save_game_state(
        self,
    ) -> Tuple[SaveGameStatus, Tuple[Optional[datetime], Optional[datetime]]]:
        if self.save_path:
            latest = self.latest_save
            # lk: if the save path wasn't known at startup, dt_local will be None
            # In that case resolve the save again before returning
            latest.status, (latest.dt_local, latest.dt_remote) = self.core.check_savegame_state(
                self.save_path, self.igame.save_timestamp, latest.file
            )
            return latest.status, (latest.dt_local, latest.dt_remote)
        return SaveGameStatus.NO_SAVE, (None, None)

    def upload_saves(self, thread=True):
        if not self.supports_cloud_saves:
            return
        if self.state == RareGameSlim.State.SYNCING:
            logger.error(f"{self.app_title} is already syncing")
            return

        status, (dt_local, dt_remote) = self.save_game_state
        if status == SaveGameStatus.NO_SAVE or not dt_local:
            logger.warning("Can't upload non existing save")
            return

        def _upload():
            logger.info(f"Uploading save for {self.app_title}")
            self.state = RareGameSlim.State.SYNCING
            self.core.upload_save(self.app_name, self.igame.save_path, dt_local)
            self.state = RareGameSlim.State.IDLE
            self.update_saves()

        if thread:
            worker = QRunnable.create(_upload)
            QThreadPool.globalInstance().start(worker)
        else:
            _upload()

    def download_saves(self, thread=True):
        if not self.supports_cloud_saves:
            return
        if self.state == RareGameSlim.State.SYNCING:
            logger.error(f"{self.app_title} is already syncing")
            return

        status, (dt_local, dt_remote) = self.save_game_state
        if status == SaveGameStatus.NO_SAVE or not dt_remote:
            logger.error("Can't download non existing save")
            return

        def _download():
            logger.info(f"Downloading save for {self.app_title}")
            self.state = RareGameSlim.State.SYNCING
            self.core.download_saves(self.app_name, self.latest_save.file.manifest_name, self.save_path)
            self.state = RareGameSlim.State.IDLE
            self.update_saves()

        if thread:
            worker = QRunnable.create(_download)
            QThreadPool.globalInstance().start(worker)
        else:
            _download()

    def load_saves(self, saves: List[SaveGameFile]):
        """Use only in a thread"""
        self.saves.clear()
        for save in saves:
            if self.save_path:
                status, (dt_local, dt_remote) = self.core.check_savegame_state(self.save_path, self.igame.save_timestamp, save)
                rsave = RareSaveGame(save, status, dt_local, dt_remote)
            else:
                rsave = RareSaveGame(
                    save,
                    SaveGameStatus.SAME_AGE,
                    dt_local=None,
                    dt_remote=save.datetime,
                )
            self.saves.append(rsave)
        self.signals.widget.update.emit()

    def update_saves(self):
        """Use only in a thread"""
        saves = self.core.get_save_games(self.app_name)
        self.load_saves(saves)

    @property
    def is_save_up_to_date(self):
        if not self.saves:
            return True
        status, (_, _) = self.save_game_state
        return status in {SaveGameStatus.SAME_AGE, SaveGameStatus.NO_SAVE}

    @property
    def raw_save_path(self) -> str:
        if self.game.supports_cloud_saves:
            return self.game.metadata.get("customAttributes", {}).get("CloudSaveFolder", {}).get("value")
        return ""

    @property
    def raw_save_path_mac(self) -> str:
        if self.game.supports_mac_cloud_saves:
            return self.game.metadata.get("customAttributes", {}).get("CloudSaveFolder_MAC", {}).get("value")
        return ""

    @property
    def supports_cloud_saves(self):
        return self.game.supports_cloud_saves or self.game.supports_mac_cloud_saves
