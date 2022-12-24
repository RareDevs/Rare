import os
import platform
from logging import getLogger

from PyQt5.QtCore import QStandardPaths
from legendary.core import LegendaryCore

from rare.lgndr.cli import LegendaryCLI
from rare.lgndr.glue.arguments import LgndrUninstallGameArgs
from rare.lgndr.glue.monkeys import LgndrIndirectStatus
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
