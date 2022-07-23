import os
import platform as pf
from dataclasses import field, dataclass
from multiprocessing import Queue
from typing import Union, List, Optional, Callable, Dict

from legendary.core import LegendaryCore
from legendary.downloader.mp.manager import DLManager
from legendary.models.downloading import AnalysisResult, ConditionCheckResult
from legendary.models.game import Game, InstalledGame


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
    # Rare's internal arguments
    # FIXME: Do we really need all of these?
    create_shortcut: bool = True
    overlay: bool = False
    update: bool = False
    silent: bool = False
    install_preqs: bool = pf.system() == "Windows"

    def __post_init__(self):
        self.sdl_prompt: Callable[[str, str], list] = lambda app_name, title: self.install_tag

    def as_install_kwargs(self) -> Dict:
        return {
            k: getattr(self, k)
            for k in self.__dict__
            if k not in ["update", "silent", "create_shortcut", "overlay", "install_preqs"]
        }


@dataclass
class InstallDownloadModel:
    dlmanager: DLManager
    analysis: AnalysisResult
    igame: InstalledGame
    game: Game
    repair: bool
    repair_file: str
    res: ConditionCheckResult


@dataclass
class InstallQueueItemModel:
    download: Optional[InstallDownloadModel] = None
    options: Optional[InstallOptionsModel] = None

    def __bool__(self):
        return (self.download is not None) and (self.options is not None)


class PathSpec:
    __egl_path_vars = {
        "{appdata}": os.path.expandvars("%LOCALAPPDATA%"),
        "{userdir}": os.path.expandvars("%USERPROFILE%/Documents"),
        # '{userprofile}': os.path.expandvars('%userprofile%'),  # possibly wrong
        "{usersavedgames}": os.path.expandvars("%USERPROFILE%/Saved Games"),
    }
    egl_appdata: str = r"%LOCALAPPDATA%\EpicGamesLauncher\Saved\Config\Windows"
    egl_programdata: str = r"%PROGRAMDATA%\Epic\EpicGamesLauncher\Data\Manifests"
    wine_programdata: str = r"dosdevices/c:/ProgramData"

    def __init__(self, core: LegendaryCore = None, app_name: str = "default"):
        if core is not None:
            self.__egl_path_vars.update({"{epicid}": core.lgd.userdata["account_id"]})
        self.app_name = app_name

    def cook(self, path: str) -> str:
        cooked_path = [self.__egl_path_vars.get(p.lower(), p) for p in path.split("/")]
        return os.path.join(*cooked_path)

    @property
    def wine_egl_programdata(self):
        return self.egl_programdata.replace("\\", "/").replace("%PROGRAMDATA%", self.wine_programdata)

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
