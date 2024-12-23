import os
import shlex
from dataclasses import dataclass
from enum import Enum
from hashlib import md5
from logging import getLogger
from typing import Optional, Union, List, Dict, Set

import vdf

logger = getLogger("SteamTools")

steam_client_install_paths = [os.path.expanduser("~/.local/share/Steam")]


def find_steam() -> Optional[str]:
    # return the first valid path
    for path in steam_client_install_paths:
        if os.path.isdir(path) and os.path.isfile(os.path.join(path, "steam.sh")):
            return path
    return None


def find_libraries(steam_path: str) -> Set[str]:
    vdf_path = os.path.join(steam_path, "config", "libraryfolders.vdf")
    with open(vdf_path, "r", encoding="utf-8") as f:
        libraryfolders = vdf.load(f)["libraryfolders"]
    # libraries = [os.path.join(folder["path"], "steamapps") for key, folder in libraryfolders.items()]
    libraries = {os.path.join(folder["path"], "steamapps") for key, folder in libraryfolders.items()}
    libraries = set(filter(lambda x: os.path.isdir(x), libraries))
    return libraries


# Notes:
# Anything older than 'Proton 5.13' doesn't have the 'require_tool_appid' attribute.
# Anything older than 'Proton 7.0' doesn't have the 'compatmanager_layer_name' attribute.
# In addition to that, the 'Steam Linux Runtime 1.0 (scout)' runtime lists the
# 'Steam Linux Runtime 2.0 (soldier)' runtime as a dependency and is probably what was
# being used for any version before 5.13.
#
# As a result the following implementation will list versions from 7.0 onwards which honestly
# is a good trade-off for the amount of complexity supporting everything would ensue.


class SteamVerb(Enum):
    RUN = "run"
    WAIT_FOR_EXIT_AND_RUN = "waitforexitandrun"
    RUN_IN_PREFIX = "runinprefix"
    DESTROY_PREFIX = "destroyprefix"
    GET_COMPAT_PATH = "getcompatpath"
    GET_NATIVE_PATH = "getnativepath"
    DEFAULT = WAIT_FOR_EXIT_AND_RUN


@dataclass
class SteamBase:
    steam_path: str
    tool_path: str
    toolmanifest: Dict

    def __eq__(self, other):
        return self.tool_path == other.tool_path

    def __hash__(self):
        return hash(self.tool_path)

    @property
    def required_tool(self) -> Optional[str]:
        return self.toolmanifest.get("require_tool_appid", None)

    @property
    def layer(self) -> Optional[str]:
        return self.toolmanifest.get("compatmanager_layer_name", None)

    def command(self, verb: SteamVerb = SteamVerb.DEFAULT) -> List[str]:
        tool_path = os.path.normpath(self.tool_path)
        cmd = "".join([shlex.quote(tool_path), self.toolmanifest["commandline"]])
        # NOTE: "waitforexitandrun" seems to be the verb used in by steam to execute stuff
        # `run` is used when setting up the environment, so use that if we are setting up the prefix.
        cmd = cmd.replace("%verb%", verb.value)
        return shlex.split(cmd)

    def as_str(self, verb: SteamVerb = SteamVerb.DEFAULT):
        return " ".join(map(shlex.quote, self.command(verb)))

    @property
    def checksum(self) -> str:
        return md5(self.as_str().encode("utf-8")).hexdigest()


@dataclass
class SteamRuntime(SteamBase):
    steam_library: str
    appmanifest: Dict

    @property
    def name(self) -> str:
        return self.appmanifest["AppState"]["name"]

    @property
    def appid(self) -> str:
        return self.appmanifest["AppState"]["appid"]


@dataclass
class SteamAntiCheat:
    steam_path: str
    tool_path: str
    steam_library: str
    appmanifest: Dict

    def __eq__(self, other):
        return self.tool_path == other.tool_path

    def __hash__(self):
        return hash(self.tool_path)

    @property
    def name(self) -> str:
        return self.appmanifest["AppState"]["name"]

    @property
    def appid(self) -> str:
        return self.appmanifest["AppState"]["appid"]


@dataclass
class ProtonTool(SteamRuntime):
    runtime: SteamRuntime = None
    anticheat: Dict[str, SteamAntiCheat] = None

    def __bool__(self) -> bool:
        if appid := self.required_tool:
            return self.runtime is not None and self.runtime.appid == appid
        return True

    def command(self, verb: SteamVerb = SteamVerb.DEFAULT) -> List[str]:
        cmd = self.runtime.command(verb)
        cmd.extend(super().command(verb))
        return cmd


@dataclass
class CompatibilityTool(SteamBase):
    compatibilitytool: Dict
    runtime: SteamRuntime = None
    anticheat: Dict[str, SteamAntiCheat] = None

    def __bool__(self) -> bool:
        if appid := self.required_tool:
            return self.runtime is not None and self.runtime.appid == appid
        return True

    @property
    def name(self) -> str:
        return self.compatibilitytool["display_name"]

    def command(self, verb: SteamVerb = SteamVerb.DEFAULT) -> List[str]:
        cmd = self.runtime.command(verb) if self.runtime is not None else []
        cmd.extend(super().command(verb))
        return cmd


def find_appmanifests(library: str) -> List[dict]:
    appmanifests = []
    for entry in os.scandir(library):
        if entry.is_file() and entry.name.endswith(".acf"):
            with open(os.path.join(library, entry.name), "r", encoding="utf-8") as f:
                appmanifest = vdf.load(f)
            appmanifests.append(appmanifest)
    return appmanifests


ANTICHEAT_RUNTIMES = {
    "eac_runtime": "1826330",
    "battleye_runtime": "1161040",
}


def find_anticheat(steam_path: str, library: str):
    runtimes = {}
    appmanifests = find_appmanifests(library)
    common = os.path.join(library, "common")
    for appmanifest in appmanifests:
        if appmanifest["AppState"]["appid"] not in ANTICHEAT_RUNTIMES.values():
            continue
        folder = appmanifest["AppState"]["installdir"]
        runtimes.update(
            {
                appmanifest["AppState"]["appid"]: SteamAntiCheat(
                    steam_path=steam_path,
                    steam_library=library,
                    appmanifest=appmanifest,
                    tool_path=os.path.join(common, folder),
                )
            }
        )
    return runtimes


def find_runtimes(steam_path: str, library: str) -> Dict[str, SteamRuntime]:
    runtimes = {}
    appmanifests = find_appmanifests(library)
    common = os.path.join(library, "common")
    for appmanifest in appmanifests:
        folder = appmanifest["AppState"]["installdir"]
        tool_path = os.path.join(common, folder)
        if os.path.isfile(vdf_file := os.path.join(tool_path, "toolmanifest.vdf")):
            with open(vdf_file, "r", encoding="utf-8") as f:
                toolmanifest = vdf.load(f)
                if toolmanifest["manifest"]["compatmanager_layer_name"] == "container-runtime":
                    runtimes.update(
                        {
                            appmanifest["AppState"]["appid"]: SteamRuntime(
                                steam_path=steam_path,
                                steam_library=library,
                                appmanifest=appmanifest,
                                tool_path=tool_path,
                                toolmanifest=toolmanifest["manifest"],
                            )
                        }
                    )
    return runtimes


def find_protons(steam_path: str, library: str) -> List[ProtonTool]:
    protons = []
    appmanifests = find_appmanifests(library)
    common = os.path.join(library, "common")
    for appmanifest in appmanifests:
        folder = appmanifest["AppState"]["installdir"]
        tool_path = os.path.join(common, folder)
        if os.path.isfile(vdf_file := os.path.join(tool_path, "toolmanifest.vdf")):
            with open(vdf_file, "r", encoding="utf-8") as f:
                toolmanifest = vdf.load(f)
                if toolmanifest["manifest"]["compatmanager_layer_name"] == "proton":
                    protons.append(
                        ProtonTool(
                            steam_path=steam_path,
                            steam_library=library,
                            appmanifest=appmanifest,
                            tool_path=tool_path,
                            toolmanifest=toolmanifest["manifest"],
                        )
                    )
    return protons


def find_compatibility_tools(steam_path: str) -> List[CompatibilityTool]:
    compatibilitytools_paths = {
        "/usr/share/steam/compatibilitytools.d",
        os.path.expanduser(os.path.join(steam_path, "compatibilitytools.d")),
        os.path.expanduser("~/.steam/compatibilitytools.d"),
        os.path.expanduser("~/.steam/root/compatibilitytools.d"),
    }
    compatibilitytools_paths = {
        os.path.realpath(path) for path in compatibilitytools_paths if os.path.isdir(path)
    }
    tools = []
    for path in compatibilitytools_paths:
        for entry in os.scandir(path):
            entry_path = os.path.join(path, entry.name)
            if entry.is_dir():
                tool_vdf = os.path.join(entry_path, "compatibilitytool.vdf")
            elif entry.is_file() and entry.name.endswith(".vdf"):
                tool_vdf = entry_path
            else:
                continue

            if not os.path.isfile(tool_vdf):
                continue

            with open(tool_vdf, "r", encoding="utf-8") as f:
                compatibilitytool = vdf.load(f)

            entry_tools = compatibilitytool["compatibilitytools"]["compat_tools"]
            for entry_tool in entry_tools.values():
                if entry_tool["from_oslist"] != "windows" and entry_tool["to_oslist"] != "linux":
                    continue

                install_path = entry_tool["install_path"]
                tool_path = os.path.abspath(os.path.join(os.path.dirname(tool_vdf), install_path))
                manifest_vdf = os.path.join(tool_path, "toolmanifest.vdf")

                if not os.path.isfile(manifest_vdf):
                    continue

                with open(manifest_vdf, "r", encoding="utf-8") as f:
                    manifest = vdf.load(f)

                tools.append(
                    CompatibilityTool(
                        steam_path=steam_path,
                        tool_path=tool_path,
                        toolmanifest=manifest["manifest"],
                        compatibilitytool=entry_tool,
                    )
                )
    return tools


def get_runtime(
    tool: Union[ProtonTool, CompatibilityTool], runtimes: Dict[str, SteamRuntime]
) -> Optional[SteamRuntime]:
    required_tool = tool.required_tool
    if required_tool is None:
        return None
    return runtimes.get(required_tool, None)


def get_umu_environment(
    tool: Optional[ProtonTool] = None, compat_path: Optional[str] = None
) -> Dict:
    # If the tool is unset, return all affected env variable names
    # IMPORTANT: keep this in sync with the code below
    environ = {"WINEPREFIX": compat_path if compat_path else ""}
    if tool is None:
        environ["WINEPREFIX"] = ""
        environ["PROTONPATH"] = ""
        environ["GAMEID"] = ""
        environ["STORE"] = ""
        return environ

    environ["PROTONPATH"] = tool.tool_path
    environ["STORE"] = "egs"
    return environ


def get_steam_environment(
    tool: Optional[Union[ProtonTool, CompatibilityTool]] = None, compat_path: Optional[str] = None
) -> Dict:
    # If the tool is unset, return all affected env variable names
    # IMPORTANT: keep this in sync with the code below
    environ = {"STEAM_COMPAT_DATA_PATH": compat_path if compat_path else ""}
    if tool is None:
        environ["STEAM_COMPAT_DATA_PATH"] = ""
        environ["STEAM_COMPAT_CLIENT_INSTALL_PATH"] = ""
        environ["STEAM_COMPAT_LIBRARY_PATHS"] = ""
        environ["STEAM_COMPAT_MOUNTS"] = ""
        environ["STEAM_COMPAT_TOOL_PATHS"] = ""
        environ["PROTON_EAC_RUNTIME"] = ""
        environ["PROTON_BATTLEYE_RUNTIME"] = ""
        return environ

    environ["STEAM_COMPAT_CLIENT_INSTALL_PATH"] = tool.steam_path
    if isinstance(tool, ProtonTool):
        environ["STEAM_COMPAT_LIBRARY_PATHS"] = tool.steam_library
    if tool.runtime is not None:
        compat_mounts = [tool.tool_path, tool.runtime.tool_path]
        environ["STEAM_COMPAT_MOUNTS"] = ":".join(compat_mounts)
    tool_paths = [tool.tool_path]
    if tool.runtime is not None:
        tool_paths.append(tool.runtime.tool_path)
    environ["STEAM_COMPAT_TOOL_PATHS"] = ":".join(tool_paths)
    if tool.anticheat is not None:
        if (appid := ANTICHEAT_RUNTIMES["eac_runtime"]) in tool.anticheat.keys():
            environ["PROTON_EAC_RUNTIME"] = tool.anticheat[appid].tool_path
        if (appid := ANTICHEAT_RUNTIMES["battleye_runtime"]) in tool.anticheat.keys():
            environ["PROTON_BATTLEYE_RUNTIME"] = tool.anticheat[appid].tool_path
    return environ


def _find_tools() -> List[Union[ProtonTool, CompatibilityTool]]:
    steam_path = find_steam()
    if steam_path is None:
        logger.info("Steam could not be found")
        return []
    logger.info("Found Steam in %s", steam_path)

    steam_libraries = find_libraries(steam_path)
    logger.debug("Searching for tools in libraries:")
    logger.debug("%s", steam_libraries)

    runtimes = {}
    for library in steam_libraries:
        runtimes.update(find_runtimes(steam_path, library))

    anticheat = {}
    for library in steam_libraries:
        anticheat.update(find_anticheat(steam_path, library))

    tools = []
    for library in steam_libraries:
        tools.extend(find_protons(steam_path, library))
    tools.extend(find_compatibility_tools(steam_path))

    for tool in tools:
        runtime = get_runtime(tool, runtimes)
        tool.runtime = runtime
        if tool.layer == "proton":
            tool.anticheat = anticheat

    tools = list(filter(lambda t: bool(t), tools))

    return tools


_tools: Optional[List[Union[ProtonTool, CompatibilityTool]]] = None


def find_tools() -> List[Union[ProtonTool, CompatibilityTool]]:
    global _tools
    if _tools is None:
        _tools = _find_tools()
    return list(filter(lambda t: t.layer != "umu-launcher", _tools))


def find_umu_launcher() -> Optional[CompatibilityTool]:
    global _tools
    if _tools is None:
        _tools = _find_tools()
    _umu = list(filter(lambda t: t.layer == "umu-launcher",  _tools))
    return _umu[0] if _umu else None


if __name__ == "__main__":
    from pprint import pprint

    tools = find_tools()
    for tool in tools:
        pprint(tool)
    umu = find_umu_launcher()
    pprint(umu)


    for tool in tools:
        print(get_steam_environment(tool))
        print(tool.name)
        print(tool.command(SteamVerb.RUN))
        print(" ".join(tool.command(SteamVerb.RUN_IN_PREFIX)))
