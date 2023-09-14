from argparse import Namespace
from enum import IntEnum
from logging import getLogger

from PyQt5.QtCore import QObject, pyqtSignal, QSettings
from requests.exceptions import HTTPError, ConnectionError

from rare.lgndr.core import LegendaryCore
from rare.utils.metrics import timelogger
from .worker import Worker

logger = getLogger("FetchWorker")


class FetchWorker(Worker):
    class Result(IntEnum):
        ERROR = 0
        GAMESDLCS = 1
        ENTITLEMENTS = 2

    class Signals(QObject):
        progress = pyqtSignal(int, str)
        result = pyqtSignal(object, int)

    def __init__(self, core: LegendaryCore, args: Namespace):
        super(Worker, self).__init__()
        self.signals = FetchWorker.Signals()
        self.core = core
        self.args = args


class EntitlementsWorker(FetchWorker):
    def __init__(self, core: LegendaryCore, args: Namespace):
        super(EntitlementsWorker, self).__init__(core, args)
        self.exclude_entitlements = QSettings().value("exclude_entitlements", False, bool)

    def run_real(self):
        entitlements = ()
        self.signals.progress.emit(0, self.signals.tr("Updating entitlements"))
        if not self.exclude_entitlements:
            with timelogger(logger, "Request entitlements"):
                entitlements = self.core.egs.get_user_entitlements()
            logger.info(f"Entitlements: {len(list(entitlements))}")
        self.signals.result.emit(entitlements, FetchWorker.Result.ENTITLEMENTS)
        return


class GamesDlcsWorker(FetchWorker):

    def __init__(self, core: LegendaryCore, args: Namespace):
        super(GamesDlcsWorker, self).__init__(core, args)
        self.exclude_non_asset = QSettings().value("exclude_non_asset", False, bool)

    def run_real(self):

        # Fetch regular EGL games with assets
        self.signals.progress.emit(0, self.signals.tr("Updating game metadata"))
        with timelogger(logger, "Request games"):
            games, dlc_dict = self.core.get_game_and_dlc_list(
                update_assets=not self.args.offline, platform="Windows", skip_ue=False
            )
        logger.info(f"Games: {len(games)}. Games with DLCs {len(dlc_dict)}")

        # Fetch non-asset games
        if not self.exclude_non_asset:
            self.signals.progress.emit(10, self.signals.tr("Updating non-asset metadata"))
            try:
                with timelogger(logger, "Request non-asset"):
                    na_games, na_dlc_dict = self.core.get_non_asset_library_items(force_refresh=False, skip_ue=False)
            except (HTTPError, ConnectionError) as e:
                logger.error(f"Connection error while fetching non asset games")
                logger.error(e)
                na_games, na_dlc_dict = ([], {})
            # NOTE: This is here because of broken appIds from Epic
            # https://discord.com/channels/826881530310819914/884510635642216499/1111321692703305729
            except Exception as e:
                logger.error(f"General exception while fetching non asset games")
                logger.error(e)
                na_games, na_dlc_dict = ([], {})
            logger.info(f"Non-asset: {len(na_games)}. Non-asset with DLCs: {len(na_dlc_dict)}")

            # Combine the two games lists and the two dlc dictionaries between regular and non-asset results
            games += na_games
            for catalog_id, dlcs in na_dlc_dict.items():
                if catalog_id in dlc_dict.keys():
                    dlc_dict[catalog_id] += dlcs
                else:
                    dlc_dict[catalog_id] = dlcs
            logger.info(f"Games: {len(games)}. Games with DLCs: {len(dlc_dict)}")

        self.signals.progress.emit(10, self.signals.tr("Preparing library"))
        self.signals.result.emit((games, dlc_dict), FetchWorker.Result.GAMESDLCS)
