import json
import os
import platform
import shutil
from dataclasses import dataclass
from logging import getLogger

from PyQt5.QtCore import QObject, QSettings, QProcess, QProcessEnvironment, pyqtSignal, QUrl, QTimer
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtNetwork import QLocalSocket
from PyQt5.QtWidgets import QMessageBox, QPushButton
from legendary.models.game import LaunchParameters, InstalledGame

from rare.components.dialogs.uninstall_dialog import UninstallDialog
from rare.components.extra.console import Console
from rare.components.tabs.games import CloudSaveUtils
from rare.shared import LegendaryCoreSingleton, GlobalSignalsSingleton, ArgumentsSingleton
from rare.utils import legendary_utils
from rare.utils import utils
from rare.utils.meta import RareGameMeta
from rare.game_launch_helper import message_models

logger = getLogger("GameUtils")


class GameProcess(QObject):
    game_finished = pyqtSignal(int, str)  # exit_code, appname
    tried_connections = 0

    def __init__(self, app_name: str, on_startup=False):
        super(GameProcess, self).__init__()
        self.app_name = app_name
        self.on_startup = on_startup
        self.game = LegendaryCoreSingleton().get_game(app_name)
        self.socket = QLocalSocket()
        self.socket.connected.connect(self._socket_connected)
        self.socket.errorOccurred.connect(self._error_occurred)
        self.socket.readyRead.connect(self._message_available)

        def close_socket():
            try:
                self.socket.close()
            except RuntimeError:
                pass

        self.socket.disconnected.connect(close_socket)
        self.timer = QTimer()
        if not on_startup:
            # wait a short time for process started
            self.timer.timeout.connect(self.connect_to_server)
            self.timer.start(200)
        else:
            # nothing happens, if no server available
            self.connect_to_server()

    def connect_to_server(self):
        self.socket.connectToServer(f"rare_{self.app_name}")
        self.tried_connections += 1

        if self.tried_connections > 50:  # 10 seconds
            QMessageBox.warning(None, "Error", self.tr("Connection to game process failed (Timeout)"))
            self.timer.stop()
            self.game_finished.emit(1, self.app_name)

    def _message_available(self):
        message = self.socket.readAll().data()
        if not message.startswith(b"{"):
            logger.error(f"Received unsupported message: {message.decode('utf-8')}")
            return
        try:
            data = json.loads(message)
        except json.JSONDecodeError as e:
            logger.error(e)
            logger.error("Could not load json data")
            return

        action = data.get("action", -1)

        if action == -1:
            logger.error("Got unexpected action")
        elif action == message_models.Actions.finished:
            logger.info(f"{self.app_name} finished")
            model = message_models.FinishedModel.base_from_json(data)
            self._game_finished(model)
        elif action == message_models.Actions.error:
            model = message_models.ErrorModel.from_json(data)
            logger.error(f"Error in game {self.game.app_title}: {model.error_string}")
            QMessageBox.warning(None, "Error", self.tr(
                "Error in game {}: \n{}").format(self.game.app_title, model.error_string))

        elif action == message_models.Actions.state_update:
            model = message_models.StateChangedModel.from_json(data)
            if model.new_state == message_models.StateChangedModel.States.started:
                logger.info("Launched Game")

    def _socket_connected(self):
        self.timer.stop()
        self.timer.deleteLater()
        logger.info(f"Connection established for {self.app_name}")

    def _error_occurred(self, _):
        if self.on_startup:
            self.socket.close()
            self.deleteLater()
            self._game_finished(-1234)
        logger.error(f"{self.app_name}: {self.socket.errorString()}")

    def _game_finished(self, exit_code):
        self.game_finished.emit(exit_code, self.app_name)


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

        self.console = Console()
        self.cloud_save_utils = CloudSaveUtils()
        self.cloud_save_utils.sync_finished.connect(self.sync_finished)
        self.game_meta = RareGameMeta()

        for igame in self.core.get_installed_list():
            game_process = GameProcess(igame.app_name, True)
            game_process.game_finished.connect(self.game_finished)
            self.running_games[igame.app_name] = game_process

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

        if game.supports_cloud_saves and not offline:
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
        executable = utils.get_rare_executable()
        executable, args = executable[0], executable[1:]
        args.extend([
            "start", app_name
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

        QProcess.startDetached(executable, args)
        logger.info(f"Start new Process: ({executable} {' '.join(args)})")
        game_process = GameProcess(app_name)
        game_process.game_finished.connect(self.game_finished)
        self.running_games[app_name] = game_process

    def game_finished(self, exit_code, app_name):
        if exit_code == -1234:
            self.running_games.pop(app_name)
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
        environment = QProcessEnvironment().systemEnvironment()
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
        self.console.set_env(environment)
        return proc

    def _get_process(self, app_name, env):
        process = GameProcess(app_name)

        environment = QProcessEnvironment().systemEnvironment()
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
        self.console.set_env(environment)
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
