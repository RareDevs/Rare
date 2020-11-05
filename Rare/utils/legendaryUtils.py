import logging
import os
import subprocess
from getpass import getuser

from legendary.core import LegendaryCore

core = LegendaryCore()


def get_installed():
    return sorted(core.get_installed_list(), key=lambda name: name.title)


def get_installed_names():
    return [i.app_name for i in core.get_installed_list()]


def get_not_installed():
    games = []
    installed = get_installed_names()
    for game in get_games():
        if not game.app_name in installed:
            games.append(game)
    return games


# return (games, dlcs)
def get_games_and_dlcs():
    if not core.login():
        print("Login Failed")
        exit(1)
    return core.get_game_and_dlc_list()


def get_game_by_name(name: str):
    return core.get_game(name)


def get_games():
    if not core.login():
        print("Login Failed")
        return None

    return sorted(core.get_game_list(), key=lambda x: x.app_title)


def get_games_sorted():
    if not core.login():
        logging.error("No login")


def launch_game(app_name: str, offline: bool = False, skip_version_check: bool = False, username_override=None,
                wine_bin: str = None, wine_prfix: str = None, language: str = None, wrapper=None,
                no_wine: bool = os.name == "nt", extra: [] = None):
    game = core.get_installed_game(app_name)
    if not game:
        return 1
    if game.is_dlc:
        return 1
    if not os.path.exists(game.install_path):
        return 1

    if not offline:
        print("logging in")
        if not core.login():
            return 1
        if not skip_version_check and not core.is_noupdate_game(app_name):
            # check updates
            try:
                latest = core.get_asset(app_name, update=True)
            except ValueError:
                print("Metadata doesn't exist")
                return 1
            if latest.build_version != game.version:
                print("Please update game")
                return 1
    params, cwd, env = core.get_launch_parameters(app_name=app_name, offline=offline,
                                                  extra_args=extra, user=username_override,
                                                  wine_bin=wine_bin, wine_pfx=wine_prfix,
                                                  language=language, wrapper=wrapper,
                                                  disable_wine=no_wine)

    return subprocess.Popen(params, cwd=cwd, env=env)


def auth(sid: str):
    # cli.auth(Namespace(session_id=sid))
    pass


def auth_import(lutris: bool = False, wine_prefix: str = None) -> bool:
    '''
    import Data from existing Egl installation

    :param lutris only linux automate using lutris wine prefix:
    :param wine_prefix only linux path to wine_prefix:
    :return success:
    '''
    print(lutris, wine_prefix)
    # Linux
    if not core.egl.appdata_path:
        lutris_wine_users = os.path.expanduser('~/Games/epic-games-store/drive_c/users')
        wine_pfx_users = None
        if lutris and os.path.exists(lutris_wine_users):
            print(f'Found Lutris EGL WINE prefix at "{lutris_wine_users}"')
            wine_pfx_users = lutris_wine_users

        elif wine_prefix:
            if not os.path.exists(wine_prefix):
                print("invalid path")
            wine_pfx_users = os.path.join(wine_prefix, "drive_c/users")
        else:
            print("insert parameter")
            return False

        appdata_dir = os.path.join(wine_pfx_users, getuser(),
                                   'Local Settings/Application Data/EpicGamesLauncher',
                                   'Saved/Config/Windows')

        if not os.path.exists(appdata_dir):
            print("No EGL appdata")
            return False
        core.egl.appdata_path = appdata_dir

    try:
        if core.auth_import():
            print("Successfully logged in")
            print(f"Logged in as {core.lgd.userdata['displayName']}")
            return True
        else:
            print("Error: No valid session found")
            return False
    except ValueError:
        print("No session found")
        return False


def get_updates():
    update_games = []
    for game in core.get_installed_list():
        update_games.append(game) if get_game_by_name(game.app_name).app_version != game.version else None
    return update_games


def logout():
    core.lgd.invalidate_userdata()


def install(app_name: str, path: str = None):
    subprocess.Popen(f"legendary -y install {app_name}".split(" "))
    # TODO


def login(sid):
    code = core.auth_sid(sid)
    if code != '':
        return core.auth_code(code)
    else:
        return False

def get_name():
    return core.lgd.userdata["displayName"]