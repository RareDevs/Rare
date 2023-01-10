import datetime
import json
import logging

from PyQt5.QtCore import QObject, pyqtSignal, QTimer, pyqtSlot
from PyQt5.QtNetwork import QLocalSocket
from PyQt5.QtWidgets import QMessageBox

from rare.models.game import RareGame
from rare.models.launcher import ErrorModel, Actions, FinishedModel, StateChangedModel

logger = logging.getLogger("GameProcess")


class GameProcess(QObject):
    # str: app_name, int: exit_code
    game_finished = pyqtSignal(RareGame, int)
    # str: app_name
    game_launched = pyqtSignal(RareGame)

    def __init__(self, rgame: RareGame, on_startup=False, always_ask_sync: bool = False):
        super(GameProcess, self).__init__()
        self.rgame = rgame
        self.on_startup = on_startup
        self.tried_connections = 0
        self.socket = QLocalSocket()
        self.socket.connected.connect(self._socket_connected)
        try:
            self.socket.errorOccurred.connect(self._error_occurred)
        except AttributeError:
            QTimer.singleShot(100, lambda: self._error_occurred(QLocalSocket.UnknownSocketError) if self.socket.error() else None)
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
        self.socket.connectToServer(f"rare_{self.rgame.app_name}")
        self.tried_connections += 1

        if self.tried_connections > 50:  # 10 seconds
            QMessageBox.warning(None, "Error", self.tr("Connection to game process failed (Timeout)"))
            self.timer.stop()
            self.game_finished.emit(self.rgame, 1)

    @pyqtSlot()
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
        elif action == Actions.finished:
            logger.info(f"{self.rgame.app_name} {self.rgame.app_title} finished")
            model = FinishedModel.from_json(data)
            self.socket.close()
            self._game_finished(model.exit_code)
        elif action == Actions.error:
            model = ErrorModel.from_json(data)
            logger.error(f"Error in game {self.rgame.app_title}: {model.error_string}")
            self.socket.close()
            self._game_finished(1)
            QMessageBox.warning(None, "Error", self.tr(
                "Error in game {}: \n{}").format(self.rgame.app_title, model.error_string))

        elif action == Actions.state_update:
            model = StateChangedModel.from_json(data)
            if model.new_state == StateChangedModel.States.started:
                logger.info("Launched Game")
                self.game_launched.emit(self.rgame)
                meta_data = self.rgame.metadata
                meta_data.last_played = datetime.datetime.now()
                self.rgame.save_metadata()

    @pyqtSlot()
    def _socket_connected(self):
        self.timer.stop()
        self.timer.deleteLater()
        logger.info(f"Connection established for {self.rgame.app_name} ({self.rgame.app_title})")
        if self.on_startup:
            logger.info(f"Found {self.rgame.app_name} ({self.rgame.app_title}) running at startup")

            # FIXME run this after startup, widgets do not exist at this time
            QTimer.singleShot(1000, lambda: self.game_launched.emit(self.rgame))

    @pyqtSlot(QLocalSocket.LocalSocketError)
    def _error_occurred(self, _: QLocalSocket.LocalSocketError):
        if self.on_startup:
            self.socket.close()
            self._game_finished(-1234)  # 1234 is exit code for startup
        logger.error(f"{self.rgame.app_name} ({self.rgame.app_title}): {self.socket.errorString()}")

    def _game_finished(self, exit_code: int):
        self.deleteLater()
        self.game_finished.emit(self.rgame, exit_code)
