import os
import platform
import shutil
from argparse import Namespace
from dataclasses import dataclass, field
from logging import getLogger
from typing import List

from PySide6.QtCore import QProcess, QProcessEnvironment
from legendary.models.game import LaunchParameters

from rare.models.base_game import RareGameSlim

logger = getLogger("RareLauncherUtils")


class GameArgsError(Exception):
    pass


class InitArgs(Namespace):
    app_name: str
    dry_run: bool = False
    debug: bool = False
    offline: bool = False
    skip_update_check: bool = False
    wine_prefix: str = ""
    wine_bin: str = ""

    @classmethod
    def from_argparse(cls, args):
        return cls(
            app_name=args.app_name,
            debug=args.debug,
            offline=args.offline,
            skip_update_check=args.skip_update_check,
            wine_bin=args.wine_bin,
            wine_prefix=args.wine_pfx,
            dry_run=args.dry_run
        )


@dataclass
class LaunchArgs:
    executable: str = ""
    arguments: List[str] = field(default_factory=list)
    working_directory: str = ""
    environment: QProcessEnvironment = None
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
        launch_args.executable = origin_uri
        launch_args.arguments = []
        # only set it here true, because on linux it is a launch command like every other game
        launch_args.is_origin_game = True
        return launch_args

    command = core.get_app_launch_command(app_name)
    if not os.path.exists(command[0]) and shutil.which(command[0]) is None:
        return launch_args
    command.append(origin_uri)

    env = core.get_app_environment(app_name)
    launch_args.environment = QProcessEnvironment.systemEnvironment()

    if os.environ.get("container") == "flatpak":
        flatpak_command = ["flatpak-spawn", "--host"]
        flatpak_command.extend(f"--env={name}={value}" for name, value in env.items())
        command = flatpak_command + command
    else:
        for name, value in env.items():
            launch_args.environment.insert(name, value)

    launch_args.executable = command[0]
    launch_args.arguments = command[1:]

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
            app_name = rgame.game.metadata['mainGameItem']['releaseInfo'][0]['appId']
            rgame.igame = rgame.core.get_installed_game(app_name)

    try:
        params: LaunchParameters = rgame.core.get_launch_parameters(
            app_name=rgame.igame.app_name, offline=args.offline, addon_app_name=rgame.game.app_name
        )
    except TypeError:
        logger.warning("Using older get_launch_parameters due to legendary version")
        params: LaunchParameters = rgame.core.get_launch_parameters(
            app_name=rgame.igame.app_name, offline=args.offline
        )

    full_params = []
    launch_args.environment = QProcessEnvironment.systemEnvironment()

    if os.environ.get("container") == "flatpak":
        full_params.extend(["flatpak-spawn", "--host"])
        full_params.extend(
            f"--env={name}={value}"
            for name, value in params.environment.items()
        )
    else:
        for name, value in params.environment.items():
            launch_args.environment.insert(name, value)

    full_params.extend(params.launch_command)
    full_params.append(os.path.join(params.game_directory, params.game_executable))
    full_params.extend(params.game_parameters)
    full_params.extend(params.egl_parameters)
    full_params.extend(params.user_parameters)

    launch_args.executable = full_params[0]
    launch_args.arguments = full_params[1:]
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


def get_configured_process(env: dict = None):
    proc = QProcess()
    proc.setProcessChannelMode(QProcess.MergedChannels)
    proc.readyReadStandardOutput.connect(
        lambda: logger.info(
            str(proc.readAllStandardOutput().data(), "utf-8", "ignore")
        )
    )
    environment = QProcessEnvironment.systemEnvironment()
    if env:
        for e in env:
            environment.insert(e, env[e])
    proc.setProcessEnvironment(environment)

    return proc
