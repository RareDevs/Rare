import time
from argparse import Namespace
from enum import IntEnum
from logging import getLogger

from PyQt5.QtCore import QObject, pyqtSignal
from requests.exceptions import ConnectionError, HTTPError

from rare.lgndr.core import LegendaryCore
from .worker import Worker

logger = getLogger("FetchWorker")


class FetchWorker(Worker):
    class Result(IntEnum):
        GAMES = 1
        NON_ASSET = 2
        COMBINED = 3

    class Signals(QObject):
        progress = pyqtSignal(int, str)
        result = pyqtSignal(object, int)

    def __init__(self, core: LegendaryCore, args: Namespace):
        super(Worker, self).__init__()
        self.signals = FetchWorker.Signals()
        self.core = core
        self.args = args

    def run_real(self):
        # Fetch regular EGL games with assets
        self.signals.progress.emit(0, self.signals.tr("Updating game metadata"))
        start_time = time.time()
        games, dlc_dict = self.core.get_game_and_dlc_list(
            update_assets=not self.args.offline, platform="Windows", skip_ue=False
        )
        logger.debug(f"Games {len(games)}, games with DLCs {len(dlc_dict)}")
        logger.debug(f"Request games: {time.time() - start_time} seconds")

        # Fetch non-asset games
        self.signals.progress.emit(10, self.signals.tr("Updating non-asset metadata"))
        start_time = time.time()
        try:
            na_games, na_dlc_dict = self.core.get_non_asset_library_items(force_refresh=False, skip_ue=False)
        except (HTTPError, ConnectionError) as e:
            logger.warning(f"Exception while fetching non asset games from EGS: {e}")
            na_games, na_dlc_dict = ([], {})
        # FIXME:
        #  This is here because of broken appIds from Epic:
        #  https://discord.com/channels/826881530310819914/884510635642216499/1111321692703305729
        #  There is a tab character in the appId of Fallout New Vegas: Honest Hearts DLC, this breaks metadata storage
        #  on Windows as they can't handle tabs at the end of the filename (?)
        #  Legendary and Heroic are also affected, but it completely breaks Rare, so dodge it for now pending a fix.
        except Exception as e:
            logger.error(f"Exception while fetching non asset games from EGS: {e}")
            na_games, na_dlc_dict = ([], {})
        logger.debug(f"Non-asset {len(na_games)}, games with non-asset DLCs {len(na_dlc_dict)}")
        logger.debug(f"Request non-asset: {time.time() - start_time} seconds")

        # Combine the two games lists and the two dlc dictionaries between regular and non-asset results
        games += na_games
        for catalog_id, dlcs in na_dlc_dict.items():
            if catalog_id in dlc_dict.keys():
                dlc_dict[catalog_id] += dlcs
            else:
                dlc_dict[catalog_id] = dlcs
        logger.debug(f"Games {len(games)}, games with DLCs {len(dlc_dict)}")

        self.signals.result.emit((games, dlc_dict), FetchWorker.Result.COMBINED)
