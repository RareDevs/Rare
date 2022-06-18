import json
import logging
import sys
import time
import traceback
from argparse import Namespace
from logging import getLogger
from typing import Union

from PyQt5.QtCore import QObject, QProcess, pyqtSignal, QUrl, QRunnable, QThreadPool
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtNetwork import QLocalServer, QLocalSocket
from PyQt5.QtWidgets import QApplication

from .lgd_helper import get_launch_args, InitArgs, get_configured_process, LaunchArgs, GameArgsError
from .message_models import ErrorModel, Actions, FinishedModel, BaseModel, StateChangedModel
from ..shared import LegendaryCoreSingleton


class PreLaunchThread(QRunnable):
    class Signals(QObject):
        ready_to_launch = pyqtSignal(LaunchArgs)
        started_pre_launch_command = pyqtSignal()
        pre_launch_command_finished = pyqtSignal(int)  # exit_code
        error_occurred = pyqtSignal(str)

    def __init__(self, args: InitArgs):
        super(PreLaunchThread, self).__init__()
        self.core = LegendaryCoreSingleton()
        self.app_name = args.app_name
        self.signals = self.Signals()

    def run(self) -> None:
        args = self.prepare_launch(self.app_name)
        if not args:
            return
        self.signals.ready_to_launch.emit(args)

    def prepare_launch(self, app_name) -> Union[LaunchArgs, None]:
        try:
            args = get_launch_args(self.core, InitArgs(app_name))
        except GameArgsError as e:
            self.signals.error_occurred.emit(str(e))
            return None
        if not args:
            return None

        if args.pre_launch_command:
            proc = get_configured_process()
            proc.setProcessEnvironment(args.env)
            self.signals.started_pre_launch_command.emit()
            proc.start(args.pre_launch_command[0], args.pre_launch_command[1:])
            if args.pre_launch_wait:
                proc.waitForFinished(-1)
        return args


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
        self.core = LegendaryCoreSingleton(True)

        self.server = QLocalServer()
        ret = self.server.listen(f"rare_{self.app_name}")
        if not ret:
            self.logger.error(self.server.errorString())
            self.logger.info("Server is running")
            self.server.close()
            self.success = False
            return
        self.server.newConnection.connect(self.new_server_connection)

        self.game_process.finished.connect(self.game_finished)
        self.game_process.errorOccurred.connect(
            lambda err: self.error_occurred(self.game_process.errorString()))

        self.start_time = time.time()

    def new_server_connection(self):
        if self.socket is not None:
            try:
                self.socket.disconnectFromServer()
            except RuntimeError:
                pass
        self.logger.info("New connection")
        self.socket = self.server.nextPendingConnection()
        self.socket.disconnected.connect(self.socket.deleteLater)
        self.socket.disconnected.connect(lambda: self.logger.info("Server disconnected"))

        self.socket.flush()

    def send_message(self, message: BaseModel):
        if self.socket:
            self.socket.write(json.dumps(message.__dict__).encode("utf-8"))
            self.socket.flush()
        else:
            self.logger.error("Can't send message")

    def game_finished(self, exit_code):
        self.logger.info("game finished")
        self.send_message(
            FinishedModel(
                action=Actions.finished,
                app_name=self.app_name,
                exit_code=exit_code,
                playtime=int(time.time() - self.start_time)
            )

        )
        self.stop()

    def launch_game(self, args: LaunchArgs):
        # should never happen
        if not args:
            self.stop()
            return

        self.start_time = time.time()

        if args.is_origin_game:
            QDesktopServices.openUrl(QUrl(args.executable))
            self.stop()  # stop because it is no subprocess
            return

        if args.cwd:
            self.game_process.setWorkingDirectory(args.cwd)

        self.game_process.start(args.executable, args.args)
        self.send_message(
            StateChangedModel(
                action=Actions.state_update, app_name=self.app_name,
                new_state=StateChangedModel.States.started
            )
        )

    def error_occurred(self, error_str: str):
        self.logger.warning(error_str)
        self.send_message(ErrorModel(
            error_string=error_str, app_name=self.app_name,
            action=Actions.error)
        )
        self.stop()

    def start(self, args: InitArgs):
        if not args.offline:
            try:
                if not self.core.login():
                    raise ValueError("You are not logged in")
            except ValueError:
                # automatically launch offline if available
                self.logger.error("Not logged in. Try to launch game offline")
                args.offline = True

        worker = PreLaunchThread(args)
        worker.signals.ready_to_launch.connect(self.launch_game)
        worker.signals.error_occurred.connect(self.error_occurred)
        # worker.signals.started_pre_launch_command(None)

        QThreadPool.globalInstance().start(worker)

    def stop(self):
        self.logger.info("Stopping server")
        self.server.close()
        self.server.deleteLater()
        self.exit_app.emit()


def start_game(args: Namespace):
    args = InitArgs.from_argparse(args)
    logging.basicConfig(
        format="[%(name)s] %(levelname)s: %(message)s",
        level=logging.INFO,
    )

    app = QApplication(sys.argv)

    helper = GameProcessHelper(args.app_name)

    def excepthook(exc_type, exc_value, exc_tb):
        tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        helper.logger.fatal(tb)
        try:
            helper.send_message(ErrorModel(
                app_name=args.app_name,
                action=Actions.error,
                error_string=tb
            ))
        except RuntimeError:
            pass
        helper.stop()

    sys.excepthook = excepthook
    if not helper.success:
        return
    helper.start(args)
    helper.exit_app.connect(lambda: app.exit(0))

    # this button is for debug. Closing with keyboard interrupt does not kill the server
    # quit_button = QPushButton("Quit")
    # quit_button.show()
    # quit_button.clicked.connect(lambda: app.exit(0))
    app.exec_()
