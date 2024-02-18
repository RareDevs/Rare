import os
from dataclasses import dataclass
from logging import getLogger
from typing import Dict, Tuple, List, Optional

logger = getLogger("Wine")

lutris_runtime_paths = [
    os.path.expanduser("~/.local/share/lutris")
]

__lutris_runtime: str = None
__lutris_wine: str = None


def find_lutris() -> Tuple[str, str]:
    global __lutris_runtime, __lutris_wine
    for path in lutris_runtime_paths:
        runtime_path = os.path.join(path, "runtime")
        wine_path = os.path.join(path, "runners", "wine")
        if os.path.isdir(path) and os.path.isdir(runtime_path) and os.path.isdir(wine_path):
            __lutris_runtime, __lutris_wine = runtime_path, wine_path
            return runtime_path, wine_path


@dataclass
class WineRuntime:
    name: str
    path: str
    environ: Dict


@dataclass
class WineRunner:
    name: str
    path: str
    environ: Dict
    runtime: Optional[WineRuntime] = None


def find_lutris_wines(runtime_path: str = None, wine_path: str = None) -> List[WineRunner]:
    runners = []
    if not runtime_path and not wine_path:
        return runners


def __get_lib_path(executable: str, basename: str = "") -> str:
    path = os.path.dirname(os.path.dirname(executable))
    lib32 = os.path.realpath(os.path.join(path, "lib32", basename))
    lib64 = os.path.realpath(os.path.join(path, "lib64", basename))
    lib = os.path.realpath(os.path.join(path, "lib", basename))
    if lib32 == lib or not os.path.exists(lib32):
        ldpath = ":".join([lib64, lib])
    elif lib64 == lib or not os.path.exists(lib64):
        ldpath = ":".join([lib, lib32])
    else:
        ldpath = lib if os.path.exists(lib) else lib64
    return ldpath


def get_wine_environment(executable: str = None, prefix: str = None) -> Dict:
    # If the tool is unset, return all affected env variable names
    # IMPORTANT: keep this in sync with the code below
    environ = {"WINEPREFIX": prefix if prefix is not None else ""}
    if executable is None:
        environ["WINEDLLPATH"] = ""
        environ["LD_LIBRARY_PATH"] = ""
    else:
        winedllpath = __get_lib_path(executable, "wine")
        environ["WINEDLLPATH"] = winedllpath
        librarypath = __get_lib_path(executable, "")
        environ["LD_LIBRARY_PATH"] = librarypath
    return environ


if __name__ == "__main__":
    from pprint import pprint

    pprint(get_wine_environment(
        "/opt/wine-ge-custom/bin/wine", None))
    pprint(get_wine_environment(
        "/usr/bin/wine", None))
    pprint(get_wine_environment(
        "/usr/share/steam/compatitiblitytools.d/dist/bin/wine", None))
    pprint(get_wine_environment(
        os.path.expanduser("~/.local/share/Steam/compatibilitytools.d/GE-Proton8-14/files/bin/wine"), None))
    pprint(get_wine_environment(
        os.path.expanduser("~/.local/share/lutris/runners/wine/lutris-GE-Proton8-14-x86_64/bin/wine"), None))
