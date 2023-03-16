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

    class Signals(QObject):
        result = pyqtSignal(object, int)

    def __init__(self, core: LegendaryCore, args: Namespace):
        super(Worker, self).__init__()
        self.signals = FetchWorker.Signals()
        self.core = core
        self.args = args


class GamesWorker(FetchWorker):
    def run_real(self):
        start_time = time.time()
        result = self.core.get_game_and_dlc_list(update_assets=not self.args.offline, platform="Windows", skip_ue=False)
        self.signals.result.emit(result, FetchWorker.Result.GAMES)
        logger.debug(f"Games: {len(result[0])}, DLCs {len(result[1])}")
        logger.debug(f"Request Games: {time.time() - start_time} seconds")


class NonAssetWorker(FetchWorker):
    def run_real(self):
        start_time = time.time()
        try:
            result = self.core.get_non_asset_library_items(force_refresh=False, skip_ue=False)
        except (HTTPError, ConnectionError) as e:
            logger.warning(f"Exception while fetching non asset games from EGS: {e}")
            result = ([], {})
        self.signals.result.emit(result, FetchWorker.Result.NON_ASSET)
        logger.debug(f"Non asset: {len(result[0])}, DLCs {len(result[1])}")
        logger.debug(f"Request Non Asset: {time.time() - start_time} seconds")
