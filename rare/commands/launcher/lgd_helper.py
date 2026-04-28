import os
import platform
import shlex
import shutil
from argparse import Namespace
from dataclasses import dataclass, field
from logging import getLogger

from legendary.models.game import LaunchParameters
from PySide6.QtCore import QProcess, QProcessEnvironment

from rare.models.game_slim import RareGameSlim
from rare.utils.compat.utils import create_compat_users
from rare.utils.paths import setup_compat_shaders_dir

logger = getLogger('RareLauncherUtils')


class GameArgsError(Exception):
    pass


class InitParams(Namespace):
    app_name: str
    offline: bool = False
    debug: bool = False
    dry_run: bool = False
    show_console: bool = False
    skip_update_check: bool = False
    wine_prefix: str = ''
    wine_bin: str = ''

    @classmethod
    def from_argparse(cls, args):
        return cls(
            app_name=args.app_name,
            offline=args.offline,
            debug=args.debug,
            dry_run=args.dry_run,
            show_console=args.show_console,
            skip_update_check=args.skip_update_check,
            wine_bin=args.wine_bin if hasattr(args, 'wine_bin') else '',
            wine_prefix=args.wine_pfx if hasattr(args, 'wine_prefix') else '',
        )


@dataclass
class LaunchParams:
    executable: str = ''
    arguments: list[str] = field(default_factory=list)
    working_directory: str = ''
    environment: dict[str, str] = field(default_factory=dict)
    pre_launch_command: str = ''
    pre_launch_wait: bool = False
    is_third_party_game: bool = False  # only for windows to launch as url

    def __bool__(self):
        return bool(self.executable)


def get_third_party_params(rgame: RareGameSlim, init: InitParams, launch: LaunchParams) -> LaunchParams:
    core = rgame.core
    app_name = rgame.app_name

    uri = (
        core.get_origin_uri(app_name, init.offline)
        if rgame.is_origin
        else core.get_ubisoft_uri(app_name, init.offline)
    )
    if platform.system() == 'Windows':
        command = [uri]
    else:
        command = core.get_app_launch_command(app_name)
        if not os.path.exists(command[0]) and shutil.which(command[0]) is None:
            return launch
        command.append(uri)

    exe, args, env = prepare_process(command, core.get_app_environment(app_name))

    launch.is_third_party_game = True
    launch.executable = exe
    launch.arguments = args
    launch.environment = env

    return launch


def get_game_params(rgame: RareGameSlim, init: InitParams, launch: LaunchParams) -> LaunchParams:
    if not init.offline:  # skip for update
        if not init.skip_update_check and not rgame.core.is_noupdate_game(rgame.app_name):
            try:
                latest = rgame.core.get_asset(rgame.app_name, rgame.igame.platform, update=False)
            except ValueError as exc:
                raise GameArgsError("Metadata doesn't exist") from exc
            else:
                if latest.build_version != rgame.igame.version:
                    raise GameArgsError('Game is not up to date. Please update first')

    if (not rgame.igame or not rgame.igame.executable) and rgame.game is not None:
        # override installed game with base title
        if rgame.is_launchable_addon:
            app_name = rgame.game.metadata['mainGameItem']['releaseInfo'][0]['appId']
            rgame.igame = rgame.core.get_installed_game(app_name)

    try:
        params: LaunchParameters = rgame.core.get_launch_parameters(
            app_name=rgame.igame.app_name, offline=init.offline, addon_app_name=rgame.game.app_name
        )
    except TypeError:
        logger.warning('Using older get_launch_parameters due to legendary version')
        params: LaunchParameters = rgame.core.get_launch_parameters(app_name=rgame.igame.app_name, offline=init.offline)

    full_params = []
    full_params.extend(params.launch_command)
    if 'LEGENDARY_WRAPPER_EXE' in params.environment:
        lgd_wrapper = params.environment.pop('LEGENDARY_WRAPPER_EXE', '').strip()
        if lgd_wrapper and os.path.isfile(lgd_wrapper):
            full_params.append(lgd_wrapper)
    full_params.append(os.path.join(params.game_directory, params.game_executable))
    full_params.extend(params.game_parameters)
    full_params.extend(params.egl_parameters)
    full_params.extend(params.user_parameters)

    _exe, _init, _env = prepare_process(full_params, params.environment)
    launch.executable = _exe
    launch.arguments = _init
    launch.environment = _env
    launch.working_directory = params.working_directory

    return launch


def get_launch_params(rgame: RareGameSlim, init: InitParams = None) -> LaunchParams:
    resp = LaunchParams()

    if not rgame.game:
        raise GameArgsError(f'Could not find metadata for {rgame.app_title}')

    if rgame.is_third_party:
        init.offline = False
    else:
        if not rgame.is_installed:
            raise GameArgsError('Game is not installed or has unsupported format')

        if rgame.is_dlc and not rgame.is_launchable_addon:
            raise GameArgsError('Game is a DLC')
        if not os.path.exists(rgame.install_path):
            raise GameArgsError('Game path does not exist')

    if rgame.is_third_party:
        resp = get_third_party_params(rgame, init, resp)
    else:
        resp = get_game_params(rgame, init, resp)

    pre_cmd, wait = rgame.core.get_pre_launch_command(init.app_name)
    resp.pre_launch_command, resp.pre_launch_wait = pre_cmd, wait
    return resp


def prepare_process(command: list[str], environment: dict) -> tuple[str, list[str], dict]:
    logger.debug('Preparing process: %s', command)

    _env = environment.copy()
    # Sanity check environment (mostly for Linux)
    # ensure shader compat dirs exist
    if platform.system() in {'Linux', 'FreeBSD'}:
        _cmd_line = shlex.join(command)
        if os.environ.get('XDG_CURRENT_DESKTOP', None) == 'gamescope' or 'gamescope' in _cmd_line:
            # disable mangohud in gamescope
            _env['MANGOHUD'] = '0'
        if 'STEAM_COMPAT_CLIENT_INSTALL_PATH' not in _env:
            _env['STEAM_COMPAT_CLIENT_INSTALL_PATH'] = ''
        if 'STEAM_COMPAT_DATA_PATH' in _env:
            compat_pfx = os.path.join(_env['STEAM_COMPAT_DATA_PATH'], 'pfx')
            os.makedirs(compat_pfx, exist_ok=True)
            create_compat_users(compat_pfx)
        if 'WINEPREFIX' in _env and not os.path.isdir(_env['WINEPREFIX']):
            os.makedirs(_env['WINEPREFIX'], exist_ok=True)
            create_compat_users(_env['WINEPREFIX'])
        if 'STEAM_COMPAT_SHADER_PATH' in _env:
            _env.update(setup_compat_shaders_dir(_env['STEAM_COMPAT_SHADER_PATH']))
        _env['WINEDLLOVERRIDES'] = _env.get('WINEDLLOVERRIDES', '') + ';lsteamclient=d;'

    final_env = os.environ.copy()
    final_cmd = command.copy()

    if os.environ.get('container') == 'flatpak':  # noqa: SIM112
        _flat_cmd = ['flatpak-spawn', '--host']
        _flat_cmd.extend(f'--env={name}={value}' for name, value in _env.items())
        final_cmd = _flat_cmd + command
    else:
        final_env.update(_env)

    return final_cmd[0], final_cmd[1:] if len(final_cmd) > 1 else [], final_env


def dict_to_qprocenv(env: dict) -> QProcessEnvironment:
    _env = QProcessEnvironment()
    for name, value in env.items():
        _env.insert(name, value)
    return _env


def get_configured_qprocess(command: list[str], environment: dict) -> QProcess:
    cmd, args, env = prepare_process(command, environment)
    proc = QProcess()
    proc.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)
    proc.setProcessEnvironment(dict_to_qprocenv(env))
    proc.setProgram(cmd)
    proc.setArguments(args)
    return proc
