import os
import platform
import shutil
from argparse import Namespace
from dataclasses import dataclass
from logging import getLogger
from typing import List, Tuple

from PyQt5.QtCore import QProcess, QProcessEnvironment
from legendary.core import LegendaryCore
from legendary.models.game import InstalledGame, LaunchParameters

logger = getLogger("Helper")


@dataclass
class InitArgs:
    app_name: str
    offline: bool = False
    skip_version_check: bool = False
    wine_prefix: str = ""
    wine_bin: str = ""

    @classmethod
    def from_argparse(cls, args):
        return cls(
            app_name=args.app_name,
            offline=args.offline,
            skip_version_check=args.skip_update_check,
            wine_bin=args.wine_bin,
            wine_prefix=args.wine_pfx
        )

@dataclass
class LaunchArgs:
    executable: str = ""
    args: List[str] = None
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
    launch_args.env = QProcessEnvironment()
    for name, value in env:
        launch_args.env.insert(name, value)

    launch_args.executable = command[0]
    launch_args.args = command[1:]
    return launch_args


def get_game_params(core: LegendaryCore, igame: InstalledGame, args: InitArgs,
                    launch_args: LaunchArgs) -> LaunchArgs:
    if not args.offline:  # skip for update
        if not args.skip_version_check and not core.is_noupdate_game(igame.app_name):
            # check updates
            try:
                latest = core.get_asset(
                    igame.app_name, igame.platform, update=False
                )
            except ValueError:
                logger.error("Metadata doesn't exist")
                return launch_args
            else:
                if latest.build_version != igame.version:
                    return launch_args
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

    launch_args.env = QProcessEnvironment()
    for name, value in params.environment.items():
        launch_args.env.insert(name, value)

    return launch_args


def get_launch_args(core: LegendaryCore, args: InitArgs = None) -> LaunchArgs:
    game = core.get_game(args.app_name)
    igame = core.get_installed_game(args.app_name)

    resp = LaunchArgs()

    if not game:
        return resp

    if game.third_party_store == "Origin":
        args.offline = False
    else:
        if not igame:
            logger.error("Game is not installed or has unsupported format")
            return resp

        if game.is_dlc:
            logger.error("Game is dlc")
            return resp
        if not os.path.exists(igame.install_path):
            logger.error("Game path does not exist")
            return resp

    if game.third_party_store == "Origin":
        resp = get_origin_params(core, args.app_name, args.offline, resp)
    else:
        resp = get_game_params(core, igame, args, resp)

    pre_cmd, wait = core.get_pre_launch_command(args.app_name)
    resp.pre_launch_command, resp.pre_launch_wait = pre_cmd, wait
    return resp


def get_configured_process(env: dict = None):
    proc = QProcess()
    proc.readyReadStandardOutput.connect(
        lambda: print(
            str(proc.readAllStandardOutput().data(), "utf-8", "ignore")
        )
    )
    proc.readyReadStandardError.connect(
        lambda: print(
            str(proc.readAllStandardError().data(), "utf-8", "ignore")
        )
    )

    if env:
        environment = QProcessEnvironment()
        for e in env:
            environment.insert(e, env[e])
        proc.setProcessEnvironment(environment)

    return proc
