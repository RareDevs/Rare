import platform
from argparse import Namespace
from enum import IntEnum
from logging import getLogger

from PySide6.QtCore import QObject, Signal, QSettings
from requests.exceptions import HTTPError, ConnectionError

from rare.lgndr.core import LegendaryCore
from rare.utils.metrics import timelogger
from rare.models.options import options
from .worker import Worker

logger = getLogger("FetchWorker")


class FetchWorker(Worker):
    class Result(IntEnum):
        ERROR = 0
        GAMESDLCS = 1
        ENTITLEMENTS = 2

    class Signals(QObject):
        progress = Signal(int, str)
        result = Signal(object, int)

    def __init__(self, core: LegendaryCore, args: Namespace):
        super(Worker, self).__init__()
        self.signals = FetchWorker.Signals()
        self.core = core
        self.args = args
        self.settings = QSettings()


class EntitlementsWorker(FetchWorker):

    def run_real(self):

        want_entitlements = not self.settings.value(*options.exclude_entitlements)

        entitlements = ()
        if want_entitlements and not self.args.offline:
            # Get entitlements, Ubisoft integration also uses them
            self.signals.progress.emit(0, self.signals.tr("Updating entitlements"))
            with timelogger(logger, "Request entitlements"):
                try:
                    entitlements = self.core.egs.get_user_entitlements_full()
                except AttributeError as e:
                    logger.warning(e)
                    entitlements = self.core.egs.get_user_entitlements()
            self.core.lgd.entitlements = entitlements
            logger.info(f"Entitlements: %s", len(list(entitlements)))
        self.signals.result.emit(entitlements, FetchWorker.Result.ENTITLEMENTS)
        return


class GamesDlcsWorker(FetchWorker):

    def run_real(self):

        # Fetch regular EGL games with assets
        # want_unreal = self.settings.value(*options.unreal_meta) or self.args.debug
        # want_win32 = self.settings.value(*options.win32_meta) or self.args.debug
        # want_macos = self.settings.value(*options.macos_meta) or self.args.debug
        want_unreal = self.settings.value(*options.unreal_meta)
        want_win32 = self.settings.value(*options.win32_meta)
        want_macos = self.settings.value(*options.macos_meta)
        want_non_asset = not self.settings.value(*options.exclude_non_asset)
        need_macos = platform.system() == "Darwin"
        need_windows = not any([want_win32, want_macos, need_macos]) and not self.args.offline

        if want_win32:
            logger.info(
                "Requesting Win32 metadata due to %s, %s Unreal engine",
                "settings" if want_win32 else "debug",
                "with" if want_unreal else "without"
            )
            self.signals.progress.emit(00, self.signals.tr("Updating game metadata for Windows"))
            with timelogger(logger, "Request Win32 games"):
                self.core.get_game_and_dlc_list(
                    update_assets=not self.args.offline, platform="Win32", skip_ue=not want_unreal
                )

        if need_macos or want_macos:
            logger.info(
                "Requesting macOS metadata due to %s, %s Unreal engine",
                "platform" if need_macos else "settings" if want_macos else "debug",
                "with" if want_unreal else "without"
            )
            self.signals.progress.emit(15, self.signals.tr("Updating game metadata for macOS"))
            with timelogger(logger, "Request macOS games"):
                self.core.get_game_and_dlc_list(
                    update_assets=not self.args.offline, platform="Mac", skip_ue=not want_unreal
                )

        if need_windows:
            self.signals.progress.emit(00, self.signals.tr("Updating game metadata for Windows"))
            logger.info(
                "Requesting Windows metadata, %s Unreal engine",
                "with" if want_unreal else "without"
            )
        with timelogger(logger, "Request Windows games"):
            games, dlc_dict = self.core.get_game_and_dlc_list(
                update_assets=need_windows, platform="Windows", skip_ue=not want_unreal
            )
        logger.info(f"Games: %s. Games with DLCs: %s", len(games), len(dlc_dict))

        # Fetch non-asset games
        if want_non_asset:
            self.signals.progress.emit(30, self.signals.tr("Updating non-asset game metadata"))
            try:
                with timelogger(logger, "Request non-asset"):
                    na_games, na_dlc_dict = self.core.get_non_asset_library_items(force_refresh=False, skip_ue=False)
            except (HTTPError, ConnectionError) as e:
                logger.error(f"Network error while fetching non asset games")
                logger.error(e)
                na_games, na_dlc_dict = ([], {})
            # NOTE: This is here because of broken appIds from Epic
            # https://discord.com/channels/826881530310819914/884510635642216499/1111321692703305729
            except Exception as e:
                logger.error("General exception while fetching non asset games from EGS.")
                logger.error(e)
                na_games, na_dlc_dict = ([], {})
            logger.info("Non-asset: %s. Non-asset with DLCs: %s", len(na_games), len(na_dlc_dict))

            # Combine the two games lists and the two dlc dictionaries between regular and non-asset results
            games += na_games
            for catalog_id, dlcs in na_dlc_dict.items():
                if catalog_id in dlc_dict.keys():
                    dlc_dict[catalog_id] += dlcs
                else:
                    dlc_dict[catalog_id] = dlcs
            logger.info(f"Games: {len(games)}. Games with DLCs: {len(dlc_dict)}")

        self.signals.progress.emit(40, self.signals.tr("Preparing library"))
        self.signals.result.emit((games, dlc_dict), FetchWorker.Result.GAMESDLCS)
