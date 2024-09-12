import platform
import shutil
from logging import getLogger
from typing import Tuple

from PySide6.QtCore import QObject, Signal
from legendary.core import LegendaryCore
from legendary.lfs.eos import remove_registry_entries

from rare.lgndr.cli import LegendaryCLI
from rare.lgndr.glue.arguments import LgndrUninstallGameArgs
from rare.lgndr.glue.monkeys import LgndrIndirectStatus
from rare.models.game import RareGame
from rare.models.install import UninstallOptionsModel
from rare.utils import config_helper as config
from rare.utils.paths import desktop_links_supported, desktop_link_types, desktop_link_path
from .worker import Worker

logger = getLogger("UninstallWorker")


# TODO: You can use RareGame directly here once this is called inside RareCore and skip metadata fetch
def uninstall_game(
    core: LegendaryCore, rgame: RareGame, keep_files=False, keep_folder=True, keep_config=False, keep_overlay_keys=False
) -> Tuple[bool, str]:
    if rgame.is_overlay:
        logger.info('Deleting overlay installation...')
        core.remove_overlay_install()

        if keep_overlay_keys:
            return True, ""

        logger.info('Removing registry entries...')
        if platform.system() != "Window":
            prefixes = config.get_prefixes()
            if platform.system() == "Darwin":
                # TODO: add crossover support
                pass
            if len(prefixes):
                for prefix, _ in prefixes:
                    remove_registry_entries(prefix)
                    logger.debug("Removed registry entries for prefix %s", prefix)
        else:
            remove_registry_entries()

        return True, ""

    # remove shortcuts link
    if desktop_links_supported():
        for link_type in desktop_link_types():
            link_path = desktop_link_path(
                rgame.game.metadata.get("customAttributes", {}).get("FolderName", {}).get("value"), link_type
            )
            if link_path.exists():
                link_path.unlink(missing_ok=True)

    install_path = rgame.igame.install_path

    status = LgndrIndirectStatus()
    LegendaryCLI(core).uninstall_game(
        LgndrUninstallGameArgs(
            app_name=rgame.app_name,
            keep_files=keep_files,
            skip_uninstaller=False,
            yes=True,
            indirect_status=status,
        )
    )

    keep_folder = keep_files if keep_files else keep_folder
    if not keep_folder:
        logger.info("Removing game install directory")
        shutil.rmtree(install_path, ignore_errors=True)

    if not keep_config:
        logger.info("Removing sections in config file")
        config.remove_section(rgame.app_name)
        config.remove_section(f"{rgame.app_name}.env")

        config.save_config()

    return status.success, status.message


class UninstallWorker(Worker):
    class Signals(QObject):
        result = Signal(RareGame, bool, str)

    def __init__(self, core: LegendaryCore, rgame: RareGame, options: UninstallOptionsModel):
        super(UninstallWorker, self).__init__()
        self.signals = UninstallWorker.Signals()
        self.core = core
        self.rgame = rgame
        self.options = options

    def run_real(self) -> None:
        self.rgame.state = RareGame.State.UNINSTALLING
        success, message = uninstall_game(
            self.core,
            self.rgame,
            keep_files=self.options.keep_files,
            keep_folder=self.options.keep_folder,
            keep_config=self.options.keep_config,
            keep_overlay_keys=self.options.keep_overlay_keys,
        )
        self.rgame.state = RareGame.State.IDLE
        self.signals.result.emit(self.rgame, success, message)
