import os
import platform as pf
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Callable, Dict, Tuple

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
    skip_dlcs: bool = False
    with_dlcs: bool = False
    # Rare's internal arguments
    # FIXME: Do we really need all of these?
    create_shortcut: bool = True
    overlay: bool = False
    update: bool = False
    silent: bool = False
    install_prereqs: bool = pf.system() == "Windows"

    def __post_init__(self):
        self.sdl_prompt: Callable[[str, str], list] = \
            lambda app_name, title: self.install_tag if self.install_tag is not None else [""]

    def as_install_kwargs(self) -> Dict:
        return {
            k: getattr(self, k)
            for k in self.__dict__
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
    keep_config: bool = None

    def __bool__(self):
        return (
            bool(self.app_name)
            and (self.accepted is not None)
            and (self.keep_files is not None)
            and (self.keep_config is not None)
        )

    @property
    def values(self) -> Tuple[bool, bool, bool]:
        """
        This model's options

        :return:
            Tuple of `accepted` `keep_files` `keep_config`
        """
        return self.accepted, self.keep_config, self.keep_files

    @values.setter
    def values(self, values: Tuple[bool, bool, bool]):
        """
        Set this model's options

        :param values:
            Tuple of `accepted` `keep_files` `keep_config`
        :return:
        """
        self.accepted = values[0]
        self.keep_files = values[1]
        self.keep_config = values[2]