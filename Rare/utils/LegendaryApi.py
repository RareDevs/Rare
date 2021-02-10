import os

from PyQt5.QtCore import QProcess, QProcessEnvironment
from legendary.core import LegendaryCore




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