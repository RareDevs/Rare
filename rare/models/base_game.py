from abc import abstractmethod
from datetime import datetime
from enum import IntEnum
from logging import getLogger
from typing import Optional, List

from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool
from legendary.models.game import SaveGameFile, SaveGameStatus, Game, InstalledGame

from rare.lgndr.core import LegendaryCore
from rare.models.install import UninstallOptionsModel, InstallOptionsModel

logger = getLogger("RareGameBase")


class RareGameBase(QObject):

    class State(IntEnum):
        IDLE = 0
        RUNNING = 1
        DOWNLOADING = 2
        VERIFYING = 3
        MOVING = 4
        UNINSTALLING = 5
        SYNCING = 6

    class Signals:
        class Progress(QObject):
            start = pyqtSignal()
            update = pyqtSignal(int)
            finish = pyqtSignal(bool)

        class Widget(QObject):
            update = pyqtSignal()

        class Download(QObject):
            enqueue = pyqtSignal(str)
            dequeue = pyqtSignal(str)

        class Game(QObject):
            install = pyqtSignal(InstallOptionsModel)
            installed = pyqtSignal(str)
            uninstall = pyqtSignal(UninstallOptionsModel)
            uninstalled = pyqtSignal(str)
            launched = pyqtSignal(str)
            finished = pyqtSignal(str)

        def __init__(self):
            super(RareGameBase.Signals, self).__init__()
            self.progress = RareGameBase.Signals.Progress()
            self.widget = RareGameBase.Signals.Widget()
            self.download = RareGameBase.Signals.Download()
            self.game = RareGameBase.Signals.Game()

        def __del__(self):
            self.progress.deleteLater()
            self.widget.deleteLater()
            self.download.deleteLater()
            self.game.deleteLater()

    __slots__ = "igame"

    def __init__(self, legendary_core: LegendaryCore, game: Game):
        super(RareGameBase, self).__init__()
        self.signals = RareGameBase.Signals()
        self.core = legendary_core
        self.game: Game = game
        self._state = RareGameBase.State.IDLE

    def __del__(self):
        del self.signals

    @property
    def state(self) -> 'RareGameBase.State':
        return self._state

    @state.setter
    def state(self, state: 'RareGameBase.State'):
        if state != self._state:
            self._state = state
            self.signals.widget.update.emit()

    @property
    def is_idle(self):
        return self.state == RareGameBase.State.IDLE

    @property
    def app_name(self) -> str:
        return self.igame.app_name if self.igame is not None else self.game.app_name

    @property
    def app_title(self) -> str:
        return self.igame.title if self.igame is not None else self.game.app_title

    @property
    def title(self) -> str:
        return self.app_title

    @property
    @abstractmethod
    def is_installed(self) -> bool:
        pass

    @abstractmethod
    def set_installed(self, installed: bool) -> None:
        pass

    @property
    @abstractmethod
    def is_mac(self) -> bool:
        pass

    @property
    @abstractmethod
    def is_win32(self) -> bool:
        pass


class RareGameSlim(RareGameBase):

    def __init__(self, legendary_core: LegendaryCore, game: Game):
        super(RareGameSlim, self).__init__(legendary_core, game)
        # None if origin or not installed
        self.igame: Optional[InstalledGame] = self.core.get_installed_game(game.app_name)
        self.saves: List[SaveGameFile] = []

    @property
    def is_installed(self) -> bool:
        return True

    def set_installed(self, installed: bool) -> None:
        pass

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
    def save_path(self) -> Optional[str]:
        if self.igame is not None:
            return self.igame.save_path
        return None

    @property
    def latest_save(self) -> Optional[SaveGameFile]:
        if self.saves:
            self.saves.sort(key=lambda s: s.datetime, reverse=True)
            return self.saves[0]
        return None

    @property
    def save_game_state(self) -> (SaveGameStatus, (datetime, datetime)):
        if self.saves and self.save_path :
            return self.core.check_savegame_state(self.save_path, self.latest_save)
        return SaveGameStatus.NO_SAVE, (None, None)

    def upload_saves(self):
        status, (dt_local, dt_remote) = self.save_game_state
        def _upload():
            logger.info(f"Uploading save for {self.title}")
            self.state = RareGameSlim.State.SYNCING
            self.core.upload_save(self.app_name, self.igame.save_path, dt_local)
            self.state = RareGameSlim.State.IDLE
            self.update_saves()

        if not self.game.supports_cloud_saves and not self.game.supports_mac_cloud_saves:
            return
        if status == SaveGameStatus.NO_SAVE or not dt_local:
            logger.warning("Can't upload non existing save")
            return
        if self.state == RareGameSlim.State.SYNCING:
            logger.error(f"{self.title} is already syncing")
            return

        worker = QRunnable.create(lambda: _upload())
        QThreadPool.globalInstance().start(worker)

    def download_saves(self):
        status, (dt_local, dt_remote) = self.save_game_state
        def _download():
            logger.info(f"Downloading save for {self.title}")
            self.state = RareGameSlim.State.SYNCING
            self.core.download_saves(self.app_name, self.latest_save.manifest_name, self.save_path)
            self.state = RareGameSlim.State.IDLE
            self.update_saves()

        if not self.game.supports_cloud_saves and not self.game.supports_mac_cloud_saves:
            return
        if status == SaveGameStatus.NO_SAVE or not dt_remote:
            logger.error("Can't download non existing save")
            return
        if self.state == RareGameSlim.State.SYNCING:
            logger.error(f"{self.title} is already syncing")
            return

        worker = QRunnable.create(lambda: _download())
        QThreadPool.globalInstance().start(worker)

    def update_saves(self):
        self.saves = self.core.get_save_games(self.app_name)
        self.signals.widget.update.emit()

    @property
    def is_save_up_to_date(self):
        status, (_, _) = self.save_game_state
        return (status == SaveGameStatus.SAME_AGE) \
            or (status == SaveGameStatus.NO_SAVE)
