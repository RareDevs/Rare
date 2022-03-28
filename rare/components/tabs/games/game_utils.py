import datetime
import os
import platform
import shutil
from dataclasses import dataclass
from logging import getLogger

from PyQt5.QtCore import QObject, QSettings, QProcess, QProcessEnvironment, pyqtSignal, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QMessageBox, QPushButton
from legendary.models.game import LaunchParameters, InstalledGame

from rare.components.dialogs.uninstall_dialog import UninstallDialog
from rare.components.extra.console import ConsoleWindow
from rare.components.tabs.games import CloudSaveUtils
from rare.shared import LegendaryCoreSingleton, GlobalSignalsSingleton, ArgumentsSingleton
from rare.utils import legendary_utils
from rare.utils.meta import RareGameMeta

logger = getLogger("GameUtils")


class GameProcess(QProcess):
    game_finished = pyqtSignal(int, str)

    # noinspection PyUnresolvedReferences
    def __init__(self, app_name):
        super(GameProcess, self).__init__()
        self.app_name = app_name
        try:
            self.finished.connect(lambda x: self.game_finished.emit(x, self.app_name))
        except RuntimeError:  # Do not raise an exception, if rare finished, but game not
            pass


@dataclass
class RunningGameModel:
    process: GameProcess
    app_name: str
    always_ask_sync: bool = False


class GameUtils(QObject):
    running_games = dict()
    finished = pyqtSignal(str, str)  # app_name, error
    cloud_save_finished = pyqtSignal(str)
    launch_queue = dict()
    game_launched = pyqtSignal(str)
    update_list = pyqtSignal(str)

    def __init__(self, parent=None):
        super(GameUtils, self).__init__(parent=parent)
        self.core = LegendaryCoreSingleton()
        self.signals = GlobalSignalsSingleton()
        self.args = ArgumentsSingleton()

        self.console = ConsoleWindow()
        self.cloud_save_utils = CloudSaveUtils()
        self.cloud_save_utils.sync_finished.connect(self.sync_finished)
        self.game_meta = RareGameMeta()

    def uninstall_game(self, app_name) -> bool:
        # returns if uninstalled
        game = self.core.get_game(app_name)
        igame = self.core.get_installed_game(app_name)
        if not os.path.exists(igame.install_path):
            if QMessageBox.Yes == QMessageBox.question(
                    None,
                    "Uninstall",
                    self.tr(
                        "Game files of {} do not exist. Remove it from installed games?"
                    ).format(igame.title),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes,
            ):
                self.core.lgd.remove_installed_game(app_name)
                return True
            else:
                return False

        infos = UninstallDialog(game).get_information()
        if infos == 0:
            return False
        legendary_utils.uninstall(game.app_name, self.core, infos)
        self.signals.game_uninstalled.emit(app_name)
        return True

    def prepare_launch(
            self, app_name, offline: bool = False, skip_update_check: bool = False
    ):
        game = self.core.get_game(app_name)
        dont_sync_after_finish = False

        if game.supports_cloud_saves:
            try:
                sync = self.cloud_save_utils.sync_before_launch_game(app_name)
            except ValueError:
                logger.info("Cancel startup")
                self.sync_finished(app_name)
                return
            except AssertionError:
                dont_sync_after_finish = True
            else:
                if sync:
                    self.launch_queue[app_name] = (app_name, skip_update_check, offline)
                    return
            self.sync_finished(app_name)

        self.launch_game(
            app_name, offline, skip_update_check, ask_always_sync=dont_sync_after_finish
        )

    def launch_game(
            self,
            app_name: str,
            offline: bool = False,
            skip_update_check: bool = False,
            wine_bin: str = None,
            wine_pfx: str = None,
            ask_always_sync: bool = False,
    ):
        if self.args.offline:
            offline = True
        game = self.core.get_game(app_name)
        igame = self.core.get_installed_game(app_name)

        meta_data = self.game_meta.get_game(app_name)
        meta_data.last_played = datetime.datetime.now()
        self.game_meta.set_game(app_name, meta_data)

        if not game:
            logger.error(f"{app_name} not found")
            self.finished.emit(app_name, self.tr("Game not found in available games"))
            return

        if QSettings().value("confirm_start", False, bool):
            if (
                    not QMessageBox.question(
                        None,
                        "Launch",
                        self.tr("Do you want to launch {}").format(game.app_title),
                        QMessageBox.Yes | QMessageBox.No,
                    ) == QMessageBox.Yes
            ):
                logger.info("Cancel Startup")
                self.finished.emit(app_name, "")
                return
        logger.info(f"Launching {game.app_title}")

        if game.third_party_store == "Origin":
            offline = False
        else:
            if not igame:
                logger.error(f"{app_name} is not installed")
            if game.is_dlc:
                logger.error("Game is dlc")
                self.finished.emit(
                    app_name, self.tr("Game is a DLC. Please launch base game instead")
                )
                return
            if not os.path.exists(igame.install_path):
                logger.error("Game doesn't exist")
                self.finished.emit(
                    app_name,
                    self.tr(
                        "Game files of {} do not exist. Please install game"
                    ).format(game.app_title),
                )
                return

        def _launch_real():
            process = self._get_process(app_name, env)
            self.console.log("\n"*2)
            if game.third_party_store != "Origin":
                self._launch_game(igame, process, offline, skip_update_check, ask_always_sync)
            else:
                self._launch_origin(app_name, process)

        env = self.core.get_app_environment(app_name, wine_pfx=wine_pfx)
        pre_cmd, wait = self.core.get_pre_launch_command(app_name)
        if pre_cmd:
            pre_cmd = pre_cmd.split()
            pre_proc = self._launch_pre_command(env)
            self.console.log("\n"*2)
            pre_proc.start(pre_cmd[0], pre_cmd[1:])
            if wait:
                pre_proc.finished.connect(_launch_real)
                return
        _launch_real()

    def game_finished(self, exit_code, app_name):
        logger.info(f"Game exited with exit code: {exit_code}")
        self.console.log(f"Game exited with code: {exit_code}")
        self.signals.set_discord_rpc.emit("")
        is_origin = self.core.get_game(app_name).third_party_store == "Origin"
        if exit_code == 1 and is_origin:
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
            QMessageBox.warning(
                None,
                "Warning",
                self.tr("Failed to launch {}. Check logs to find error").format(
                    self.core.get_game(app_name).app_title
                ),
            )
            # show console on error, even if disabled
            self.console.show()

        game: RunningGameModel = self.running_games.get(app_name, None)
        if app_name in self.running_games.keys():
            self.running_games.pop(app_name)
        self.finished.emit(app_name, "")

        if self.core.get_game(app_name).supports_cloud_saves:
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
            self.cloud_save_utils.game_finished(app_name, game.always_ask_sync)

    def _launch_pre_command(self, env: dict):
        proc = QProcess()
        environment = QProcessEnvironment()
        for e in env:
            environment.insert(e, env[e])
        proc.setProcessEnvironment(environment)

        proc.readyReadStandardOutput.connect(
            lambda: self.console.log(
                str(proc.readAllStandardOutput().data(), "utf-8", "ignore")
            )
        )
        proc.readyReadStandardError.connect(
            lambda: self.console.error(
                str(proc.readAllStandardError().data(), "utf-8", "ignore")
            )
        )
        return proc

    def _get_process(self, app_name, env):
        process = GameProcess(app_name)

        environment = QProcessEnvironment()
        for e in env:
            environment.insert(e, env[e])
        process.setProcessEnvironment(environment)

        process.readyReadStandardOutput.connect(
            lambda: self.console.log(
                str(process.readAllStandardOutput().data(), "utf-8", "ignore")
            )
        )
        process.readyReadStandardError.connect(
            lambda: self.console.error(
                str(process.readAllStandardError().data(), "utf-8", "ignore")
            )
        )
        process.finished.connect(lambda x: self.game_finished(x, app_name))
        process.stateChanged.connect(
            lambda state: self.console.show()
            if (state == QProcess.Running
                and QSettings().value("show_console", False, bool))
            else None
        )
        return process

    def _launch_origin(self, app_name, process: QProcess):
        origin_uri = self.core.get_origin_uri(app_name, self.args.offline)
        logger.info("Launch Origin Game: ")
        if platform.system() == "Windows":
            QDesktopServices.openUrl(QUrl(origin_uri))
            self.finished.emit(app_name, "")
            return

        command = self.core.get_app_launch_command(app_name)

        if not os.path.exists(command[0]) and shutil.which(command[0]) is None:
            # wine binary does not exist
            QMessageBox.warning(
                None, "Warning",
                self.tr(
                    "'{}' does not exist. Please change it in Settings"
                ).format(command[0]),
            )
            process.deleteLater()
            return
        command.append(origin_uri)
        process.start(command[0], command[1:])

    def _launch_game(self, igame: InstalledGame, process: QProcess, offline: bool,
                     skip_update_check: bool, ask_always_sync: bool):
        if not offline:  # skip for update
            if not skip_update_check and not self.core.is_noupdate_game(igame.app_name):
                # check updates
                try:
                    latest = self.core.get_asset(
                        igame.app_name, igame.platform, update=False
                    )
                except ValueError:
                    self.finished.emit(igame.app_name, self.tr("Metadata doesn't exist"))
                    return
                else:
                    if latest.build_version != igame.version:
                        self.finished.emit(igame.app_name, self.tr("Please update game"))
                        return

        params: LaunchParameters = self.core.get_launch_parameters(
            app_name=igame.app_name, offline=offline
        )

        full_params = list()

        if os.environ.get("container") == "flatpak":
            full_params.extend(["flatpak-spawn", "--host"])

        full_params.extend(params.launch_command)
        full_params.append(
            os.path.join(params.game_directory, params.game_executable)
        )
        full_params.extend(params.game_parameters)
        full_params.extend(params.egl_parameters)
        full_params.extend(params.user_parameters)

        process.setWorkingDirectory(params.working_directory)

        if platform.system() != "Windows":
            # wine prefixes
            for env in ["STEAM_COMPAT_DATA_PATH", "WINEPREFIX"]:
                if val := process.processEnvironment().value(env, ""):
                    if not os.path.exists(val):
                        try:
                            os.makedirs(val)
                        except PermissionError as e:
                            logger.error(str(e))
                            QMessageBox.warning(
                                None,
                                "Error",
                                self.tr(
                                    "Error while launching {}. No permission to create {} for {}"
                                ).format(igame.title, val, env),
                            )
                            process.deleteLater()
                            return
            # check wine executable

        if shutil.which(full_params[0]) is None:
            QMessageBox.warning(None, "Warning", self.tr("'{}' does not exist").format(full_params[0]))
            return
        running_game = RunningGameModel(
            process=process, app_name=igame.app_name, always_ask_sync=ask_always_sync
        )
        process.start(full_params[0], full_params[1:])

        self.game_launched.emit(igame.app_name)
        self.signals.set_discord_rpc.emit(igame.app_name)
        logger.info(f"{igame.title} launched")

        self.running_games[igame.app_name] = running_game

    def sync_finished(self, app_name):
        if app_name in self.launch_queue.keys():
            self.cloud_save_finished.emit(app_name)
            params = self.launch_queue[app_name]
            self.launch_queue.pop(app_name)
            self.launch_game(*params)
        else:
            self.cloud_save_finished.emit(app_name)
