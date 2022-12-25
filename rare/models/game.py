import os
from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from logging import getLogger
from typing import List, Optional

from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool, QMetaObject
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMessageBox
from legendary.models.game import Game, InstalledGame, SaveGameFile

from rare.models.install import InstallOptionsModel
from rare.lgndr.core import LegendaryCore
from rare.shared.image_manager import ImageManager
# from rare.utils.legendary_utils import VerificationWorker

logger = getLogger("RareGame")


class RareGameState(IntEnum):
    IDLE = 0,
    RUNNING = 1,


class RareGame(QObject):

    @dataclass
    class Metadata:
        queued: bool = False
        queue_pos: Optional[int] = None
        last_played: Optional[datetime] = None

        @classmethod
        def from_json(cls, data):
            return cls(
                queued=data.get("queued", False),
                queue_pos=data.get("queue_pos", None),
                last_played=datetime.strptime(data.get("last_played", "None"), "%Y-%m-%dT%H:%M:%S.%f"),
            )

        def __dict__(self):
            return dict(
                queued=self.queued,
                queue_pos=self.queue_pos,
                last_played=self.last_played.strftime("%Y-%m-%dT%H:%M:%S.%f"),
            )

        def __bool__(self):
            return self.queued or self.queue_pos is not None or self.last_played is not None

    class Signals:
        class Progress(QObject):
            start = pyqtSignal()
            update = pyqtSignal(int)
            finish = pyqtSignal(bool)

        class Widget(QObject):
            update = pyqtSignal()

        class Game(QObject):
            install = pyqtSignal(InstallOptionsModel)
            uninstalled = pyqtSignal()

        def __init__(self):
            super(RareGame.Signals, self).__init__()
            self.progress = RareGame.Signals.Progress()
            self.widget = RareGame.Signals.Widget()
            self.game = RareGame.Signals.Game()

    progress: int = 0
    active_thread: Optional[QRunnable] = None

    def __init__(self, game: Game, legendary_core: LegendaryCore, image_manager: ImageManager):
        super(RareGame, self).__init__()
        self.signals = RareGame.Signals()

        self.core = legendary_core
        self.image_manager = image_manager

        self.game: Game = game
        # Update names for Unreal Engine
        if self.game.app_title == "Unreal Engine":
            self.game.app_title += f" {self.game.app_name.split('_')[-1]}"

        # None if origin or not installed
        self.igame: Optional[InstalledGame] = self.core.get_installed_game(game.app_name)

        self.pixmap: QPixmap = QPixmap()
        self.metadata: RareGame.Metadata = RareGame.Metadata()

        self.owned_dlcs: List[RareGame] = []
        self.saves: List[SaveGameFile] = []

        if self.has_update:
            logger.info(f"Update available for game: {self.app_name} ({self.app_title})")

        self.threadpool = QThreadPool.globalInstance()

        self.game_running = False

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
    def developer(self) -> str:
        """!
        @brief Property to report the developer of a Game

        @return str
        """
        return self.game.metadata["developer"]

    @property
    def install_size(self) -> int:
        """!
        @brief Property to report the installation size of an InstalledGame

        @return int The size of the installation
        """
        return self.igame.install_size if self.igame is not None else 0

    @property
    def version(self) -> str:
        """!
        @brief Reports the currently installed version of the Game

        If InstalledGame reports the currently installed version, which might be
        different from the remote version available from EGS. For not installed Games
        it reports the already known version.

        @return str The current version of the game
        """
        return self.igame.version if self.igame is not None else self.game.app_version()

    @property
    def remote_version(self) -> str:
        """!
        @brief Property to report the remote version of an InstalledGame

        If the Game is installed, requests the latest version string from EGS,
        otherwise it reports the already known version of the Game for Windows.

        @return str The current version from EGS
        """
        if self.igame is not None:
            return self.game.app_version(self.igame.platform)
        else:
            return self.game.app_version()

    @property
    def has_update(self) -> bool:
        """!
        @brief Property to report if an InstalledGame has updates available

        Games have to be installed and have assets available to have
        updates

        @return bool If there is an update available
        """
        if self.igame is not None and self.core.lgd.assets is not None:
            try:
                if self.remote_version != self.igame.version:
                    return True
            except ValueError:
                logger.error(f"Asset error for {self.game.app_title}")
                return False
        return False

    @property
    def is_installed(self) -> bool:
        """!
        @brief Property to report if a game is installed

        This returns True if InstalledGame data have been loaded for the game
        or if the game is a game without assets, for example an Origin game.

        @return bool If the game should be considered installed
        """
        return (self.igame is not None) or self.is_non_asset

    def set_installed(self, installed: bool) -> None:
        """!
        @brief Sets the installation status of a game

        If this is set to True the InstalledGame data is fetched
        for the game, if set to False the igame attribute is cleared.

        @param installed The installation status of the game
        @return None
        """
        if installed:
            self.igame = self.core.get_installed_game(self.app_name)
        else:
            self.igame = None
        self.set_pixmap()

    @property
    def can_run_offline(self) -> bool:
        """!
        @brief Property to report if a game can run offline

        Checks if the game can run without connectin the internet.
        It's a simple wrapper around legendary provided information,
        with handling of not installed games.

        @return bool If the games can run without network
        """
        return self.igame.can_run_offline if self.igame is not None else False

    @property
    def is_foreign(self) -> bool:
        """!
        @brief Property to report if a game doesn't belong to the current account

        Checks if a game belongs to the currently logged in account. Games that require
        a network connection or remote authentication will fail to run from another account
        despite being installed. On the other hand, games that do not require network,
        can be executed, facilitating a rudimentary game sharing option on the same computer.

        @return bool If the game belongs to another count or not
        """
        ret = True
        try:
            if self.igame is not None:
                _ = self.core.get_asset(self.game.app_name, platform=self.igame.platform).build_version
                ret = False
        except ValueError:
            logger.warning(f"Game {self.game.app_title} has no metadata. Set offline true")
        except AttributeError:
            ret = False
        return ret

    @property
    def needs_verification(self) -> bool:
        """!
        @brief Property to report if a games requires to be verified

        Simple wrapper around legendary's attribute with installation
        status check

        @return bool If the games needs to be verified
        """
        if self.igame is not None:
            return self.igame.needs_verification
        else:
            return False

    @needs_verification.setter
    def needs_verification(self, not_update: bool) -> None:
        """!
        @brief Sets the verification status of a game.

        The operation here is reversed. since the property is
        named like this. After the verification, set this to 'False'
        to update the InstalledGame in the widget.

        @param not_update If the game requires verification
        @return None
        """
        if not not_update:
            self.igame = self.core.get_installed_game(self.game.app_name)

    @property
    def is_dlc(self) -> bool:
        """!
        @brief Property to report if Game is a dlc

        @return bool
        """
        return self.game.is_dlc

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
    def is_unreal(self) -> bool:
        """!
        @brief Property to report if a Game is an Unreal Engine bundle

        @return bool
        """
        if not self.is_non_asset:
            return self.game.asset_infos["Windows"].namespace == "ue"
        else:
            return False

    @property
    def is_non_asset(self) -> bool:
        """!
        @brief Property to report if a Game doesn't have assets

        Typically, games have assets, however some games that require
        other launchers do not have them. Rare treats these games as installed
        offering to execute their launcher.

        @return bool If the game doesn't have assets
        """
        return not self.game.asset_infos

    @property
    def is_origin(self) -> bool:
        return self.game.metadata.get("customAttributes", {}).get("ThirdPartyManagedApp", {}).get("value") == "Origin"

    @property
    def can_launch(self) -> bool:
        if self.is_installed:
            if self.is_non_asset:
                return True
            elif self.game_running or self.needs_verification:
                return False
            else:
                return True
        else:
            return False

    def set_pixmap(self):
        self.pixmap = self.image_manager.get_pixmap(self.app_name, self.is_installed)
        if self.pixmap.isNull():
            self.image_manager.download_image(self.game, self.set_pixmap, 0, False)
        else:
            self.signals.widget.update.emit()

    def refresh_pixmap(self):
        self.image_manager.download_image(self.game, self.set_pixmap, 0, True)

    def start_progress(self):
        self.signals.progress.start.emit()

    def update_progress(self, progress: int):
        self.progress = progress
        self.signals.progress.update.emit(progress)

    def finish_progress(self, fail: bool, miss: int, app: str):
        self.set_installed(True)
        self.signals.progress.finish.emit(fail)
