import json
import logging
from enum import IntEnum
from typing import TYPE_CHECKING

from PyQt5.QtCore import QObject, pyqtSignal, QTimer, pyqtSlot
from PyQt5.QtNetwork import QLocalSocket
from PyQt5.QtWidgets import QMessageBox

from rare.models.launcher import ErrorModel, Actions, FinishedModel, StateChangedModel

logger = logging.getLogger("GameProcess")

if TYPE_CHECKING:
    from rare.models.game import RareGame


class GameProcess(QObject):
    # int: code
    launched = pyqtSignal(int)
    # int: code
    finished = pyqtSignal(int)

    class Code(IntEnum):
        SUCCESS = 0
        TIMEOUT = -1
        ON_STARTUP = -1234

    def __init__(self, rgame: 'RareGame'):
        super(GameProcess, self).__init__()
        self.rgame = rgame
        self.on_startup = False
        self.tried_connections = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self.__connect)
        self.socket = QLocalSocket()
        self.socket_name = f"rare_{self.rgame.app_name}"

        self.socket.connected.connect(self._socket_connected)
        # if hasattr(self.socket, "errorOccured"):
        #     self.socket.errorOccurred.connect(self._error_occurred)
        # else:
        #     QTimer.singleShot(
        #         100,
        #         lambda: self._error_occurred(QLocalSocket.UnknownSocketError) if self.socket.error() else None
        #     )
        #     logger.warning("Do not handle errors on QLocalSocket, because of an old qt version")
        try:
            self.socket.errorOccurred.connect(self._error_occurred)
        except AttributeError:
            # QTimer.singleShot(
            #     100,
            #     lambda: self._error_occurred(QLocalSocket.UnknownSocketError) if self.socket.error() else None
            # )
            logger.warning("Do not handle errors on QLocalSocket, because of an old qt version")
        self.socket.readyRead.connect(self._message_available)
        self.socket.disconnected.connect(self.__close)

    def connect(self, on_startup: bool):
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

        action = data.get("action", False)

        if not action:
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
                "Error in game {}:\n{}").format(self.rgame.app_title, model.error_string))

        elif action == Actions.state_update:
            model = StateChangedModel.from_json(data)
            if model.new_state == StateChangedModel.States.started:
                logger.info("Launched Game")
                self.launched.emit(GameProcess.Code.SUCCESS)

    @pyqtSlot()
    def _socket_connected(self):
        self.timer.stop()
        logger.info(f"Connection established for {self.rgame.app_name} ({self.rgame.app_title})")
        if self.on_startup:
            logger.info(f"Found {self.rgame.app_name} ({self.rgame.app_title}) running at startup")
            self.launched.emit(GameProcess.Code.ON_STARTUP)

    @pyqtSlot(QLocalSocket.LocalSocketError)
    def _error_occurred(self, _: QLocalSocket.LocalSocketError):
        if self.on_startup:
            self.timer.stop()
            self.socket.close()
            self._game_finished(GameProcess.Code.ON_STARTUP)  # 1234 is exit code for startup
        logger.error(f"{self.rgame.app_name} ({self.rgame.app_title}): {self.socket.errorString()}")

    def _game_finished(self, exit_code: int):
        self.finished.emit(exit_code)
