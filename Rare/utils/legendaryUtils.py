import subprocess

from legendary.cli import LegendaryCLI
from legendary.core import LegendaryCore

core = LegendaryCore()
cli = LegendaryCLI


def get_installed():
    return core.get_installed_list()


def get_installed_names():
    names = []
    for i in core.get_installed_list():
        names.append(i.app_name)
    return names

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

def get_games_by_name():
    if not core.login():
        print("Login Failed")
        exit(1)
    game = []
    for i in core.get_game_list():
        game.append(i.app_name)

def get_game_by_name(name: str):
    return core.get_game(name)

def get_games():
    if not core.login():
        print("Login Failed")
        exit(1)
    return core.get_game_list()


def start(game_name: str, args):
    subprocess.run(["legendary", "launch", game_name])

