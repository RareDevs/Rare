import os
from typing import Union, List

from legendary.core import LegendaryCore
from legendary.models.game import InstalledGame

from rare.utils.config_helper import get_prefixes


class PathSpec:

    @staticmethod
    def egl_appdata() -> str:
        return r"%LOCALAPPDATA%\EpicGamesLauncher\Saved\Config\Windows"

    @staticmethod
    def egl_programdata() -> str:
        return r"%PROGRAMDATA%\Epic\EpicGamesLauncher\Data\Manifests"

    @staticmethod
    def wine_programdata() -> str:
        return r"ProgramData"

    @staticmethod
    def wine_egl_programdata() -> str:
        return PathSpec.egl_programdata(
        ).replace(
            "\\", "/"
        ).replace(
            "%PROGRAMDATA%", PathSpec.wine_programdata()
        )

    @staticmethod
    def prefix_egl_programdata(prefix: str) -> str:
        return os.path.join(prefix, "dosdevices/c:", PathSpec.wine_egl_programdata())

    @staticmethod
    def wine_egl_prefixes(results: int = 0) -> Union[List[str], str]:
        possible_prefixes = get_prefixes()
        prefixes = [
            prefix
            for prefix, _ in possible_prefixes
            if os.path.exists(os.path.join(prefix, PathSpec.wine_egl_programdata()))
        ]
        if not prefixes:
            return ""
        if not results:
            return prefixes
        elif results == 1:
            return prefixes[0]
        else:
            return prefixes[:results]

    def __init__(self, core: LegendaryCore = None, igame: InstalledGame = None):
        self.__egl_path_vars = {
            "{appdata}": os.path.expandvars("%LOCALAPPDATA%"),
            "{userdir}": os.path.expandvars("%USERPROFILE%/Documents"),
            "{userprofile}": os.path.expandvars("%userprofile%"),  # possibly wrong
            "{usersavedgames}": os.path.expandvars("%USERPROFILE%/Saved Games"),
        }

        if core is not None:
            self.__egl_path_vars["{epicid}"] = core.lgd.userdata["account_id"]

        if igame is not None:
            self.__egl_path_vars["{installdir}"] = igame.install_path

    def resolve_egl_path_vars(self, path: str) -> Union[str, bytes]:
        cooked_path = (self.__egl_path_vars.get(p.lower(), p) for p in path.split("/"))
        return os.path.join(*cooked_path)
