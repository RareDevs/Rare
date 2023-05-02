import json
import os
import platform
from dataclasses import dataclass, field
from datetime import datetime
from logging import getLogger
from threading import Lock
from typing import List, Optional, Dict

from PyQt5.QtCore import QRunnable, pyqtSlot, QProcess, QThreadPool
from PyQt5.QtGui import QPixmap
from legendary.models.game import Game, InstalledGame

from rare.lgndr.core import LegendaryCore
from rare.models.install import InstallOptionsModel, UninstallOptionsModel
from rare.models.base_game import RareGameBase, RareGameSlim
from rare.shared.game_process import GameProcess
from rare.shared.image_manager import ImageManager
from rare.utils.paths import data_dir, get_rare_executable
from rare.utils.steam_grades import get_rating

logger = getLogger("RareGame")


class RareGame(RareGameSlim):
    @dataclass
    class Metadata:
        auto_update: bool = False
        queued: bool = False
        queue_pos: Optional[int] = None
        last_played: datetime = datetime.min
        grant_date: Optional[datetime] = None
        steam_grade: Optional[str] = None
        steam_date: datetime = datetime.min
        tags: List[str] = field(default_factory=list)

        @classmethod
        def from_dict(cls, data: Dict):
            return cls(
                auto_update=data.get("auto_update", False),
                queued=data.get("queued", False),
                queue_pos=data.get("queue_pos", None),
                last_played=datetime.fromisoformat(data["last_played"]) if data.get("last_played", None) else datetime.min,
                grant_date=datetime.fromisoformat(data["grant_date"]) if data.get("grant_date", None) else None,
                steam_grade=data.get("steam_grade", None),
                steam_date=datetime.fromisoformat(data["steam_date"]) if data.get("steam_date", None) else datetime.min,
                tags=data.get("tags", []),
            )

        def as_dict(self):
            return dict(
                auto_update=self.auto_update,
                queued=self.queued,
                queue_pos=self.queue_pos,
                last_played=self.last_played.isoformat() if self.last_played else datetime.min,
                grant_date=self.grant_date.isoformat() if self.grant_date else None,
                steam_grade=self.steam_grade,
                steam_date=self.steam_date.isoformat() if self.steam_date else datetime.min,
                tags=self.tags,
            )

        def __bool__(self):
            return self.queued or self.queue_pos is not None or self.last_played is not None

    def __init__(self, legendary_core: LegendaryCore, image_manager: ImageManager, game: Game):
        super(RareGame, self).__init__(legendary_core, game)
        self.__origin_install_path: Optional[str] = None
        self.__origin_install_size: Optional[int] = None

        self.image_manager = image_manager

        # Update names for Unreal Engine
        if self.game.app_title == "Unreal Engine":
            self.game.app_title += f" {self.game.app_name.split('_')[-1]}"

        self.pixmap: QPixmap = QPixmap()
        self.metadata: RareGame.Metadata = RareGame.Metadata()
        self.__load_metadata()

        self.owned_dlcs: List[RareGame] = []

        if self.has_update:
            logger.info(f"Update available for game: {self.app_name} ({self.app_title})")

        self.__worker: Optional[QRunnable] = None
        self.progress: int = 0
        self.signals.progress.start.connect(lambda: self.__on_progress_update(0))
        self.signals.progress.update.connect(self.__on_progress_update)

        self.game_process = GameProcess(self.game)
        self.game_process.launched.connect(self.__game_launched)
        self.game_process.finished.connect(self.__game_finished)
        if self.is_installed and not self.is_dlc:
            self.game_process.connect_to_server(on_startup=True)

    def __on_progress_update(self, progress: int):
        self.progress = progress

    def worker(self) -> Optional[QRunnable]:
        return self.__worker

    def set_worker(self, worker: Optional[QRunnable]):
        self.__worker = worker
        if worker is None:
            self.state = RareGame.State.IDLE

    @pyqtSlot(int)
    def __game_launched(self, code: int):
        self.state = RareGame.State.RUNNING
        self.metadata.last_played = datetime.now()
        if code == GameProcess.Code.ON_STARTUP:
            return
        self.__save_metadata()
        self.signals.game.launched.emit(self.app_name)

    @pyqtSlot(int)
    def __game_finished(self, exit_code: int):
        if exit_code == GameProcess.Code.ON_STARTUP:
            return
        if self.supports_cloud_saves:
            self.update_saves()
        self.state = RareGame.State.IDLE
        self.signals.game.finished.emit(self.app_name)

    __metadata_json: Optional[Dict] = None
    __metadata_lock: Lock = Lock()

    @staticmethod
    def __load_metadata_json() -> Dict:
        if RareGame.__metadata_json is None:
            metadata = {}
            try:
                with open(os.path.join(data_dir(), "game_meta.json"), "r") as metadata_fh:
                    metadata = json.load(metadata_fh)
            except FileNotFoundError:
                logger.info("Game metadata json file does not exist.")
            except json.JSONDecodeError:
                logger.warning("Game metadata json file is corrupt.")
            finally:
                RareGame.__metadata_json = metadata
        return RareGame.__metadata_json

    def __load_metadata(self):
        with RareGame.__metadata_lock:
            metadata: Dict = self.__load_metadata_json()
            # pylint: disable=unsupported-membership-test
            if self.app_name in metadata:
                # pylint: disable=unsubscriptable-object
                self.metadata = RareGame.Metadata.from_dict(metadata[self.app_name])

    def __save_metadata(self):
        with RareGame.__metadata_lock:
            metadata: Dict = self.__load_metadata_json()
            # pylint: disable=unsupported-assignment-operation
            metadata[self.app_name] = self.metadata.as_dict()
            with open(os.path.join(data_dir(), "game_meta.json"), "w") as metadata_json:
                json.dump(metadata, metadata_json, indent=2)

    def update_game(self):
        self.game = self.core.get_game(
            self.app_name, update_meta=False, platform=self.igame.platform if self.igame else "Windows"
        )

    def update_igame(self):
        self.igame = self.core.get_installed_game(self.app_name)

    def store_igame(self):
        self.core.lgd.set_installed_game(self.app_name, self.igame)
        self.update_igame()

    def update_rgame(self):
        self.update_game()
        self.update_igame()

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
        if self.is_origin:
            return self.__origin_install_size if self.__origin_install_size is not None else 0
        return self.igame.install_size if self.igame is not None else 0

    @property
    def install_path(self) -> Optional[str]:
        if self.igame:
            return self.igame.install_path
        elif self.is_origin:
            # TODO Linux is also C:\\...
            return self.__origin_install_path
        return None

    @install_path.setter
    def install_path(self, path: str) -> None:
        if self.igame:
            self.igame.install_path = path
            self.store_igame()
        elif self.is_origin:
            self.__origin_install_path = path

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
        return (self.igame is not None) \
            or (self.is_origin and self.__origin_install_path is not None)

    def set_installed(self, installed: bool) -> None:
        """!
        @brief Sets the installation status of a game

        If this is set to True the InstalledGame data is fetched
        for the game, if set to False the igame attribute is cleared.

        @param installed The installation status of the game
        @return None
        """
        if installed:
            self.update_igame()
            if not self.is_dlc:
                self.core.egstore_delete(self.igame)
                self.core.egstore_write(self.igame.app_name)
            self.signals.game.installed.emit(self.app_name)
            if self.has_update:
                self.signals.download.enqueue.emit(self.app_name)
        else:
            if self.has_update:
                self.signals.download.dequeue.emit(self.app_name)
            self.core.egstore_delete(self.igame)
            self.igame = None
            self.signals.game.uninstalled.emit(self.app_name)
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
            if self.is_installed:
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
    def needs_verification(self, needs: bool) -> None:
        """!
        @brief Sets the verification status of a game.

        The operation here is reversed. since the property is
        named like this. After the verification, set this to 'False'
        to update the InstalledGame in the widget.

        @param needs If the game requires verification
        @return None
        """
        self.igame.needs_verification = needs
        self.store_igame()
        # FIXME: This might not be right to do for DLCs with actual data
        for dlc in self.owned_dlcs:
            if dlc.is_installed:
                dlc.needs_verification = needs
        if not needs:
            if not self.is_dlc:
                self.core.egstore_delete(self.igame)
            self.core.egstore_write(self.igame.app_name)

    @property
    def repair_file(self) -> str:
        return os.path.join(self.core.lgd.get_tmp_path(), f"{self.app_name}.repair")

    @property
    def needs_repair(self) -> bool:
        return os.path.exists(self.repair_file)

    @needs_repair.setter
    def needs_repair(self, needs: bool) -> None:
        if not needs and os.path.exists(self.repair_file):
            os.unlink(self.repair_file)

    @property
    def is_dlc(self) -> bool:
        """!
        @brief Property to report if Game is a dlc

        @return bool
        """
        return self.game.is_dlc

    @property
    def is_unreal(self) -> bool:
        """!
        @brief Property to report if a Game is an Unreal Engine bundle

        @return bool
        """
        return False if self.is_non_asset else self.game.asset_infos["Windows"].namespace == "ue"

    @property
    def is_non_asset(self) -> bool:
        """!
        @brief Property to report if a Game doesn't have assets

        Typically, games have assets, however some games that require
        other launchers do not have them. Rare treats these games as installed
        offering to execute their launcher.

        @return bool If the game doesn't have assets
        """

        # Asset infos are usually None, but there was a bug, that it was an empty GameAsset class
        return not self.game.asset_infos or not next(iter(self.game.asset_infos.values())).app_name

    @property
    def is_origin(self) -> bool:
        """!
        @brief Property to report if a Game is an Origin game

        Legendary and by extenstion Rare can't launch Origin games directly,
        it just launches the Origin client and thus requires a bit of a special
        handling to let the user know.

        @return bool If the game is an Origin game
        """
        return (
            self.game.metadata.get("customAttributes", {}).get("ThirdPartyManagedApp", {}).get("value") == "Origin"
        )

    @property
    def is_ubisoft(self) -> bool:
        return (
            self.game.metadata.get("customAttributes", {}).get("partnerLinkType", {}).get("value") == "ubisoft"
        )

    @property
    def folder_name(self) -> str:
        return self.game.metadata.get("customAttributes", {}).get("FolderName", {}).get("value")

    @property
    def save_path(self) -> Optional[str]:
        return super(RareGame, self).save_path

    @save_path.setter
    def save_path(self, path: str) -> None:
        if self.igame and (self.game.supports_cloud_saves or self.game.supports_mac_cloud_saves):
            self.igame.save_path = path
            self.store_igame()
            self.signals.widget.update.emit()

    def steam_grade(self) -> str:
        if platform.system() == "Windows" or self.is_unreal:
            return "na"
        elapsed_time = abs(datetime.utcnow() - self.metadata.steam_date)
        if self.metadata.steam_grade is not None and elapsed_time.days < 3:
            return self.metadata.steam_grade
        worker = QRunnable.create(
            lambda: self.set_steam_grade(get_rating(self.core, self.app_name))
        )
        QThreadPool.globalInstance().start(worker)
        return "pending"

    def set_steam_grade(self, grade: str) -> None:
        self.metadata.steam_grade = grade
        self.metadata.steam_date = datetime.utcnow()
        self.__save_metadata()
        self.signals.widget.update.emit()

    def grant_date(self, force=False) -> datetime:
        if self.metadata.grant_date is None or force:
            logger.debug("Grant date for %s not found in metadata, resolving", self.app_name)
            entitlements = self.core.lgd.entitlements
            matching = filter(lambda ent: ent["namespace"] == self.game.namespace, entitlements)
            entitlement = next(matching, None)
            grant_date = datetime.fromisoformat(
                entitlement["grantDate"].replace("Z", "+00:00")
            ) if entitlement else None
            if force:
                print(grant_date)
            self.metadata.grant_date = grant_date
            self.__save_metadata()
        return self.metadata.grant_date

    @property
    def can_launch(self) -> bool:
        if self.is_idle and self.is_origin:
            return True
        if self.is_installed:
            if (not self.is_idle) or self.needs_verification:
                return False
            if self.is_foreign and not self.can_run_offline:
                return False
            return True
        return False

    def set_pixmap(self):
        self.pixmap = self.image_manager.get_pixmap(self.app_name, self.is_installed)
        if not self.pixmap.isNull():
            self.signals.widget.update.emit()

    def load_pixmap(self):
        """ Do not call this function, call set_pixmap instead. This is only used for startup image loading """
        if self.pixmap.isNull():
            self.image_manager.download_image(self.game, self.set_pixmap, 0, False)

    def refresh_pixmap(self):
        self.image_manager.download_image(self.game, self.set_pixmap, 0, True)

    def install(self) -> bool:
        if not self.is_idle:
            return False
        self.signals.game.install.emit(
            InstallOptionsModel(app_name=self.app_name)
        )
        return True

    def set_origin_attributes(self, path: str, size: int = 0) -> None:
        self.__origin_install_path = path
        self.__origin_install_size = size
        if self.install_path and self.install_size:
            self.signals.game.installed.emit(self.app_name)
        else:
            self.signals.game.uninstalled.emit(self.app_name)
        self.set_pixmap()

    def repair(self, repair_and_update):
        self.signals.game.install.emit(
            InstallOptionsModel(
                app_name=self.app_name, repair_mode=True, repair_and_update=repair_and_update, update=repair_and_update
            )
        )

    def uninstall(self) -> bool:
        if not self.is_idle:
            return False
        self.signals.game.uninstall.emit(
            UninstallOptionsModel(app_name=self.app_name)
        )
        return True

    def launch(
        self,
        offline: bool = False,
        skip_update_check: bool = False,
        wine_bin: Optional[str] = None,
        wine_pfx: Optional[str] = None,
    ) -> bool:
        if not self.can_launch:
            return False

        cmd_line = get_rare_executable()
        executable, args = cmd_line[0], cmd_line[1:]
        args.extend(["start", self.app_name])
        if offline:
            args.append("--offline")
        if skip_update_check:
            args.append("--skip-update-check")
        if wine_bin:
            args.extend(["--wine-bin", wine_bin])
        if wine_pfx:
            args.extend(["--wine-prefix", wine_pfx])

        QProcess.startDetached(executable, args)
        logger.info(f"Start new Process: ({executable} {' '.join(args)})")
        self.game_process.connect_to_server(on_startup=False)
        return True


class RareEosOverlay(RareGameBase):
    def __init__(self, legendary_core: LegendaryCore, game: Game):
        super(RareEosOverlay, self).__init__(legendary_core, game)
        self.igame: Optional[InstalledGame] = self.core.lgd.get_overlay_install_info()

    @property
    def is_installed(self) -> bool:
        return self.igame is not None

    def set_installed(self, installed: bool) -> None:
        if installed:
            self.igame = self.core.lgd.get_overlay_install_info()
            self.signals.game.installed.emit(self.app_name)
        else:
            self.igame = None
            self.signals.game.uninstalled.emit(self.app_name)

    @property
    def is_mac(self) -> bool:
        return False

    @property
    def is_win32(self) -> bool:
        return False
