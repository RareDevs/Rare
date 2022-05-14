import json
import sys
import time
from logging import getLogger
from typing import List, Union

from PyQt5.QtCore import QObject, QProcess, pyqtSignal, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtNetwork import QLocalServer, QLocalSocket
from PyQt5.QtWidgets import QApplication, QPushButton

from .lgd_helper import get_launch_args, LaunchArgs, get_configured_process
from legendary.core import LegendaryCore


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
        ret = self.server.listen(f"rare1_{self.app_name}")
        if not ret:
            self.logger.info(self.server.errorString())
            print("Server is running")
            self.server.close()
            self.success = False
            return
        self.server.newConnection.connect(self.new_server_connection)

        self.game_process.finished.connect(self.game_finished)
        self.start_time = time.time()

    def prepare_launch(self, app_name) -> List[str]:
        args = get_launch_args(self.core, LaunchArgs(app_name))
        if not args:
            return []

        self.game_process.setProcessEnvironment(args.env)

        if args.pre_launch_command:
            proc = get_configured_process()
            proc.setProcessEnvironment(args.env)
            proc.start(args.pre_launch_command[0], args.pre_launch_command[1:])
            if args.pre_launch_wait:
                proc.waitForFinished(-1)

        return [
            args.executable, args.args, args.is_origin_game
        ]

    def new_server_connection(self):
        if self.socket is not None:
            self.socket.disconnectFromServer()
        self.logger.info("New connection")
        self.socket = self.server.nextPendingConnection()
        self.socket.disconnected.connect(self.socket.deleteLater)
        self.socket.flush()

    def send_message(self, message: Union[bytes, str]):
        if isinstance(message, str):
            message = message.encode("utf-8")
        if self.socket:
            self.socket.write(message)
            self.socket.flush()
        else:
            print("Can't send message")

    def game_finished(self, exit_code):
        print("game finished")
        self.send_message(
            json.dumps({
                "action": "finished",
                "app_name": self.app_name,
                "exit_code": exit_code,
                "playtime": int(time.time() - self.start_time)
            })
        )
        self.exit_app.emit()

    def start(self, app_name):
        # if offline
        try:
            if not self.core.login():
                raise ValueError("You are not logged in")
        except ValueError:
            # automatically launch offline if available
            self.logger.error("Not logged in. Try to launch game offline")
            # offline = True

        args = self.prepare_launch(app_name)
        if not args:
            print(args)
            self.server.close()
            self.server.deleteLater()
            return
        if args[2]:
            # origin game on Windows
            QDesktopServices.openUrl(QUrl(args[2]))
            return
        self.game_process.start(*args[:2])
        self.start_time = time.time()


def start_game(app_name: str):
    app = QApplication(sys.argv)
    helper = GameProcessHelper(app_name)
    if not helper.success:
        return
    helper.start(app_name)
    helper.exit_app.connect(lambda: app.exit(0))

    # this button is for debug. Closing with keyboard interrupt does not kill the server
    quit_button = QPushButton("Quit")
    quit_button.show()
    quit_button.clicked.connect(lambda: app.exit(0))
    app.exec_()
    helper.server.close()


if __name__ == '__main__':
    # TODO add argparse for offline app name, wine prefix/binary ...
    start_game("963137e4c29d4c79a81323b8fab03a40")
