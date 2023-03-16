from logging import getLogger

from PyQt5.QtCore import QObject, pyqtSignal
from legendary.core import LegendaryCore

from rare.lgndr.cli import LegendaryCLI
from rare.lgndr.glue.arguments import LgndrUninstallGameArgs
from rare.lgndr.glue.monkeys import LgndrIndirectStatus
from rare.models.game import RareGame
from rare.models.install import UninstallOptionsModel
from rare.utils import config_helper
from rare.utils.paths import desktop_links_supported, desktop_link_types, desktop_link_path
from .worker import Worker

logger = getLogger("UninstallWorker")

# TODO: You can use RareGame directly here once this is called inside RareCore and skip metadata fetch
def uninstall_game(core: LegendaryCore, app_name: str, keep_files=False, keep_config=False):
    game = core.get_game(app_name)

    # remove shortcuts link
    if desktop_links_supported():
        for link_type in desktop_link_types():
            link_path = desktop_link_path(
                game.metadata.get("customAttributes", {}).get("FolderName", {}).get("value"), link_type
            )
            if link_path.exists():
                link_path.unlink(missing_ok=True)

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


class UninstallWorker(Worker):
    class Signals(QObject):
        result = pyqtSignal(RareGame, bool, str)

    def __init__(self, core: LegendaryCore, rgame: RareGame, options: UninstallOptionsModel):
        super(UninstallWorker, self).__init__()
        self.signals = UninstallWorker.Signals()
        self.core = core
        self.rgame = rgame
        self.options = options

    def run_real(self) -> None:
        self.rgame.state = RareGame.State.UNINSTALLING
        success, message = uninstall_game(
            self.core, self.rgame.app_name, self.options.keep_files, self.options.keep_config
        )
        self.rgame.state = RareGame.State.IDLE
        self.signals.result.emit(self.rgame, success, message)
