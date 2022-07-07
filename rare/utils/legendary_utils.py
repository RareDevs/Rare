import os
import platform
from argparse import Namespace
from logging import getLogger

from PyQt5.QtCore import pyqtSignal, QCoreApplication, QObject, QRunnable, QStandardPaths
from legendary.core import LegendaryCore
from legendary.models.game import VerifyResult
from legendary.utils.lfs import validate_files
from parse import parse

from rare.shared import LegendaryCLISingleton, LegendaryCoreSingleton
from rare.utils import config_helper
from rare.lgndr.exception import LgndrException

logger = getLogger("Legendary Utils")


def uninstall(app_name: str, core: LegendaryCore, options=None):
    if not options:
        options = {"keep_files": False}
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

    try:
        # Remove DLC first so directory is empty when game uninstall runs
        dlcs = core.get_dlc_for_game(app_name)
        for dlc in dlcs:
            if (idlc := core.get_installed_game(dlc.app_name)) is not None:
                logger.info(f'Uninstalling DLC "{dlc.app_name}"...')
                core.uninstall_game(idlc, delete_files=not options["keep_files"])

        logger.info(f'Removing "{igame.title}" from "{igame.install_path}"...')
        core.uninstall_game(
            igame, delete_files=not options["keep_files"], delete_root_directory=True
        )
        logger.info("Game has been uninstalled.")

    except Exception as e:
        logger.warning(
            f"Removing game failed: {e!r}, please remove {igame.install_path} manually."
        )
    if not options["keep_files"]:
        logger.info("Removing sections in config file")
        config_helper.remove_section(app_name)
        config_helper.remove_section(f"{app_name}.env")

        config_helper.save_config()


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
        status = pyqtSignal(int, int, str)
        summary = pyqtSignal(int, int, str)

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
        self.signals.status.emit(num, total, self.app_name)

    def run(self):
        args = Namespace(app_name=self.app_name,
                         callback=self.status_callback)
        try:
            # TODO: offer this as an alternative when manifest doesn't exist
            # TODO: requires the client to be online. To do it this way, we need to
            # TODO: somehow detect the error and offer a dialog in which case `verify_games` is
            # TODO: re-run with `repair_mode` and `repair_online`
            self.cli.verify_game(args, print_command=False, repair_mode=True, repair_online=True)
            # self.cli.verify_game(args, print_command=False)
            self.signals.summary.emit(0, 0, self.app_name)
        except LgndrException as ret:
            r = parse('Verification failed, {:d} file(s) corrupted, {:d} file(s) are missing.', ret.message)
            if r is None:
                raise ret
            else:
                self.signals.summary.emit(r[0], r[1], self.app_name)


# FIXME: lk: ah ef me sideways, we can't even import this thing properly
# FIXME: lk: so copy it here
def resolve_aliases(core: LegendaryCore, name):
    # make sure aliases exist if not yet created
    core.update_aliases(force=False)
    name = name.strip()
    # resolve alias (if any) to real app name
    return core.lgd.config.get(
        section='Legendary.aliases', option=name,
        fallback=core.lgd.aliases.get(name.lower(), name)
    )


def import_game(core: LegendaryCore, app_name: str, path: str) -> str:
    _tr = QCoreApplication.translate
    logger.info(f"Import {app_name}")
    game = core.get_game(app_name, update_meta=False)
    if not game:
        return _tr("LgdUtils", "Could not get game for {}").format(app_name)

    if core.is_installed(app_name):
        logger.error(f"{game.app_title} is already installed")
        return _tr("LgdUtils", "{} is already installed").format(game.app_title)

    if not os.path.exists(path):
        logger.error("Path does not exist")
        return _tr("LgdUtils", "Path does not exist")

    manifest, igame = core.import_game(game, path)
    exe_path = os.path.join(path, manifest.meta.launch_exe.lstrip("/"))

    if not os.path.exists(exe_path):
        logger.error(f"Launch Executable of {game.app_title} does not exist")
        return _tr("LgdUtils", "Launch executable of {} does not exist").format(
            game.app_title
        )

    if game.is_dlc:
        release_info = game.metadata.get("mainGameItem", {}).get("releaseInfo")
        if release_info:
            main_game_appname = release_info[0]["appId"]
            main_game_title = game.metadata["mainGameItem"]["title"]
            if not core.is_installed(main_game_appname):
                return _tr("LgdUtils", "Game is a DLC, but {} is not installed").format(
                    main_game_title
                )
        else:
            return _tr("LgdUtils", "Unable to get base game information for DLC")

    total = len(manifest.file_manifest_list.elements)
    found = sum(
        os.path.exists(os.path.join(path, f.filename))
        for f in manifest.file_manifest_list.elements
    )
    ratio = found / total

    if ratio < 0.9:
        logger.warning(
            "Game files are missing. It may be not the latest version or it is corrupt"
        )
        # return False
    core.install_game(igame)
    if igame.needs_verification:
        logger.info(f"{igame.title} needs verification")

    logger.info(f"Successfully imported Game: {game.app_title}")
    return ""
