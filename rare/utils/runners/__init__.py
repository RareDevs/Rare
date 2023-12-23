import os
import platform
import subprocess
from configparser import ConfigParser
from logging import getLogger
from typing import Mapping, Dict, List, Tuple, Optional

from rare.utils import config_helper as config
if platform.system() != "Windows":
    from . import wine
    if platform.system() != "Darwin":
        from . import proton

logger = getLogger("Runners")


# this is a copied function from legendary.utils.wine_helpers, but registry file can be specified
def read_registry(registry: str, prefix: str) -> ConfigParser:
    accepted = ["system.reg", "user.reg"]
    if registry not in accepted:
        raise RuntimeError(f'Unknown target "{registry}" not in {accepted}')
    reg = ConfigParser(comment_prefixes=(';', '#', '/', 'WINE'), allow_no_value=True,
                       strict=False)
    reg.optionxform = str
    reg.read(os.path.join(prefix, 'system.reg'))
    return reg


def execute(command: List[str], environment: Mapping) -> Tuple[str, str]:
    if os.environ.get("container") == "flatpak":
        flatpak_command = ["flatpak-spawn", "--host"]
        for name, value in environment.items():
            flatpak_command.append(f"--env={name}={value}")
        command = flatpak_command + command
    try:
        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            # Use the current environment if we are in flatpak or our own if we are on host
            # In flatpak our environment is passed through `flatpak-spawn` arguments
            env=os.environ.copy() if os.environ.get("container") == "flatpak" else environment,
            shell=False,
            text=True,
        )
        res = proc.communicate()
    except (FileNotFoundError, PermissionError) as e:
        res = ("", str(e))
    return res


def resolve_path(command: List[str], environment: Mapping, path: str) -> str:
    path = path.strip().replace("/", "\\")
    # lk: if path does not exist form
    cmd = command + ["cmd", "/c", "echo", path]
    # lk: if path exists and needs a case-sensitive interpretation form
    # cmd = [wine_cmd, 'cmd', '/c', f'cd {path} & cd']
    out, err = execute(cmd, environment)
    out, err = out.strip(), err.strip()
    if not out:
        logger.error("Failed to resolve wine path due to \"%s\"", err)
        return out
    return out.strip('"')


def query_reg_path(wine_exec: str, wine_env: Mapping, reg_path: str):
    raise NotImplementedError


def query_reg_key(command: List[str], environment: Mapping, reg_path: str, reg_key) -> str:
    cmd = command + ["reg", "query", reg_path, "/v", reg_key]
    out, err = execute(cmd, environment)
    out, err = out.strip(), err.strip()
    if not out:
        logger.error("Failed to query registry key due to \"%s\"", err)
        return out
    lines = out.split("\n")
    keys: Dict = {}
    for line in lines:
        if line.startswith(" "*4):
            key = [x for x in line.split(" "*4, 3) if bool(x)]
            keys.update({key[0]: key[2]})
    return keys.get(reg_key, "")


def convert_to_windows_path(wine_exec: str, wine_env: Mapping, path: str) -> str:
    raise NotImplementedError


def convert_to_unix_path(command: List[str], environment: Mapping, path: str) -> str:
    path = path.strip().strip('"')
    cmd = command + ["winepath.exe", "-u", path]
    out, err = execute(cmd, environment)
    out, err = out.strip(), err.strip()
    if not out:
        logger.error("Failed to convert to unix path due to \"%s\"", err)
    return os.path.realpath(out) if (out := out.strip()) else out


def get_environment(app_environment: Dict, silent: bool = True) -> Dict:
    # Get a clean environment if we are in flatpak, this environment will be passed
    # to `flatpak-spawn`, otherwise use the system's.
    _environ = {} if os.environ.get("container") == "flatpak" else os.environ.copy()
    _environ.update(app_environment)
    if silent:
        _environ["WINEDEBUG"] = "-all"
        _environ["WINEDLLOVERRIDES"] = "winemenubuilder=d;mscoree=d;mshtml=d;"
        _environ["DISPLAY"] = ""
    return _environ
