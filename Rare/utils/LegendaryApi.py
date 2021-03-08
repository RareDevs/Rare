import os
from logging import getLogger

from PyQt5.QtCore import QProcess, QProcessEnvironment

logger = getLogger("Legendary Utils")


def launch_game(core, app_name: str, offline: bool = False, skip_version_check: bool = False):
    game = core.get_installed_game(app_name)
    if not game:
        print("Game not found")
        return None
    if game.is_dlc:
        print("Game is dlc")
        return None
    if not os.path.exists(game.install_path):
        print("Game doesn't exist")
        return None

    if not offline:

        if not skip_version_check and not core.is_noupdate_game(app_name):
            # check updates
            try:
                latest = core.get_asset(app_name, update=True)
            except ValueError:
                print("Metadata doesn't exist")
                return None
            if latest.build_version != game.version:
                print("Please update game")
                return None
    params, cwd, env = core.get_launch_parameters(app_name=app_name, offline=offline)
    process = QProcess()
    process.setWorkingDirectory(cwd)
    environment = QProcessEnvironment()
    for e in env:
        environment.insert(e, env[e])
    process.setProcessEnvironment(environment)
    process.start(params[0], params[1:])
    return process


def uninstall(app_name: str, core):
    igame = core.get_installed_game(app_name)
    try:
        # Remove DLC first so directory is empty when game uninstall runs
        dlcs = core.get_dlc_for_game(app_name)
        for dlc in dlcs:
            if (idlc := core.get_installed_game(dlc.app_name)) is not None:
                logger.info(f'Uninstalling DLC "{dlc.app_name}"...')
                core.uninstall_game(idlc, delete_files=True)

        logger.info(f'Removing "{igame.title}" from "{igame.install_path}"...')
        core.uninstall_game(igame, delete_files=True, delete_root_directory=True)
        logger.info('Game has been uninstalled.')

    except Exception as e:
        logger.warning(f'Removing game failed: {e!r}, please remove {igame.install_path} manually.')
