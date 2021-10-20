import os
from typing import Union, List
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

    def set_no_install(self, enabled: bool) -> None:
        self.no_install = enabled


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


class PathSpec:
    egl_appdata: str = r'%LOCALAPPDATA%\EpicGamesLauncher\Saved\Config\Windows'
    egl_programdata: str = r'%PROGRAMDATA%\Epic\EpicGamesLauncher\Data\Manifests'
    wine_programdata: str = r'dosdevices/c:/ProgramData'

    @property
    def wine_egl_programdata(self):
        return self.egl_programdata.replace('\\', '/').replace('%PROGRAMDATA%', self.wine_programdata)

    def wine_egl_prefixes(self, results: int = 0) -> Union[List[str], str]:
        possible_prefixes = [
            os.path.expanduser("~/.wine"),
            os.path.expanduser("~/Games/epic-games-store"),
        ]
        prefixes = []
        for prefix in possible_prefixes:
            if os.path.exists(os.path.join(prefix, self.wine_egl_programdata)):
                prefixes.append(prefix)
        if not prefixes:
            return str()
        if not results:
            return prefixes
        elif results == 1:
            return prefixes[0]
        else:
            return prefixes[:results]


@dataclass
class ApiResults:
    game_list: list = None
    dlcs: list = None
    bit32_games: list = None
    mac_games: list = None
    assets: list = None
    no_asset_games: list = None

    def __bool__(self):
        return self.game_list is not None \
               and self.dlcs is not None \
               and self.bit32_games is not None \
               and self.mac_games is not None \
               and self.assets is not None \
               and self.no_asset_games is not None


class Signals(QObject):
    exit_app = pyqtSignal(int)
    send_notification = pyqtSignal(str)

    set_main_tab_index = pyqtSignal(int)
    update_download_tab_text = pyqtSignal()

    dl_progress = pyqtSignal(int)
    # set visibility of installing widget in games tab
    installation_started = pyqtSignal(Game)

    install_game = pyqtSignal(InstallOptionsModel)
    installation_finished = pyqtSignal(bool, str)

    update_gamelist = pyqtSignal(str)
    uninstall_game = pyqtSignal(Game)

    set_discord_rpc = pyqtSignal(str)
