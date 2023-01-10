import os
import platform
from logging import getLogger

from PyQt5.QtCore import QObject, QProcess, pyqtSignal, QUrl, pyqtSlot
from PyQt5.QtCore import QStandardPaths
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QMessageBox, QPushButton
from legendary.core import LegendaryCore

from rare.components.dialogs.uninstall_dialog import UninstallDialog
from rare.lgndr.cli import LegendaryCLI
from rare.lgndr.glue.arguments import LgndrUninstallGameArgs
from rare.lgndr.glue.monkeys import LgndrIndirectStatus
from rare.models.game import RareGame
from rare.shared import LegendaryCoreSingleton, GlobalSignalsSingleton, ArgumentsSingleton
from rare.shared.game_process import GameProcess
from rare.utils import config_helper, misc
from .cloud_save_utils import CloudSaveUtils

logger = getLogger("GameUtils")


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


class GameUtils(QObject):
    finished = pyqtSignal(str, str)  # app_name, error
    cloud_save_finished = pyqtSignal(str)
    game_launched = pyqtSignal(RareGame)
    update_list = pyqtSignal(str)

    def __init__(self, parent=None):
        super(GameUtils, self).__init__(parent=parent)
        self.core = LegendaryCoreSingleton()
        self.signals = GlobalSignalsSingleton()
        self.args = ArgumentsSingleton()

        self.running_games = {}
        self.launch_queue = {}

        self.cloud_save_utils = CloudSaveUtils()
        self.cloud_save_utils.sync_finished.connect(self.sync_finished)

    def check_running(self, rgame: RareGame):
        if rgame.is_installed:
            game_process = GameProcess(rgame, on_startup=True)
            game_process.game_finished.connect(self.game_finished)
            game_process.game_launched.connect(self.game_launched.emit)
            self.running_games[rgame.app_name] = game_process

    def uninstall_game(self, rgame: RareGame) -> bool:
        # returns if uninstalled
        if not os.path.exists(rgame.igame.install_path):
            if QMessageBox.Yes == QMessageBox.question(
                    None,
                    self.tr("Uninstall - {}").format(rgame.igame.title),
                    self.tr(
                        "Game files of {} do not exist. Remove it from installed games?"
                    ).format(rgame.igame.title),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes,
            ):
                self.core.lgd.remove_installed_game(rgame.app_name)
                return True
            else:
                return False

        proceed, keep_files, keep_config = UninstallDialog(rgame.game).get_options()
        if not proceed:
            return False
        success, message = uninstall_game(self.core, rgame.app_name, keep_files, keep_config)
        if not success:
            QMessageBox.warning(None, self.tr("Uninstall - {}").format(rgame.title), message, QMessageBox.Close)
        self.signals.game.uninstalled.emit(rgame.app_name)
        return True

    def prepare_launch(
            self, rgame: RareGame, offline: bool = False, skip_update_check: bool = False
    ):
        dont_sync_after_finish = False

        # TODO move this to helper
        if rgame.game.supports_cloud_saves and not offline:
            try:
                sync = self.cloud_save_utils.sync_before_launch_game(rgame)
            except ValueError:
                logger.info("Cancel startup")
                self.sync_finished(rgame)
                return
            except AssertionError:
                dont_sync_after_finish = True
            else:
                if sync:
                    self.launch_queue[rgame.app_name] = (rgame, skip_update_check, offline)
                    return
            self.sync_finished(rgame)

        self.launch_game(
            rgame, offline, skip_update_check, ask_always_sync=dont_sync_after_finish
        )

    def launch_game(
            self,
            rgame: RareGame,
            offline: bool = False,
            skip_update_check: bool = False,
            wine_bin: str = None,
            wine_pfx: str = None,
            ask_always_sync: bool = False,
    ):
        executable = misc.get_rare_executable()
        executable, args = executable[0], executable[1:]
        args.extend([
            "start", rgame.app_name
        ])
        if offline:
            args.append("--offline")
        if skip_update_check:
            args.append("--skip-update-check")
        if wine_bin:
            args.extend(["--wine-bin", wine_bin])
        if wine_pfx:
            args.extend(["--wine-prefix", wine_pfx])
        if ask_always_sync:
            args.extend("--ask-always-sync")

        # kill me, if I don't change it before commit
        QProcess.startDetached(executable, args)
        logger.info(f"Start new Process: ({executable} {' '.join(args)})")
        game_process = GameProcess(rgame, ask_always_sync)
        game_process.game_finished.connect(self.game_finished)
        game_process.game_launched.connect(self.game_launched.emit)
        self.running_games[rgame.app_name] = game_process

    @pyqtSlot(RareGame, int)
    def game_finished(self, rgame: RareGame, exit_code):
        if self.running_games.get(rgame.app_name):
            self.running_games.pop(rgame.app_name)
        if exit_code == -1234:
            return

        self.finished.emit(rgame.app_name, "")

        logger.info(f"Game exited with exit code: {exit_code}")
        self.signals.discord_rpc.set_title.emit("")
        if exit_code == 1 and rgame.is_origin:
            msg_box = QMessageBox()
            msg_box.setText(
                self.tr(
                    "Origin is not installed. Do you want to download installer file? "
                )
            )
            msg_box.addButton(QPushButton("Download"), QMessageBox.YesRole)
            msg_box.addButton(QPushButton("Cancel"), QMessageBox.RejectRole)
            resp = msg_box.exec()
            # click install button
            if resp == 0:
                QDesktopServices.openUrl(QUrl("https://www.dm.origin.com/download"))
            return

        if exit_code != 0:
            pass
            """
            QMessageBox.warning(
                None,
                "Warning",
                self.tr("Failed to launch {}. Check logs to find error").format(
                    self.core.get_game(app_name).app_title
                ),
            )
            """

        if rgame.app_name in self.running_games.keys():
            self.running_games.pop(rgame.app_name)

        if rgame.game.supports_cloud_saves:
            if exit_code != 0:
                r = QMessageBox.question(
                    None,
                    "Question",
                    self.tr(
                        "Game exited with code {}, which is not a normal code. "
                        "It could be caused by a crash. Do you want to sync cloud saves"
                    ).format(exit_code),
                    buttons=QMessageBox.Yes | QMessageBox.No,
                    defaultButton=QMessageBox.Yes,
                )
                if r != QMessageBox.Yes:
                    return

            # TODO move this to helper
            self.cloud_save_utils.game_finished(rgame, always_ask=False)

    @pyqtSlot(RareGame)
    def sync_finished(self, rgame: RareGame):
        if rgame.app_name in self.launch_queue.keys():
            self.cloud_save_finished.emit(rgame.app_name)
            params = self.launch_queue[rgame.app_name]
            self.launch_queue.pop(rgame.app_name)
            self.launch_game(*params)
        else:
            self.cloud_save_finished.emit(rgame.app_name)
