import os
from dataclasses import field, dataclass
from multiprocessing import Queue

from PyQt5.QtCore import QObject, pyqtSignal

from legendary.downloader.mp.manager import DLManager
from legendary.models.downloading import AnalysisResult, ConditionCheckResult
from legendary.models.game import Game, InstalledGame


@dataclass
class InstallOptionsModel:
    app_name: str
    base_path: str = os.path.expanduser("~/legendary")
    max_workers: int = os.cpu_count() * 2
    repair: bool = False
    no_install: bool = False
    ignore_space_req: bool = False
    force: bool = False
    sdl_list: list = field(default_factory=lambda: [''])
    update: bool = False
    silent: bool = False


@dataclass
class InstallDownloadModel:
    dlmanager: DLManager
    analysis: AnalysisResult
    game: Game
    igame: InstalledGame
    repair: bool
    repair_file: str
    res: ConditionCheckResult


@dataclass
class InstallQueueItemModel:
    status_q: Queue = None
    download: InstallDownloadModel = None
    options: InstallOptionsModel = None

    def __bool__(self):
        return (self.status_q is not None) and (self.download is not None) and (self.options is not None)


class SignalActions:
    quit_app = "quit_app"
    dl_status = "dl_status"
    install_game = "install_game"
    start_installation = "start_installation"
    installation_finished = "installation_finished"
    uninstall = "uninstall"
    set_index = "set_index"
    set_dl_tab_text = "set_dl_tab_text"


class Signals(QObject):
    actions = SignalActions()

    tab_widget = pyqtSignal(tuple)
    games_tab = pyqtSignal(tuple)
    cloud_saves = pyqtSignal(tuple)
    dl_tab = pyqtSignal(tuple)
    main_window = pyqtSignal(tuple)
    app = pyqtSignal(tuple)
