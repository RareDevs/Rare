import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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
    read_files: bool = False
    order_opt: bool = False
    repair_mode: bool = False
    repair_and_update: bool = False
    no_install: bool = False
    ignore_space: bool = False
    reset_sdl: bool = False
    disable_https: bool = False
    always_use_signed_urls: bool = True
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
    def __init__(self, options: InstallOptionsModel, download: InstallDownloadModel = None):
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
        return datetime.now() > (self.__date + timedelta(minutes=5))

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
        return (
            self.accepted,
            self.keep_files,
            self.keep_folder,
            self.keep_config,
            self.keep_overlay_keys,
        )

    @__values.setter
    def __values(self, values: Tuple[bool, bool, bool, bool, bool]):
        (
            self.accepted,
            self.keep_files,
            self.keep_folder,
            self.keep_config,
            self.keep_overlay_keys,
        ) = values

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
        return bool(self.app_name) and (self.accepted is not None) and (self.install_tag is not None)


class MoveGameModel:

    def __init__(self, app_name, install_path: str, default_name: str):
        self.app_name: str = app_name
        self.default_name: str = default_name

        path = Path(install_path)
        self._target_path: Path = path.parent
        self._target_name: str = path.name

        self._rename_path: bool = False
        self._reset_name: bool = False

        self.dst_exists: bool = False
        self.dst_delete: bool = False
        self.accepted: bool = False

    @property
    def rename_path(self) -> bool:
        return self._rename_path

    @rename_path.setter
    def rename_path(self, val: bool):
        self._rename_path = val
        self._reset_name = False

    @property
    def reset_name(self) -> bool:
        return self._reset_name

    @reset_name.setter
    def reset_name(self, val: bool):
        self._rename_path = False
        self._reset_name = val

    @property
    def target_path(self) -> str:
        return str(self._target_path)

    @target_path.setter
    def target_path(self, path: str):
        self._target_path = Path(path)

    @property
    def target_name(self) -> str:
        if self._rename_path:
            return ""
        if self._reset_name:
            return self.default_name
        return self._target_name

    @property
    def full_path(self) -> str:
        if self._rename_path:
            return self.target_path
        else:
            return str(self._target_path.joinpath(self.target_name))

    def __bool__(self):
        return (
            bool(self.app_name)
            and (self.accepted is not None)
            and bool(self.target_path)
            and (bool(self.target_name) ^ self._rename_path)
        )
