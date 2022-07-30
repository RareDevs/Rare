import datetime
import json
import os
from logging import getLogger

from PyQt5.QtCore import QObject, QProcess, pyqtSignal, QUrl, QTimer
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtNetwork import QLocalSocket
from PyQt5.QtWidgets import QMessageBox, QPushButton

from rare.components.dialogs.uninstall_dialog import UninstallDialog
from rare.components.tabs.games import CloudSaveUtils
from rare.game_launch_helper import message_models
from rare.shared import LegendaryCoreSingleton, GlobalSignalsSingleton, ArgumentsSingleton
from rare.utils import legendary_utils
from rare.utils import misc
from rare.utils.meta import RareGameMeta

logger = getLogger("GameUtils")


class GameProcess(QObject):
    game_finished = pyqtSignal(int, str)  # exit_code, appname
    game_launched = pyqtSignal(str)
    tried_connections = 0

    def __init__(self, app_name: str, on_startup=False, always_ask_sync: bool = False):
        super(GameProcess, self).__init__()
        self.app_name = app_name
        self.on_startup = on_startup
        self.game = LegendaryCoreSingleton().get_game(app_name)
        self.game_meta = RareGameMeta()
        self.socket = QLocalSocket()
        self.socket.connected.connect(self._socket_connected)
        try:
            self.socket.errorOccurred.connect(self._error_occurred)
        except AttributeError:
            QTimer.singleShot(100, lambda: self._error_occurred(None) if self.socket.error() else None)
            logger.warning("Do not handle errors on QLocalSocket, because of an old qt version")
        self.socket.readyRead.connect(self._message_available)
        self.always_ask_sync = always_ask_sync

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
            model = message_models.FinishedModel.from_json(data)
            self.socket.close()
            self._game_finished(model.exit_code)
        elif action == message_models.Actions.error:
            model = message_models.ErrorModel.from_json(data)
            logger.error(f"Error in game {self.game.app_title}: {model.error_string}")
            QMessageBox.warning(None, "Error", self.tr(
                "Error in game {}: \n{}").format(self.game.app_title, model.error_string))
        elif action == message_models.Actions.state_update:
            model = message_models.StateChangedModel.from_json(data)
            if model.new_state == message_models.StateChangedModel.States.started:
                logger.info("Launched Game")
                self.game_launched.emit(self.app_name)
                meta_data = self.game_meta.get_game(self.app_name)
                meta_data.last_played = datetime.datetime.now()
                self.game_meta.set_game(self.app_name, meta_data)

    def _socket_connected(self):
        self.timer.stop()
        self.timer.deleteLater()
        logger.info(f"Connection established for {self.app_name}")
        if self.on_startup:
            logger.info(f"Found {self.app_name} running at startup")

            # FIXME run this after startup, widgets do not exist at this time
            QTimer.singleShot(1000, lambda: self.game_launched.emit(self.app_name))

    def _error_occurred(self, _):
        if self.on_startup:
            self.socket.close()
            self.deleteLater()
            self._game_finished(-1234)  # 1234 is exit code for startup
        logger.error(f"{self.app_name}: {self.socket.errorString()}")

    def _game_finished(self, exit_code: int):
        self.game_finished.emit(exit_code, self.app_name)


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

        self.cloud_save_utils = CloudSaveUtils()
        self.cloud_save_utils.sync_finished.connect(self.sync_finished)
        self.game_meta = RareGameMeta()

        for igame in self.core.get_installed_list():
            game_process = GameProcess(igame.app_name, True)
            game_process.game_finished.connect(self.game_finished)
            game_process.game_launched.connect(self.game_launched.emit)
            self.running_games[igame.app_name] = game_process

    def uninstall_game(self, app_name) -> bool:
        # returns if uninstalled
        game = self.core.get_game(app_name)
        igame = self.core.get_installed_game(app_name)
        if not os.path.exists(igame.install_path):
            if QMessageBox.Yes == QMessageBox.question(
                    None,
                    self.tr("Uninstall - {}").format(igame.title),
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

        proceed, keep_files, keep_config = UninstallDialog(game).get_options()
        if not proceed:
            return False
        success, message = legendary_utils.uninstall_game(self.core, game.app_name, keep_files, keep_config)
        if not success:
            QMessageBox.warning(None, self.tr("Uninstall - {}").format(igame.title), message, QMessageBox.Close)
        self.signals.game_uninstalled.emit(app_name)
        return True

    def prepare_launch(
            self, app_name, offline: bool = False, skip_update_check: bool = False
    ):
        game = self.core.get_game(app_name)
        dont_sync_after_finish = False

        # TODO move this to helper
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
        executable = misc.get_rare_executable()
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

        # kill me, if I don't change it before commit
        QProcess.startDetached(executable, args)
        logger.info(f"Start new Process: ({executable} {' '.join(args)})")
        game_process = GameProcess(app_name, ask_always_sync)
        game_process.game_finished.connect(self.game_finished)
        game_process.game_launched.connect(self.game_launched.emit)
        self.running_games[app_name] = game_process

    def game_finished(self, exit_code, app_name):
        if self.running_games.get(app_name):
            self.running_games.pop(app_name)
        if exit_code == -1234:
            return

        self.finished.emit(app_name, "")

        logger.info(f"Game exited with exit code: {exit_code}")
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

        if app_name in self.running_games.keys():
            self.running_games.pop(app_name)

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

            # TODO move this to helper
            self.cloud_save_utils.game_finished(app_name, always_ask=False)

    def sync_finished(self, app_name):
        if app_name in self.launch_queue.keys():
            self.cloud_save_finished.emit(app_name)
            params = self.launch_queue[app_name]
            self.launch_queue.pop(app_name)
            self.launch_game(*params)
        else:
            self.cloud_save_finished.emit(app_name)
