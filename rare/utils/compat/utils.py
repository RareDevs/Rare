import os
import platform as pf
import subprocess
from configparser import ConfigParser
from logging import getLogger
from typing import Mapping, Dict, List, Tuple

from PySide6.QtCore import QProcess, QProcessEnvironment

if pf.system() != "Windows":
    if pf.system() in {"Linux", "FreeBSD"}:
        pass

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


def prepare_process(command: List[str], environment: Dict) -> Tuple[str, List[str], Dict]:
    logger.debug("Preparing process: %s", command)
    _env = os.environ.copy()
    _command = command.copy()
    if os.environ.get("container") == "flatpak":
        flatpak_command = ["flatpak-spawn", "--host"]
        flatpak_command.extend(f"--env={name}={value}" for name, value in environment.items())
        _command = flatpak_command + command
    else:
        _env.update(environment)
    return  _command[0], _command[1:] if len(_command) > 1 else [], _env


def dict_to_qprocenv(env: Dict) -> QProcessEnvironment:
    _env = QProcessEnvironment()
    for name, value in env.items():
        _env.insert(name, value)
    return _env


def get_configured_qprocess(command: List[str], environment: Dict) -> QProcess:
    cmd, args, env = prepare_process(command, environment)
    proc = QProcess()
    proc.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)
    proc.setProcessEnvironment(dict_to_qprocenv(env))
    proc.setProgram(cmd)
    proc.setArguments(args)
    return proc


def get_configured_subprocess(command: List[str], environment: Dict) -> subprocess.Popen:
    cmd, args, env = prepare_process(command, environment)
    return subprocess.Popen(
        (cmd, *args),
        stdin=None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        shell=False,
        text=False,
    )


def execute_subprocess(command: List[str], arguments: List[str], environment: Mapping) -> Tuple[str, str]:
    proc = get_configured_subprocess(command + arguments, environment)
    out, err = proc.communicate()
    out, err = out.decode("utf-8", "ignore") if out else "", err.decode("utf-8", "ignore") if err else ""

    # lk: the following is a work-around for wineserver sometimes hanging around after
    proc = get_configured_subprocess(command + ["wineboot", "-e"], environment)
    _, _ = proc.communicate()
    return out, err


def execute_qprocess(command: List[str], arguments: List[str], environment: Mapping) -> Tuple[str, str]:
    logger.debug("WINEPREFIX: %s", environment.get("WINEPREFIX", None))
    logger.debug("STEAM_COMPAT_DATA_PATH: %s", environment.get("STEAM_COMPAT_DATA_PATH", None))
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
    try:
        out, err = execute_qprocess(command, arguments, environment)
    except Exception as e:
        out, err = "", str(e)

    return out, err


def resolve_path(command: List[str], environment: Mapping, path: str) -> str:
    path = path.strip().replace("/", "\\")
    # lk: if path does not exist form
    arguments = ["c:\\windows\\system32\\cmd.exe", "/c", "echo", path]
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
    arguments = ["c:\\windows\\system32\\reg.exe", "query", reg_path, "/v", reg_key]
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
    arguments = ["c:\\windows\\system32\\winepath.exe", "-u", path]
    out, err = execute(command, arguments, environment)
    out, err = out.strip(), err.strip()
    if not out:
        logger.error("Failed to convert to unix path due to \"%s\"", err)
    return os.path.realpath(out) if (out := out.strip()) else out


def get_host_environment(app_environment: Dict, silent: bool = False) -> Dict:
    # Get a clean environment if we are in flatpak, this environment will be passed
    # to `flatpak-spawn`, otherwise use the system's.
    _environ = app_environment.copy()
    if silent:
        _environ["WINEESYNC"] = "0"
        _environ["WINEFSYNC"] = "0"
        _environ["WINE_DISABLE_FAST_SYNC"] = "1"
        _environ["WINEDEBUG"] = "-all"
        _environ["WINEDLLOVERRIDES"] = "winemenubuilder=d;mscoree=d;mshtml=d;"
        _environ["WINEDLLOVERRIDES"] += "winex11.drv,winewayland.drv=d;"
        # lk: pressure-vessel complains about this but it doesn't fail due to it
        #_environ["DISPLAY"] = ""
    return _environ
