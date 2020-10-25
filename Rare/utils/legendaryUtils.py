import os
from argparse import Namespace
from distutils.util import strtobool

from legendary.cli import LegendaryCLI
from legendary.core import LegendaryCore


core = LegendaryCore()
cli = LegendaryCLI()


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


def start(game_name,
          offline=False,
          skip_version_check=False,
          reset_defaults=None,
          set_defaults=None,
          wine_bin=os.environ.get('LGDRY_WINE_BINARY', None),
          wine_pfx=os.environ.get('LGDRY_WINE_PREFIX', None),
          no_wine=strtobool(os.environ.get('LGDRY_NO_WINE', 'False')),
          debug=False,
          dry_run=False,
          user_name_override=None,
          language=None
          ):
    cli.launch_game(Namespace(app_name=game_name,
                              offline=offline,
                              wrapper=os.environ.get('LGDRY_WRAPPER', None),
                              skip_version_check=skip_version_check,
                              reset_defaults=reset_defaults,
                              set_defaults=set_defaults,
                              wine_bin=wine_bin,
                              wine_pfx=wine_pfx,
                              no_wine=no_wine,
                              debug=debug,
                              dry_run=dry_run,
                              user_name_override=user_name_override,
                              language=language
                              ),
                    [] # Extra
                    )

# start("Sugar")
