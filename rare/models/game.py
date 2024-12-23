import json
import os
import platform
from dataclasses import dataclass, field
from datetime import datetime, timezone
from logging import getLogger
from threading import Lock
from typing import List, Optional, Dict, Set

from PySide6.QtCore import QRunnable, Slot, QProcess, QThreadPool
from PySide6.QtGui import QPixmap
from legendary.lfs import eos
from legendary.models.game import Game, InstalledGame

from rare.models.image import ImageSize
from rare.lgndr.core import LegendaryCore
from rare.models.base_game import RareGameBase, RareGameSlim
from rare.models.install import InstallOptionsModel, UninstallOptionsModel
from rare.shared.game_process import GameProcess
from rare.shared.image_manager import ImageManager
from rare.utils.paths import data_dir, get_rare_executable
from rare.utils.steam_grades import get_rating
from rare.utils.config_helper import set_envvar, get_option

logger = getLogger("RareGame")


class RareGame(RareGameSlim):
    @dataclass
    class Metadata:
        queued: bool = False
        queue_pos: Optional[int] = None
        last_played: datetime = datetime.min.replace(tzinfo=timezone.utc)
        grant_date: datetime = datetime.min.replace(tzinfo=timezone.utc)
        steam_appid: Optional[int] = None
        steam_grade: Optional[str] = None
        steam_date: datetime = datetime.min.replace(tzinfo=timezone.utc)
        steam_shortcut: Optional[int] = None
        tags: List[str] = field(default_factory=list)

        # For compatibility with previously created game metadata
        @staticmethod
        def parse_date(strdate: str):
            dt = datetime.fromisoformat(strdate) if strdate else datetime.min
            return dt.replace(tzinfo=timezone.utc)

        @classmethod
        def from_dict(cls, data: Dict):
            return cls(
                queued=data.get("queued", False),
                queue_pos=data.get("queue_pos", None),
                last_played=RareGame.Metadata.parse_date(data.get("last_played", "")),
                grant_date=RareGame.Metadata.parse_date(data.get("grant_date", "")),
                steam_appid=data.get("steam_appid", None),
                steam_grade=data.get("steam_grade", None),
                steam_date=RareGame.Metadata.parse_date(data.get("steam_date", "")),
                steam_shortcut=data.get("steam_shortcut", None),
                tags=data.get("tags", []),
            )

        @property
        def __dict__(self):
            return dict(
                queued=self.queued,
                queue_pos=self.queue_pos,
                last_played=self.last_played.isoformat() if self.last_played else datetime.min.replace(tzinfo=timezone.utc),
                grant_date=self.grant_date.isoformat() if self.grant_date else datetime.min.replace(tzinfo=timezone.utc),
                steam_appid=self.steam_appid,
                steam_grade=self.steam_grade,
                steam_date=self.steam_date.isoformat() if self.steam_date else datetime.min.replace(tzinfo=timezone.utc),
                steam_shortcut=self.steam_shortcut,
                tags=self.tags,
            )

        def __bool__(self):
            return self.queued or self.queue_pos is not None or self.last_played is not None

    def __init__(self, legendary_core: LegendaryCore, image_manager: ImageManager, game: Game, parent=None):
        super(RareGame, self).__init__(legendary_core, game, parent=parent)
        self.__origin_install_path: Optional[str] = None
        self.__origin_install_size: Optional[int] = None

        self.image_manager = image_manager

        # Update names for Unreal Engine
        if self.game.app_title == "Unreal Engine":
            self.game.app_title += f" {self.game.app_name.split('_')[-1]}"

        self.has_pixmap: bool = False
        self.metadata: RareGame.Metadata = RareGame.Metadata()
        self.__load_metadata()
        self.grant_date()

        self.owned_dlcs: Set[RareGame] = set()

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

    def add_dlc(self, dlc) -> None:
        # lk: plug dlc progress signals to the game's
        dlc.signals.progress.start.connect(self.signals.progress.start)
        dlc.signals.progress.update.connect(self.signals.progress.update)
        dlc.signals.progress.finish.connect(self.signals.progress.finish)
        self.owned_dlcs.add(dlc)

    def __on_progress_update(self, progress: int):
        self.progress = progress

    def worker(self) -> Optional[QRunnable]:
        return self.__worker

    def set_worker(self, worker: Optional[QRunnable]):
        self.__worker = worker
        if worker is None:
            self.state = RareGame.State.IDLE

    @Slot(int)
    def __game_launched(self, code: int):
        self.state = RareGame.State.RUNNING
        self.metadata.last_played = datetime.now(timezone.utc)
        if code == GameProcess.Code.ON_STARTUP:
            return
        self.__save_metadata()
        self.signals.game.launched.emit(self.app_name)

    @Slot(int)
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
            file = os.path.join(data_dir(), "game_meta.json")
            try:
                with open(file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
            except FileNotFoundError:
                logger.info("%s does not exist", file)
            except json.JSONDecodeError:
                logger.warning("%s is corrupt", file)
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
            metadata[self.app_name] = vars(self.metadata)
            with open(os.path.join(data_dir(), "game_meta.json"), "w+", encoding="utf-8") as file:
                json.dump(metadata, file, indent=2)

    def update_game(self):
        self.game = self.core.get_game(
            self.app_name, update_meta=False,
            platform=self.igame.platform if self.igame else self.default_platform
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
        if self.is_origin:
            # TODO Linux is also C:\\...
            return self.__origin_install_path
        return super(RareGame, self).install_path

    @install_path.setter
    def install_path(self, path: str) -> None:
        if self.igame:
            self.igame.install_path = path
            self.store_igame()
        elif self.is_origin:
            self.__origin_install_path = path

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
            return self.game.app_version(self.default_platform)

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
    def is_ubisoft(self) -> bool:
        return self.game.partner_link_type == "ubisoft"

    @property
    def folder_name(self) -> str:
        return (
            folder_name
            if (folder_name := self.game.metadata.get("customAttributes", {}).get("FolderName", {}).get("value"))
            else self.app_title
        )

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
        if self.metadata.steam_grade != "pending":
            elapsed_time = abs(datetime.now(timezone.utc) - self.metadata.steam_date)
            if elapsed_time.days > 3:
                logger.info("Refreshing ProtonDB grade for %s", self.app_title)
                worker = QRunnable.create(self.set_steam_grade)
                QThreadPool.globalInstance().start(worker)
                self.metadata.steam_grade = "pending"
        return self.metadata.steam_grade

    @property
    def steam_appid(self) -> Optional[int]:
        return self.metadata.steam_appid

    def set_steam_appid(self, appid: int):
        set_envvar(self.app_name, "SteamAppId", str(appid))
        set_envvar(self.app_name, "SteamGameId", str(appid))
        set_envvar(self.app_name, "STEAM_COMPAT_APP_ID", str(appid))
        self.metadata.steam_appid = appid

    def set_steam_grade(self) -> None:
        appid, grade = get_rating(self.core, self.app_name)
        if appid and self.steam_appid is None:
            self.set_steam_appid(appid)
        self.metadata.steam_grade = grade
        self.metadata.steam_date = datetime.now(timezone.utc)
        self.__save_metadata()
        self.signals.widget.update.emit()

    def grant_date(self, force=False) -> datetime:
        if not (entitlements := self.core.lgd.entitlements):
            return self.metadata.grant_date
        if self.metadata.grant_date == datetime.min.replace(tzinfo=timezone.utc) or force:
            logger.debug("Grant date for %s not found in metadata, resolving", self.app_name)
            matching = filter(lambda ent: ent["namespace"] == self.game.namespace, entitlements)
            entitlement = next(matching, None)
            grant_date = datetime.fromisoformat(
                entitlement["grantDate"].replace("Z", "+00:00")
            ) if entitlement else datetime.min.replace(tzinfo=timezone.utc)
            self.metadata.grant_date = grant_date
            self.__save_metadata()
        return self.metadata.grant_date

    def set_origin_attributes(self, path: str, size: int = 0) -> None:
        self.__origin_install_path = path
        self.__origin_install_size = size
        if self.install_path and self.install_size:
            self.signals.game.installed.emit(self.app_name)
        else:
            self.signals.game.uninstalled.emit(self.app_name)
        self.set_pixmap()

    @property
    def can_launch(self) -> bool:
        if self.is_idle and self.is_origin:
            return True
        if self.is_installed:
            if (not self.is_idle) or self.needs_verification:
                return False
            return bool(not self.is_foreign or self.can_run_offline)
        return False

    def get_pixmap(self, preset: ImageSize.Preset, color=True) -> QPixmap:
        return self.image_manager.get_pixmap(self.app_name, preset, color)

    @Slot(object)
    def set_pixmap(self):
        # self.pixmap = not self.image_manager.get_pixmap(self.app_name, self.is_installed).isNull()
        self.has_pixmap = True
        if self.has_pixmap:
            self.signals.widget.update.emit()

    def load_pixmaps(self):
        """ Do not call this function, call set_pixmap instead. This is only used for initial image loading """
        if not self.has_pixmap:
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

    def modify(self) -> bool:
        if not self.is_idle:
            return False
        self.signals.game.install.emit(
            InstallOptionsModel(
                app_name=self.app_name, reset_sdl=True
            )
        )
        return True

    def repair(self, repair_and_update) -> bool:
        if not self.is_idle:
            return False
        self.signals.game.install.emit(
            InstallOptionsModel(
                app_name=self.app_name, repair_mode=True, repair_and_update=repair_and_update, update=repair_and_update
            )
        )
        return True

    def uninstall(self) -> bool:
        if not self.is_idle:
            return False
        self.signals.game.uninstall.emit(
            UninstallOptionsModel(app_name=self.app_name, keep_config=self.sdl_name is not None)
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
        args.extend(["launch", self.app_name])
        if offline or get_option(self.app_name, "offline", fallback=None):
            args.append("--offline")
        if skip_update_check or get_option(self.app_name, "skip_update_check", fallback=None):
            args.append("--skip-update-check")
        if wine_bin:
            args.extend(["--wine-bin", wine_bin])
        if wine_pfx:
            args.extend(["--wine-prefix", wine_pfx])

        logger.info(f"Starting game process: ({executable} {' '.join(args)})")
        QProcess.startDetached(executable, args)
        self.game_process.connect_to_server(on_startup=False)
        return True


class RareEosOverlay(RareGameBase):
    def __init__(self, legendary_core: LegendaryCore, game: Game, parent=None):
        super(RareEosOverlay, self).__init__(legendary_core, game, parent=parent)
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
    def has_update(self) -> bool:
        # lk: Don't check for updates here to ensure fast return
        # There is already a thread in the EosGroup form to update it for us asynchronously
        # and legendary does it too during login
        return self.core.overlay_update_available

    def is_enabled(self, prefix: Optional[str] = None) -> bool:
        try:
            reg_paths = eos.query_registry_entries(prefix)
        except ValueError as e:
            logger.info("%s %s", e, prefix)
            return False
        return reg_paths["overlay_path"] and self.core.is_overlay_install(reg_paths["overlay_path"])

    def active_path(self, prefix: Optional[str] = None) -> str:
        try:
            path = eos.query_registry_entries(prefix)["overlay_path"]
        except ValueError as e:
            logger.info("%s %s", e, prefix)
            return ""
        return path if path and self.core.is_overlay_install(path) else ""

    def available_paths(self, prefix: Optional[str] = None) -> List[str]:
        try:
            installs = self.core.search_overlay_installs(prefix)
        except ValueError as e:
            logger.info("%s %s", e, prefix)
            return []
        return installs

    def enable(
        self, prefix: Optional[str] = None, path: Optional[str] = None
    ) -> bool:
        if self.is_enabled(prefix):
            return False
        if not path:
            if self.is_installed:
                path = self.igame.install_path
            else:
                path = self.available_paths(prefix)[-1]
        reg_paths = eos.query_registry_entries(prefix)
        if old_path := reg_paths["overlay_path"]:
            if os.path.normpath(old_path) == path:
                logger.info("Overlay already enabled, nothing to do.")
                return True
            else:
                logger.info(f'Updating overlay registry entries from "{old_path}" to "{path}"')
            eos.remove_registry_entries(prefix)
        try:
            eos.add_registry_entries(path, prefix)
        except PermissionError as e:
            logger.error("Exception while writing registry to enable the overlay.")
            logger.error(e)
            return False
        logger.info(f"Enabled overlay at: {path} for prefix: {prefix}")
        return True

    def disable(self, prefix: Optional[str] = None) -> bool:
        if not self.is_enabled(prefix):
            return False
        logger.info(f"Disabling overlay (removing registry keys) for prefix: {prefix}")
        try:
            eos.remove_registry_entries(prefix)
        except PermissionError as e:
            logger.error("Exception while writing registry to disable the overlay.")
            logger.error(e)
            return False
        return True

    def install(self) -> bool:
        if not self.is_idle:
            return False
        self.signals.game.install.emit(
            InstallOptionsModel(
                app_name=self.app_name,
                base_path=self.core.get_default_install_dir(),
                platform="Windows", update=self.is_installed, overlay=True
            )
        )
        return True

    def uninstall(self) -> bool:
        if not self.is_idle or not self.is_installed:
            return False
        self.signals.game.uninstall.emit(
            UninstallOptionsModel(app_name=self.app_name)
        )
        return True
