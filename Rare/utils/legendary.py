import subprocess

from legendary.cli import LegendaryCLI
from legendary.core import LegendaryCore

core = LegendaryCore()
cli = LegendaryCLI


def get_installed():
    return core.get_installed_list()
    # games = sorted(get_installed, key=lambda x: x.title)


def get_installed_names():
    names = []
    for i in core.get_installed_list():
        names.append(i.app_name)
    return names


# return (games, dlcs)
def get_games_and_dlcs():
    if not core.login():
        print("Login Failed")
        exit(1)
    print('Getting game list... (this may take a while)')
    return core.get_game_and_dlc_list()


def get_games():
    if not core.login():
        print("Login Failed")
        exit(1)
    print('Getting game list... (this may take a while)')
    return core.get_game_list()


def start(game_name: str, args):
    subprocess.run(["legendary", "launch", game_name])