import datetime
import json
import os
import sys
import time
from logging import getLogger
from typing import List, Union

from PyQt5.QtCore import QObject, QCoreApplication, QProcess, pyqtSignal
from PyQt5.QtNetwork import QLocalServer, QLocalSocket

from rare.legendary.legendary.core import LegendaryCore


class GameProcessHelper(QObject):
    game_process: QProcess
    server: QLocalServer
    socket: QLocalSocket = None
    exit_app = pyqtSignal()
    success: bool = True

    def __init__(self, app_name: str):
        super(GameProcessHelper, self).__init__()
        self.game_process = QProcess()
        self.app_name = app_name
        self.logger = getLogger(self.app_name)
        self.core = LegendaryCore()

        self.server = QLocalServer()
        ret = self.server.listen(f"rare_{self.app_name}")
        if not ret:
            self.logger.info(self.server.errorString())
            print("Error")
            self.server.close()
            self.success = False
            return
        self.server.newConnection.connect(self.new_server_connection)

        self.game_process.readyReadStandardOutput.connect(
            lambda: print(
                str(self.game_process.readAllStandardOutput().data(), "utf-8", "ignore")
            )
        )
        self.game_process.readyReadStandardError.connect(
            lambda: print(
                str(self.game_process.readAllStandardError().data(), "utf-8", "ignore")
            )
        )
        self.game_process.finished.connect(self.game_finished)
        self.start_time = time.time()

    def get_args(self) -> List[str]:
        # self.core.whatever
        return [
            "python", os.path.expanduser("~/testx.py")
        ]

    def new_server_connection(self):
        if self.socket is not None:
            self.socket.disconnectFromServer()
        self.logger.info("New connection")
        self.socket = self.server.nextPendingConnection()
        self.socket.disconnected.connect(self.socket.deleteLater)
        self.socket.write(b'Test')
        self.socket.flush()

    def send_message(self, message: Union[bytes, str]):
        if isinstance(message, str):
            message = message.encode("utf-8")
        if self.socket:
            self.socket.write(message)
            self.socket.flush()
        else:
            print("error: ", self.socket.errorString())

    def game_finished(self, exit_code):
        print("game finished")
        self.send_message(
            json.dumps({
                "action": "finished",
                "exit_code": exit_code,
                "playtime": int(time.time() - self.start_time)
            })
        )
        self.exit_app.emit()

    def start(self):
        args = self.get_args()
        self.game_process.start(args[0], args[1:])
        self.start_time = time.time()


def run_game(app_name: str):
    app = QCoreApplication(sys.argv)
    helper = GameProcessHelper(app_name)
    if not helper.success:
        return
    helper.start()
    helper.exit_app.connect(lambda: app.exit(0))
    app.exec_()
    helper.server.close()


if __name__ == '__main__':
    run_game("CrabEA")
