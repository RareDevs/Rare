import os
import shutil
import subprocess
from configparser import ConfigParser
from typing import Mapping, Dict, List, Tuple

from rare.lgndr.core import LegendaryCore


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


def execute(cmd: List, wine_env: Mapping) -> Tuple[str, str]:
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=wine_env,
        shell=False,
        text=True,
    )
    return proc.communicate()


def resolve_path(wine_exec: str, wine_env: Mapping, path: str) -> str:
    path = path.strip().replace("/", "\\")
    # lk: if path does not exist form
    cmd = [wine_exec, "cmd", "/c", "echo", path]
    # lk: if path exists and needs a case-sensitive interpretation form
    # cmd = [wine_cmd, 'cmd', '/c', f'cd {path} & cd']
    out, err = execute(cmd, wine_env)
    return out.strip().strip('"')


def query_reg_path(wine_exec: str, wine_env: Mapping, reg_path: str):
    raise NotImplementedError


def query_reg_key(wine_exec: str, wine_env: Mapping, reg_path: str, reg_key) -> str:
    cmd = [wine_exec, "reg", "query", reg_path, "/v", reg_key]
    out, err = execute(cmd, wine_env)
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
    cmd = [winepath(wine_exec), "-u", path]
    out, err = execute(cmd, wine_env)
    return os.path.realpath(out.strip())


def winepath(wine_exec: str) -> str:
    _winepath = os.path.join(os.path.dirname(wine_exec), "winepath")
    if not os.path.isfile(_winepath):
        return ""
    return _winepath


def wine(core: LegendaryCore, app_name: str = "default") -> str:
    _wine = core.lgd.config.get(
        app_name, "wine_executable", fallback=core.lgd.config.get(
            "default", "wine_executable", fallback=shutil.which("wine")
        )
    )
    return _wine


def environ(core: LegendaryCore, app_name: str = "default") -> Dict:
    _environ = os.environ.copy()
    _environ.update(core.get_app_environment(app_name))
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
