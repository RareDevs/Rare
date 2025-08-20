import os
import platform
import shlex
import shutil
from argparse import Namespace
from dataclasses import dataclass, field
from logging import getLogger
from typing import List, Dict, Tuple

from PySide6.QtCore import QProcess, QProcessEnvironment
from legendary.models.game import LaunchParameters

from rare.models.base_game import RareGameSlim
from rare.utils.paths import setup_compat_shaders_dir

logger = getLogger("RareLauncherUtils")


class GameArgsError(Exception):
    pass


class InitArgs(Namespace):
    app_name: str
    offline: bool = False
    debug: bool = False
    dry_run: bool = False
    show_console: bool = False
    skip_update_check: bool = False
    wine_prefix: str = ""
    wine_bin: str = ""

    @classmethod
    def from_argparse(cls, args):
        return cls(
            app_name=args.app_name,
            offline=args.offline,
            debug=args.debug,
            dry_run=args.dry_run,
            show_console=args.show_console,
            skip_update_check=args.skip_update_check,
            wine_bin=args.wine_bin if hasattr(args, "wine_bin") else "",
            wine_prefix=args.wine_pfx if hasattr(args, "wine_prefix") else "",
        )


@dataclass
class LaunchArgs:
    executable: str = ""
    arguments: List[str] = field(default_factory=list)
    working_directory: str = ""
    environment: Dict[str, str] = field(default_factory=dict)
    pre_launch_command: str = ""
    pre_launch_wait: bool = False
    is_origin_game: bool = False  # only for windows to launch as url

    def __bool__(self):
        return bool(self.executable)


def get_origin_params(rgame: RareGameSlim, init_args: InitArgs, launch_args: LaunchArgs) -> LaunchArgs:
    core = rgame.core
    app_name = rgame.app_name

    origin_uri = core.get_origin_uri(app_name, init_args.offline)
    if platform.system() == "Windows":
        command = [origin_uri]
    else:
        command = core.get_app_launch_command(app_name)
        if not os.path.exists(command[0]) and shutil.which(command[0]) is None:
            return launch_args
        command.append(origin_uri)

    exe, args, env = prepare_process(command, core.get_app_environment(app_name))

    launch_args.is_origin_game = True
    launch_args.executable = exe
    launch_args.arguments = args
    launch_args.environment = env

    return launch_args


def get_game_params(rgame: RareGameSlim, args: InitArgs, launch_args: LaunchArgs) -> LaunchArgs:
    if not args.offline:  # skip for update
        if not args.skip_update_check and not rgame.core.is_noupdate_game(rgame.app_name):
            try:
                latest = rgame.core.get_asset(rgame.app_name, rgame.igame.platform, update=False)
            except ValueError:
                raise GameArgsError("Metadata doesn't exist")
            else:
                if latest.build_version != rgame.igame.version:
                    raise GameArgsError("Game is not up to date. Please update first")

    if (not rgame.igame or not rgame.igame.executable) and rgame.game is not None:
        # override installed game with base title
        if rgame.is_launchable_addon:
            app_name = rgame.game.metadata["mainGameItem"]["releaseInfo"][0]["appId"]
            rgame.igame = rgame.core.get_installed_game(app_name)

    try:
        params: LaunchParameters = rgame.core.get_launch_parameters(
            app_name=rgame.igame.app_name, offline=args.offline, addon_app_name=rgame.game.app_name
        )
    except TypeError:
        logger.warning("Using older get_launch_parameters due to legendary version")
        params: LaunchParameters = rgame.core.get_launch_parameters(app_name=rgame.igame.app_name, offline=args.offline)

    full_params = []
    full_params.extend(params.launch_command)
    full_params.append(os.path.join(params.game_directory, params.game_executable))
    full_params.extend(params.game_parameters)
    full_params.extend(params.egl_parameters)
    full_params.extend(params.user_parameters)

    exe, args, env = prepare_process(full_params, params.environment)

    launch_args.executable = exe
    launch_args.arguments = args
    launch_args.environment = env
    launch_args.working_directory = params.working_directory

    return launch_args


def get_launch_args(rgame: RareGameSlim, init_args: InitArgs = None) -> LaunchArgs:
    resp = LaunchArgs()

    if not rgame.game:
        raise GameArgsError(f"Could not find metadata for {rgame.app_title}")

    if rgame.is_origin:
        init_args.offline = False
    else:
        if not rgame.is_installed:
            raise GameArgsError("Game is not installed or has unsupported format")

        if rgame.is_dlc and not rgame.is_launchable_addon:
            raise GameArgsError("Game is a DLC")
        if not os.path.exists(rgame.install_path):
            raise GameArgsError("Game path does not exist")

    if rgame.is_origin:
        resp = get_origin_params(rgame, init_args, resp)
    else:
        resp = get_game_params(rgame, init_args, resp)

    pre_cmd, wait = rgame.core.get_pre_launch_command(init_args.app_name)
    resp.pre_launch_command, resp.pre_launch_wait = pre_cmd, wait
    return resp


def prepare_process(command: List[str], environment: Dict) -> Tuple[str, List[str], Dict]:
    logger.debug("Preparing process: %s", command)

    environ = environment.copy()
    # Sanity check environment (mostly for Linux)
    command_line = shlex.join(command)
    if os.environ.get("XDG_CURRENT_DESKTOP", None) == "gamescope" or "gamescope" in command_line:
        # disable mangohud in gamescope
        environ["MANGOHUD"] = "0"
    # ensure shader compat dirs exist
    if platform.system() in {"Linux", "FreeBSD"}:
        if "WINEPREFIX" in environ and not os.path.isdir(environ["WINEPREFIX"]):
            os.makedirs(environ["WINEPREFIX"], exist_ok=True)
        if "STEAM_COMPAT_DATA_PATH" in environ:
            compat_pfx = os.path.join(environ["STEAM_COMPAT_DATA_PATH"], "pfx")
            if not os.path.isdir(compat_pfx):
                os.makedirs(compat_pfx, exist_ok=True)
        if "STEAM_COMPAT_SHADER_PATH" in environ:
            environ.update(setup_compat_shaders_dir(environ["STEAM_COMPAT_SHADER_PATH"]))
        environ["WINEDLLOVERRIDES"] = environ.get("WINEDLLOVERRIDES", "") + ";lsteamclient=d;"

    _env = os.environ.copy()
    _command = command.copy()

    if os.environ.get("container") == "flatpak":
        flatpak_command = ["flatpak-spawn", "--host"]
        flatpak_command.extend(f"--env={name}={value}" for name, value in environ.items())
        _command = flatpak_command + command
    else:
        _env.update(environ)

    return _command[0], _command[1:] if len(_command) > 1 else [], _env


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
