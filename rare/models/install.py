import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple

from legendary.models.downloading import AnalysisResult, ConditionCheckResult
from legendary.models.game import Game, InstalledGame

from rare.lgndr.downloader.mp.manager import DLManager


@dataclass
class InstallOptionsModel:
    app_name: str
    base_path: str = ""
    shared_memory: int = 1024
    max_workers: int = os.cpu_count() * 2
    force: bool = False
    platform: str = "Windows"
    install_tag: Optional[List[str]] = None
    order_opt: bool = False
    repair_mode: bool = False
    repair_and_update: bool = False
    no_install: bool = False
    ignore_space: bool = False
    reset_sdl: bool = False
    skip_dlcs: bool = False
    with_dlcs: bool = False
    # Rare's internal arguments
    # FIXME: Do we really need all of these?
    create_shortcut: bool = True
    overlay: bool = False
    update: bool = False
    silent: bool = False
    install_prereqs: bool = False

    def as_install_kwargs(self) -> Dict:
        return {
            k: getattr(self, k)
            for k in vars(self)
            if k not in ["update", "silent", "create_shortcut", "overlay", "install_prereqs"]
        }


@dataclass
class InstallDownloadModel:
    dlm: DLManager
    analysis: AnalysisResult
    igame: InstalledGame
    game: Game
    repair: bool
    repair_file: str
    res: ConditionCheckResult


class InstallQueueItemModel:
    def __init__(self, options: InstallOptionsModel,  download: InstallDownloadModel = None):
        self.options: Optional[InstallOptionsModel] = options
        # lk: internal attribute holders
        self.__download: Optional[InstallDownloadModel] = None
        self.__date: Optional[datetime] = None

        self.download = download

    @property
    def download(self) -> Optional[InstallDownloadModel]:
        return self.__download

    @download.setter
    def download(self, download: Optional[InstallDownloadModel]):
        self.__download = download
        if download is not None:
            self.__date = datetime.now()

    @property
    def expired(self) -> bool:
        return datetime.now() > (self.__date + timedelta(minutes=30))

    def __bool__(self):
        return (self.download is not None) and (self.options is not None) and (not self.expired)


@dataclass
class UninstallOptionsModel:
    app_name: str
    accepted: bool = None
    keep_files: bool = None
    keep_folder: bool = True
    keep_config: bool = None
    keep_overlay_keys: bool = None

    @property
    def __values(self) -> Tuple[bool, bool, bool, bool, bool]:
        return self.accepted, self.keep_files, self.keep_folder, self.keep_config, self.keep_overlay_keys

    @__values.setter
    def __values(self, values: Tuple[bool, bool, bool, bool, bool]):
        self.accepted, self.keep_files, self.keep_folder, self.keep_config, self.keep_overlay_keys = values

    def __bool__(self):
        return bool(self.app_name) and all(map(lambda x: x is not None, self.__values))

    def __iter__(self):
        return iter(self.__values)

    def set_accepted(self, keep_files, keep_folder, keep_config, keep_overlay_keys):
        self.__values = True, keep_files, keep_folder, keep_config, keep_overlay_keys

    def set_rejected(self):
        self.__values = False, None, None, None, None


@dataclass
class SelectiveDownloadsModel:
    app_name: str
    accepted: bool = None
    install_tag: Optional[List[str]] = None

    def __bool__(self):
        return (
            bool(self.app_name)
            and (self.accepted is not None)
            and (self.install_tag is not None)
        )


@dataclass
class MoveGameModel:
    app_name: str
    accepted: bool = None
    target_path: Optional[str] = None

    def __bool__(self):
        return (
            bool(self.app_name)
            and (self.accepted is not None)
            and (self.target_path is not None)
        )
