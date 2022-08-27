import os
import platform
from logging import getLogger

from PyQt5.QtCore import pyqtSignal, QObject, QRunnable, QStandardPaths
from legendary.core import LegendaryCore

from rare.lgndr.api_arguments import LgndrVerifyGameArgs, LgndrUninstallGameArgs
from rare.lgndr.api_monkeys import LgndrIndirectStatus
from rare.lgndr.cli import LegendaryCLI
from rare.shared import LegendaryCoreSingleton, ArgumentsSingleton
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
    LegendaryCLI(core).uninstall_game(
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
    core.lgd.save_manifest(game.app_name, new_manifest_data, version=new_manifest.meta.build_version)


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
        self.core = LegendaryCoreSingleton()
        self.args = ArgumentsSingleton()
        self.app_name = app_name

    def status_callback(self, num: int, total: int, percentage: float, speed: float):
        self.signals.status.emit(self.app_name, num, total, percentage, speed)

    def run(self):
        cli = LegendaryCLI(self.core)
        status = LgndrIndirectStatus()
        args = LgndrVerifyGameArgs(
            app_name=self.app_name, indirect_status=status, verify_stdout=self.status_callback
        )

        # lk: first pass, verify with the current manifest
        repair_mode = False
        result = cli.verify_game(
            args, print_command=False, repair_mode=repair_mode, repair_online=not self.args.offline
        )
        if result is None:
            # lk: second pass with downloading the latest manifest
            # lk: this happens if the manifest was not found and repair_mode was not requested
            # lk: we already have checked if the directory exists before starting the worker
            try:
                # lk: this try-except block handles the exception caused by a missing manifest
                # lk: and is raised only in the case we are offline
                repair_mode = True
                result = cli.verify_game(
                    args, print_command=False, repair_mode=repair_mode, repair_online=not self.args.offline
                )
                if result is None:
                    raise ValueError
            except ValueError:
                self.signals.error.emit(self.app_name, status.message)
                return

        success = result is not None and not any(result)
        if success:
            # lk: if verification was successful we delete the repair file and run the clean procedure
            # lk: this could probably be cut down to what is relevant for this use-case and skip the `cli` call
            igame = self.core.get_installed_game(self.app_name)
            game = self.core.get_game(self.app_name, platform=igame.platform)
            repair_file = os.path.join(self.core.lgd.get_tmp_path(), f"{self.app_name}.repair")
            cli.install_game_cleanup(game=game, igame=igame, repair_mode=True, repair_file=repair_file)

        self.signals.result.emit(self.app_name, success, *result)
