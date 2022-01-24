import random

from legendary.core import LegendaryCore

core = LegendaryCore()
core.login()

print(
    " ".join(
        map(
            lambda game: game.app_name,
            random.choices(
                list(
                    filter(lambda x: len(x.app_name) != 32, core.get_game_list(False))
                ),
                k=2,
            ),
        )
    )
)
