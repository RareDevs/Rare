import os
import platform as pf
import subprocess
from configparser import ConfigParser
from logging import getLogger
from typing import Mapping, Dict, List, Tuple

from PySide6.QtCore import QProcess, QProcessEnvironment

from rare.utils import config_helper as config
if pf.system() != "Windows":
    from . import wine
    if pf.system() in {"Linux", "FreeBSD"}:
        from . import steam

logger = getLogger("CompatUtils")


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


def get_configured_qprocess(command: List[str], environment: Mapping) -> QProcess:
    logger.debug("Executing command: %s", command)
    proc = QProcess()
    proc.setProcessChannelMode(QProcess.SeparateChannels)
    penv = QProcessEnvironment()
    for ek, ev in environment.items():
        penv.insert(ek, ev)
    proc.setProcessEnvironment(penv)
    proc.setProgram(command[0])
    proc.setArguments(command[1:])
    return proc


def get_configured_subprocess(command: List[str], environment: Mapping) -> subprocess.Popen:
    logger.debug("Executing command: %s", command)
    return subprocess.Popen(
        command,
        stdin=None,
        stdout=subprocess.PIPE,
        stderr=None,
        env=environment,
        shell=False,
        text=False,
    )


def execute_subprocess(command: List[str], arguments: List[str], environment: Mapping) -> Tuple[str, str]:
    proc = get_configured_subprocess(command + arguments, environment)
    print(proc.args)
    out, err = proc.communicate()
    out, err = out.decode("utf-8", "ignore") if out else "", err.decode("utf-8", "ignore") if err else ""

    # lk: the following is a work-around for wineserver sometimes hanging around after
    proc = get_configured_subprocess(command + ["wineboot", "-e"], environment)
    _, _ = proc.communicate()
    return out, err


def execute_qprocess(command: List[str], arguments: List[str], environment: Mapping) -> Tuple[str, str]:
    proc = get_configured_qprocess(command + arguments, environment)
    proc.start()
    proc.waitForFinished(-1)
    out, err = (
        proc.readAllStandardOutput().data().decode("utf-8", "ignore"),
        proc.readAllStandardError().data().decode("utf-8", "ignore")
    )
    proc.deleteLater()

    # lk: the following is a work-around for wineserver sometimes hanging around after
    proc = get_configured_qprocess(command + ["wineboot", "-e"], environment)
    proc.start()
    proc.waitForFinished(-1)
    proc.deleteLater()

    return out, err


def execute(command: List[str], arguments: List[str], environment: Mapping) -> Tuple[str, str]:
    # Use the current environment if we are in flatpak or our own if we are on host
    # In flatpak our environment is passed through `flatpak-spawn` arguments
    if os.environ.get("container") == "flatpak":
        flatpak_command = ["flatpak-spawn", "--host"]
        flatpak_command.extend(f"--env={name}={value}" for name, value in environment.items())
        _command = flatpak_command + command
        _environment = os.environ.copy()
    else:
        _command = command
        _environment = environment

    try:
        out, err = execute_qprocess(_command, arguments, _environment)
    except Exception as e:
        out, err = "", str(e)

    return out, err


def resolve_path(command: List[str], environment: Mapping, path: str) -> str:
    path = path.strip().replace("/", "\\")
    # lk: if path does not exist form
    arguments = ["cmd.exe", "/c", "echo", path]
    # lk: if path exists and needs a case-sensitive interpretation form
    # cmd = [wine_cmd, 'cmd', '/c', f'cd {path} & cd']
    out, err = execute(command, arguments, environment)
    out, err = out.strip(), err.strip()
    if not out:
        logger.error("Failed to resolve wine path due to \"%s\"", err)
        return out
    return out.strip('"')


def query_reg_path(wine_exec: str, wine_env: Mapping, reg_path: str):
    raise NotImplementedError


def query_reg_key(command: List[str], environment: Mapping, reg_path: str, reg_key) -> str:
    arguments = ["reg.exe", "query", reg_path, "/v", reg_key]
    out, err = execute(command, arguments, environment)
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
    arguments = ["winepath.exe", "-u", path]
    out, err = execute(command, arguments, environment)
    out, err = out.strip(), err.strip()
    if not out:
        logger.error("Failed to convert to unix path due to \"%s\"", err)
    return os.path.realpath(out) if (out := out.strip()) else out


def get_host_environment(app_environment: Dict, silent: bool = True) -> Dict:
    # Get a clean environment if we are in flatpak, this environment will be passed
    # to `flatpak-spawn`, otherwise use the system's.
    _environ = {} if os.environ.get("container") == "flatpak" else os.environ.copy()
    _environ.update(app_environment)
    if silent:
        _environ["WINEESYNC"] = "0"
        _environ["WINEFSYNC"] = "0"
        _environ["WINE_DISABLE_FAST_SYNC"] = "1"
        _environ["WINEDEBUG"] = "-all"
        _environ["WINEDLLOVERRIDES"] = "winemenubuilder=d;mscoree=d;mshtml=d;"
        # lk: pressure-vessel complains about this but it doesn't fail due to it
        #_environ["DISPLAY"] = ""
    return _environ
