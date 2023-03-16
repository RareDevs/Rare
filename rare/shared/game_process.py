import json
import logging
from enum import IntEnum

from PyQt5.QtCore import QObject, pyqtSignal, QTimer, pyqtSlot
from PyQt5.QtNetwork import QLocalSocket
from PyQt5.QtWidgets import QMessageBox
from legendary.models.game import Game

from rare.models.launcher import ErrorModel, Actions, FinishedModel, StateChangedModel

logger = logging.getLogger("GameProcess")


class GameProcess(QObject):
    # int: code
    launched = pyqtSignal(int)
    # int: code
    finished = pyqtSignal(int)

    class Code(IntEnum):
        SUCCESS = 0
        ERROR = 1
        TIMEOUT = -1
        ON_STARTUP = -1234

    def __init__(self, game: Game):
        super(GameProcess, self).__init__()
        self.game = game
        self.on_startup = False
        self.tried_connections = 0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.__connect)
        self.socket = QLocalSocket()
        self.socket_name = f"rare_{self.game.app_name}"

        self.socket.connected.connect(self.__on_connected)
        try:
            self.socket.errorOccurred.connect(self.__on_error)
        except AttributeError:
            # QTimer.singleShot(
            #     100,
            #     lambda: self._error_occurred(QLocalSocket.UnknownSocketError) if self.socket.error() else None
            # )
            logger.warning("Do not handle errors on QLocalSocket, because of an old qt version")
        self.socket.readyRead.connect(self.__on_message)
        self.socket.disconnected.connect(self.__close)

    def connect_to_server(self, on_startup: bool):
        self.on_startup = on_startup
        self.timer.start(200)

    @pyqtSlot()
    def __close(self):
        try:
            self.socket.close()
        except RuntimeError:
            pass

    @pyqtSlot()
    def __connect(self):
        self.socket.connectToServer(self.socket_name)
        self.tried_connections += 1

        if self.tried_connections > 50:  # 10 seconds
            QMessageBox.warning(None, "Error", self.tr("Connection to game process failed (Timeout)"))
            self.timer.stop()
            self.finished.emit(GameProcess.Code.TIMEOUT)

    @pyqtSlot()
    def __on_message(self):
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

        action = data.get("action", False)

        if not action:
            logger.error("Got unexpected action")
        elif action == Actions.finished:
            logger.info(f"{self.game.app_name} {self.game.app_title} finished")
            model = FinishedModel.from_json(data)
            self.socket.close()
            self.__game_finished(model.exit_code)
        elif action == Actions.error:
            model = ErrorModel.from_json(data)
            logger.error(f"Error in game {self.game.app_title}: {model.error_string}")
            self.socket.close()
            self.__game_finished(GameProcess.Code.ERROR)
            QMessageBox.warning(None, "Error", self.tr(
                "Error in game {}:\n{}").format(self.game.app_title, model.error_string))
        elif action == Actions.state_update:
            model = StateChangedModel.from_json(data)
            if model.new_state == StateChangedModel.States.started:
                logger.info("Launched Game")
                self.launched.emit(GameProcess.Code.SUCCESS)

    @pyqtSlot()
    def __on_connected(self):
        self.timer.stop()
        logger.info(f"Connection established for {self.game.app_name} ({self.game.app_title})")
        if self.on_startup:
            logger.info(f"Found {self.game.app_name} ({self.game.app_title}) running at startup")
            self.launched.emit(GameProcess.Code.ON_STARTUP)

    @pyqtSlot(QLocalSocket.LocalSocketError)
    def __on_error(self, _: QLocalSocket.LocalSocketError):
        if self.on_startup:
            self.timer.stop()
            self.__close()
            self.__game_finished(GameProcess.Code.ON_STARTUP)  # 1234 is exit code for startup
        logger.error(f"{self.game.app_name} ({self.game.app_title}): {self.socket.errorString()}")

    def __game_finished(self, exit_code: int):
        self.finished.emit(exit_code)
