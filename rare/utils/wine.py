import os
import shutil
import subprocess
from configparser import ConfigParser
from logging import getLogger
from typing import Mapping, Dict, List, Tuple

from rare.lgndr.core import LegendaryCore

logger = getLogger("Wine")


# this is a copied function from legendary.utils.wine_helpers, but registry file can be specified
def read_registry(registry: str, wine_pfx: str) -> ConfigParser:
    accepted = ["system.reg", "user.reg"]
    if registry not in accepted:
        raise RuntimeError(f'Unknown target "{registry}" not in {accepted}')
    reg = ConfigParser(comment_prefixes=(';', '#', '/', 'WINE'), allow_no_value=True,
                       strict=False)
    reg.optionxform = str
    reg.read(os.path.join(wine_pfx, 'system.reg'))
    return reg


def execute(command: List, wine_env: Mapping) -> Tuple[str, str]:
    if os.environ.get("container") == "flatpak":
        flatpak_command = ["flatpak-spawn", "--host"]
        for name, value in wine_env.items():
            flatpak_command.append(f"--env={name}={value}")
        command = flatpak_command + command
    try:
        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            # Use the current environment if we are in flatpak or our own if we are on host
            # In flatpak our environment is passed through `flatpak-spawn` arguments
            env=os.environ.copy() if os.environ.get("container") == "flatpak" else wine_env,
            shell=False,
            text=True,
        )
        res = proc.communicate()
    except (FileNotFoundError, PermissionError) as e:
        res = ("", str(e))
    return res


def resolve_path(wine_exec: str, wine_env: Mapping, path: str) -> str:
    path = path.strip().replace("/", "\\")
    # lk: if path does not exist form
    cmd = [wine_exec, "cmd", "/c", "echo", path]
    # lk: if path exists and needs a case-sensitive interpretation form
    # cmd = [wine_cmd, 'cmd', '/c', f'cd {path} & cd']
    out, err = execute(cmd, wine_env)
    out, err = out.strip(), err.strip()
    if not out:
        logger.error("Failed to resolve wine path due to \"%s\"", err)
        return out
    return out.strip('"')


def query_reg_path(wine_exec: str, wine_env: Mapping, reg_path: str):
    raise NotImplementedError


def query_reg_key(wine_exec: str, wine_env: Mapping, reg_path: str, reg_key) -> str:
    cmd = [wine_exec, "reg", "query", reg_path, "/v", reg_key]
    out, err = execute(cmd, wine_env)
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


def convert_to_unix_path(wine_exec: str, wine_env: Mapping, path: str) -> str:
    path = path.strip().strip('"')
    cmd = [wine_exec, "winepath.exe", "-u", path]
    out, err = execute(cmd, wine_env)
    out, err = out.strip(), err.strip()
    if not out:
        logger.error("Failed to convert to unix path due to \"%s\"", err)
    return os.path.realpath(out) if (out := out.strip()) else out


def wine(core: LegendaryCore, app_name: str = "default") -> str:
    _wine = core.lgd.config.get(
        app_name, "wine_executable", fallback=core.lgd.config.get(
            "default", "wine_executable", fallback=shutil.which("wine")
        )
    )
    return _wine


def environ(core: LegendaryCore, app_name: str = "default") -> Dict:
    # Get a clean environment if we are in flatpak, this environment will be pass
    # to `flatpak-spawn`, otherwise use the system's.
    _environ = {} if os.environ.get("container") == "flatpak" else os.environ.copy()
    _environ.update(core.get_app_environment(app_name))
    _environ["WINEDEBUG"] = "-all"
    _environ["WINEDLLOVERRIDES"] = "winemenubuilder=d;mscoree=d;mshtml=d;"
    _environ["DISPLAY"] = ""
    return _environ


def prefix(core: LegendaryCore, app_name: str = "default") -> str:
    _prefix = core.lgd.config.get(
        app_name, "wine_prefix", fallback=core.lgd.config.get(
            "default", "wine_prefix", fallback=os.path.expanduser("~/.wine")
        )
    )
    return _prefix if os.path.isdir(_prefix) else ""
