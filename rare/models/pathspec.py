import os
from typing import Union, List

from legendary.core import LegendaryCore


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
