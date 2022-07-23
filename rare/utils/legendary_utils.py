import os
import platform
from logging import getLogger

from PyQt5.QtCore import pyqtSignal, QObject, QRunnable, QStandardPaths
from legendary.core import LegendaryCore

from rare.lgndr.api_monkeys import LgndrIndirectStatus
from rare.lgndr.api_arguments import LgndrVerifyGameArgs, LgndrUninstallGameArgs
from rare.lgndr.api_exception import LgndrException
from rare.shared import LegendaryCLISingleton, LegendaryCoreSingleton
from rare.utils import config_helper

logger = getLogger("Legendary Utils")


def uninstall_game(core: LegendaryCore, app_name: str, keep_files=False, keep_config=False):
    igame = core.get_installed_game(app_name)

    # remove shortcuts link
    desktop = QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)
    applications = QStandardPaths.writableLocation(QStandardPaths.ApplicationsLocation)
    if platform.system() == "Linux":
        desktop_shortcut = os.path.join(desktop, f"{igame.title}.desktop")
        if os.path.exists(desktop_shortcut):
            os.remove(desktop_shortcut)

        applications_shortcut = os.path.join(applications, f"{igame.title}.desktop")
        if os.path.exists(applications_shortcut):
            os.remove(applications_shortcut)

    elif platform.system() == "Windows":
        game_title = igame.title.split(":")[0]
        desktop_shortcut = os.path.join(desktop, f"{game_title}.lnk")
        if os.path.exists(desktop_shortcut):
            os.remove(desktop_shortcut)

        start_menu_shortcut = os.path.join(applications, "..", f"{game_title}.lnk")
        if os.path.exists(start_menu_shortcut):
            os.remove(start_menu_shortcut)

    status = LgndrIndirectStatus()
    LegendaryCLISingleton().uninstall_game(
        LgndrUninstallGameArgs(
            app_name=app_name,
            keep_files=keep_files,
            indirect_status=status,
            yes=True,
        )
    )
    if not keep_config:
        logger.info("Removing sections in config file")
        config_helper.remove_section(app_name)
        config_helper.remove_section(f"{app_name}.env")

        config_helper.save_config()

    return status.success, status.message


def update_manifest(app_name: str, core: LegendaryCore):
    game = core.get_game(app_name)
    logger.info(f"Reloading game manifest of {game.app_title}")
    new_manifest_data, base_urls = core.get_cdn_manifest(game)
    # overwrite base urls in metadata with current ones to avoid using old/dead CDNs
    game.base_urls = base_urls
    # save base urls to game metadata
    core.lgd.set_game_meta(game.app_name, game)

    new_manifest = core.load_manifest(new_manifest_data)
    logger.debug(f"Base urls: {base_urls}")
    # save manifest with version name as well for testing/downgrading/etc.
    core.lgd.save_manifest(
        game.app_name, new_manifest_data, version=new_manifest.meta.build_version
    )


class VerifyWorker(QRunnable):
    class Signals(QObject):
        status = pyqtSignal(str, int, int, float, float)
        result = pyqtSignal(str, bool, int, int)
        error = pyqtSignal(str, str)

    num: int = 0
    total: int = 1  # set default to 1 to avoid DivisionByZero before it is initialized

    def __init__(self, app_name):
        super(VerifyWorker, self).__init__()
        self.signals = VerifyWorker.Signals()
        self.setAutoDelete(True)
        self.cli = LegendaryCLISingleton()
        self.core = LegendaryCoreSingleton()
        self.app_name = app_name

    def status_callback(self, num: int, total: int, percentage: float, speed: float):
        self.signals.status.emit(self.app_name, num, total, percentage, speed)

    def run(self):
        status = LgndrIndirectStatus()
        args = LgndrVerifyGameArgs(app_name=self.app_name,
                                   indirect_status=status,
                                   verify_stdout=self.status_callback)
        # TODO: offer this as an alternative when manifest doesn't exist
        # TODO: requires the client to be online. To do it this way, we need to
        # TODO: somehow detect the error and offer a dialog in which case `verify_games` is
        # TODO: re-run with `repair_mode` and `repair_online`
        result = self.cli.verify_game(
            args, print_command=False, repair_mode=True, repair_online=True)
        # success, failed, missing = self.cli.verify_game(args, print_command=False)
        if result:
            self.signals.result.emit(self.app_name, not any(result), *result)
        else:
            self.signals.error.emit(self.app_name, status.message)
