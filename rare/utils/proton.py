import os
from dataclasses import dataclass
from logging import getLogger
from typing import Optional, Union, List, Dict

import vdf

logger = getLogger("Proton")

steam_compat_client_install_paths = [os.path.expanduser("~/.local/share/Steam")]


def find_steam() -> str:
    # return the first valid path
    for path in steam_compat_client_install_paths:
        if os.path.isdir(path) and os.path.isfile(os.path.join(path, "steam.sh")):
            return path


def find_libraries(steam_path: str) -> List[str]:
    vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
    with open(vdf_path, "r") as f:
        libraryfolders = vdf.load(f)["libraryfolders"]
    libraries = [os.path.join(folder["path"], "steamapps") for key, folder in libraryfolders.items()]
    return libraries


@dataclass
class SteamBase:
    steam_path: str
    tool_path: str
    toolmanifest: dict

    def __eq__(self, other):
        return self.tool_path == other.tool_path

    def __hash__(self):
        return hash(self.tool_path)

    def commandline(self):
        cmd = "".join([f"'{self.tool_path}'", self.toolmanifest["manifest"]["commandline"]])
        cmd = os.path.normpath(cmd)
        # NOTE: "waitforexitandrun" seems to be the verb used in by steam to execute stuff
        cmd = cmd.replace("%verb%", "waitforexitandrun")
        return cmd


@dataclass
class SteamRuntime(SteamBase):
    steam_library: str
    appmanifest: dict

    def name(self):
        return self.appmanifest["AppState"]["name"]

    def appid(self):
        return self.appmanifest["AppState"]["appid"]


@dataclass
class ProtonTool(SteamRuntime):
    runtime: SteamRuntime = None

    def __bool__(self):
        if appid := self.toolmanifest.get("require_tool_appid", False):
            return self.runtime is not None and self.runtime.appid() == appid

    def commandline(self):
        runtime_cmd = self.runtime.commandline()
        cmd = super().commandline()
        return " ".join([runtime_cmd, cmd])


@dataclass
class CompatibilityTool(SteamBase):
    compatibilitytool: dict
    runtime: SteamRuntime = None

    def __bool__(self):
        if appid := self.toolmanifest.get("require_tool_appid", False):
            return self.runtime is not None and self.runtime.appid() == appid

    def name(self):
        name, data = list(self.compatibilitytool["compatibilitytools"]["compat_tools"].items())[0]
        return data["display_name"]

    def commandline(self):
        runtime_cmd = self.runtime.commandline() if self.runtime is not None else ""
        cmd = super().commandline()
        return " ".join([runtime_cmd, cmd])


def find_appmanifests(library: str) -> List[dict]:
    appmanifests = []
    for entry in os.scandir(library):
        if entry.is_file() and entry.name.endswith(".acf"):
            with open(os.path.join(library, entry.name), "r") as f:
                appmanifest = vdf.load(f)
            appmanifests.append(appmanifest)
    return appmanifests


def find_protons(steam_path: str, library: str) -> List[ProtonTool]:
    protons = []
    appmanifests = find_appmanifests(library)
    common = os.path.join(library, "common")
    for appmanifest in appmanifests:
        folder = appmanifest["AppState"]["installdir"]
        tool_path = os.path.join(common, folder)
        if os.path.isfile(vdf_file := os.path.join(tool_path, "toolmanifest.vdf")):
            with open(vdf_file, "r") as f:
                toolmanifest = vdf.load(f)
                if toolmanifest["manifest"]["compatmanager_layer_name"] == "proton":
                    protons.append(
                        ProtonTool(
                            steam_path=steam_path,
                            steam_library=library,
                            appmanifest=appmanifest,
                            tool_path=tool_path,
                            toolmanifest=toolmanifest,
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
            if entry.is_dir():
                tool_path = os.path.join(path, entry.name)
                tool_vdf = os.path.join(tool_path, "compatibilitytool.vdf")
                manifest_vdf = os.path.join(tool_path, "toolmanifest.vdf")
                if os.path.isfile(tool_vdf) and os.path.isfile(manifest_vdf):
                    with open(tool_vdf, "r") as f:
                        compatibilitytool = vdf.load(f)
                    with open(manifest_vdf, "r") as f:
                        manifest = vdf.load(f)
                    tools.append(
                        CompatibilityTool(
                            steam_path=steam_path,
                            tool_path=tool_path,
                            toolmanifest=manifest,
                            compatibilitytool=compatibilitytool,
                        )
                    )
    return tools


def find_runtimes(steam_path: str, library: str) -> Dict[str, SteamRuntime]:
    runtimes = {}
    appmanifests = find_appmanifests(library)
    common = os.path.join(library, "common")
    for appmanifest in appmanifests:
        folder = appmanifest["AppState"]["installdir"]
        tool_path = os.path.join(common, folder)
        if os.path.isfile(vdf_file := os.path.join(tool_path, "toolmanifest.vdf")):
            with open(vdf_file, "r") as f:
                toolmanifest = vdf.load(f)
                if toolmanifest["manifest"]["compatmanager_layer_name"] == "container-runtime":
                    runtimes.update(
                        {
                            appmanifest["AppState"]["appid"]: SteamRuntime(
                                steam_path=steam_path,
                                steam_library=library,
                                appmanifest=appmanifest,
                                tool_path=tool_path,
                                toolmanifest=toolmanifest,
                            )
                        }
                    )
    return runtimes


def find_runtime(
    tool: Union[ProtonTool, CompatibilityTool], runtimes: Dict[str, SteamRuntime]
) -> Optional[SteamRuntime]:
    required_tool = tool.toolmanifest["manifest"].get("require_tool_appid")
    if required_tool is None:
        return None
    return runtimes[required_tool]


def get_steam_environment(tool: Optional[Union[ProtonTool, CompatibilityTool]], app_name: str = None) -> Dict:
    environ = {}
    # If the tool is unset, return all affected env variable names
    # IMPORTANT: keep this in sync with the code below
    if tool is None:
        environ["STEAM_COMPAT_CLIENT_INSTALL_PATH"] = ""
        environ["STEAM_COMPAT_LIBRARY_PATHS"] = ""
        environ["STEAM_COMPAT_MOUNTS"] = ""
        environ["STEAM_COMPAT_TOOL_PATHS"] = ""
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
    return environ


def find_tools() -> List[Union[ProtonTool, CompatibilityTool]]:
    steam_path = find_steam()
    logger.info("Using Steam install in %s", steam_path)
    steam_libraries = find_libraries(steam_path)
    logger.info("Searching for tools in libraries %s", steam_libraries)

    runtimes = {}
    for library in steam_libraries:
        runtimes.update(find_runtimes(steam_path, library))

    tools = []
    for library in steam_libraries:
        tools.extend(find_protons(steam_path, library))
    tools.extend(find_compatibility_tools(steam_path))

    for tool in tools:
        runtime = find_runtime(tool, runtimes)
        tool.runtime = runtime

    return tools


if __name__ == "__main__":
    from pprint import pprint

    _tools = find_tools()
    pprint(_tools)

    for tool in _tools:
        print(get_steam_environment(tool))
        print(tool.name(), tool.commandline())


def find_proton_combos():
    possible_proton_combos = []
    compatibilitytools_dirs = [
        os.path.expanduser("~/.steam/steam/steamapps/common"),
        "/usr/share/steam/compatibilitytools.d",
        os.path.expanduser("~/.steam/compatibilitytools.d"),
        os.path.expanduser("~/.steam/root/compatibilitytools.d"),
    ]
    for c in compatibilitytools_dirs:
        if os.path.exists(c):
            for i in os.listdir(c):
                proton = os.path.join(c, i, "proton")
                compatibilitytool = os.path.join(c, i, "compatibilitytool.vdf")
                toolmanifest = os.path.join(c, i, "toolmanifest.vdf")
                if os.path.exists(proton) and (
                        os.path.exists(compatibilitytool) or os.path.exists(toolmanifest)
                ):
                    wrapper = f'"{proton}" run'
                    possible_proton_combos.append(wrapper)
    if not possible_proton_combos:
        logger.warning("Unable to find any Proton version")
    return possible_proton_combos
