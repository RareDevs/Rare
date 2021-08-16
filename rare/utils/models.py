import os
from dataclasses import field, dataclass
from multiprocessing import Queue

from custom_legendary.downloader.manager import DLManager
from custom_legendary.models.downloading import AnalysisResult
from custom_legendary.models.game import Game, InstalledGame


class InstallOptionsModel:
    app_name: str
    base_path: str = os.path.expanduser("~/legendary")
    max_workers: int = os.cpu_count() * 2
    repair: bool = False
    no_install: bool = False
    ignore_space_req: bool = False
    force: bool = False
    sdl_list: list[str] = field(default_factory=lambda: [''])


@dataclass
class InstallDownloadModel:
    dlmanager: DLManager
    analysis: AnalysisResult
    game: Game
    igame: InstalledGame
    repair: bool
    repair_file: str


@dataclass
class InstallQueueItemModel:
    status_q: Queue = None
    download: InstallDownloadModel = None
    options: InstallOptionsModel = None

    def __bool__(self):
        return (self.status_q is not None) and (self.download is not None) and (self.options is not None)
