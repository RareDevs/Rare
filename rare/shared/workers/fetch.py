import platform
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
        self.settings = QSettings()

    def run_real(self):
        # Fetch regular EGL games with assets
        want_unreal = self.settings.value("unreal_meta", False, bool) or self.args.debug
        want_win32 = self.settings.value("win32_meta", False, bool)
        want_macos = self.settings.value("macos_meta", False, bool)
        need_macos = platform.system() == "Darwin"
        need_windows = not any([want_win32, want_macos, need_macos, self.args.debug]) and not self.args.offline

        if want_win32 or self.args.debug:
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

        if need_macos or want_macos or self.args.debug:
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

        want_non_asset = not self.settings.value("exclude_non_asset", False, bool)
        want_entitlements = not self.settings.value("exclude_entitlements", False, bool)

        # Fetch non-asset games
        if want_non_asset:
            self.signals.progress.emit(30, self.signals.tr("Updating non-asset game metadata"))
            try:
                with timelogger(logger, "Request non-asset"):
                    na_games, na_dlc_dict = self.core.get_non_asset_library_items(force_refresh=False, skip_ue=False)
            except (HTTPError, ConnectionError) as e:
                logger.error("Network exception while fetching non asset games from EGS.")
                logger.error(e)
                na_games, na_dlc_dict = ([], {})
            # FIXME:
            #  This is here because of broken appIds from Epic:
            #  https://discord.com/channels/826881530310819914/884510635642216499/1111321692703305729
            #  There is a tab character in the appId of Fallout New Vegas: Honest Hearts DLC, this breaks metadata storage
            #  on Windows as they can't handle tabs at the end of the filename (?)
            #  Legendary and Heroic are also affected, but it completely breaks Rare, so dodge it for now pending a fix.
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

        if want_entitlements:
            # Get entitlements, Ubisoft integration also uses them
            self.signals.progress.emit(40, self.signals.tr("Updating entitlements"))
            with timelogger(logger, "Request entitlements"):
                entitlements = self.core.egs.get_user_entitlements()
            self.core.lgd.entitlements = entitlements
            logger.info(f"Entitlements: {len(list(entitlements))}")

        self.signals.progress.emit(50, self.signals.tr("Preparing games"))
        self.signals.result.emit((games, dlc_dict), FetchWorker.Result.COMBINED)
