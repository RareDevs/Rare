import os
import platform
import shutil
from argparse import Namespace
from dataclasses import dataclass
from logging import getLogger
from typing import List

from PyQt5.QtCore import QProcess, QProcessEnvironment
from legendary.models.game import InstalledGame, LaunchParameters

from rare.lgndr.core import LegendaryCore


logger = getLogger("Helper")


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
    args: List[str] = None
    cwd: str = None
    env: QProcessEnvironment = None
    pre_launch_command: str = ""
    pre_launch_wait: bool = False
    is_origin_game: bool = False  # only for windows to launch as url

    def __bool__(self):
        return bool(self.executable)


def get_origin_params(core: LegendaryCore, app_name, offline: bool,
                      launch_args: LaunchArgs) -> LaunchArgs:
    origin_uri = core.get_origin_uri(app_name, offline)
    if platform.system() == "Windows":
        launch_args.executable = origin_uri
        launch_args.args = []
        # only set it here true, because on linux it is a launch command like every other game
        launch_args.is_origin_game = True
        return launch_args

    command = core.get_app_launch_command(app_name)
    if not os.path.exists(command[0]) and shutil.which(command[0]) is None:
        return launch_args
    command.append(origin_uri)

    env = core.get_app_environment(app_name)
    launch_args.env = QProcessEnvironment.systemEnvironment()
    for name, value in env.items():
        launch_args.env.insert(name, value)

    launch_args.executable = command[0]
    launch_args.args = command[1:]
    return launch_args


def get_game_params(core: LegendaryCore, igame: InstalledGame, args: InitArgs,
                    launch_args: LaunchArgs) -> LaunchArgs:
    if not args.offline:  # skip for update
        if not args.skip_update_check and not core.is_noupdate_game(igame.app_name):
            print("Checking for updates...")
            # check updates
            try:
                latest = core.get_asset(
                    igame.app_name, igame.platform, update=False
                )
            except ValueError:
                raise GameArgsError("Metadata doesn't exist")
            else:
                if latest.build_version != igame.version:
                    raise GameArgsError("Game is not up to date. Please update first")

    params: LaunchParameters = core.get_launch_parameters(
        app_name=igame.app_name, offline=args.offline
    )

    full_params = list()

    if os.environ.get("container") == "flatpak":
        full_params.extend(["flatpak-spawn", "--host"])

    full_params.extend(params.launch_command)
    full_params.append(
        os.path.join(params.game_directory, params.game_executable)
    )
    full_params.extend(params.game_parameters)
    full_params.extend(params.egl_parameters)
    full_params.extend(params.user_parameters)

    launch_args.executable = full_params[0]
    launch_args.args = full_params[1:]

    launch_args.env = QProcessEnvironment.systemEnvironment()
    for name, value in params.environment.items():
        launch_args.env.insert(name, value)
    launch_args.cwd = params.working_directory
    return launch_args


def get_launch_args(core: LegendaryCore, args: InitArgs = None) -> LaunchArgs:
    game = core.get_game(args.app_name)
    igame = core.get_installed_game(args.app_name)

    resp = LaunchArgs()

    if not game:
        raise GameArgsError(f"Could not find metadata for ")

    if game.third_party_store == "Origin":
        args.offline = False
    else:
        if not igame:
            raise GameArgsError("Game is not installed or has unsupported format")

        if game.is_dlc:
            raise GameArgsError("Game is a DLC")
        if not os.path.exists(igame.install_path):
            raise GameArgsError("Game path does not exist")

    if game.third_party_store == "Origin":
        resp = get_origin_params(core, args.app_name, args.offline, resp)
    else:
        resp = get_game_params(core, igame, args, resp)

    pre_cmd, wait = core.get_pre_launch_command(args.app_name)
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
