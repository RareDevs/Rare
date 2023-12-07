import json
import platform
import subprocess
import time
import traceback
from argparse import Namespace
from logging import getLogger
from signal import signal, SIGINT, SIGTERM, strsignal
from typing import Optional

from PyQt5.QtCore import QObject, QProcess, pyqtSignal, QUrl, QRunnable, QThreadPool, QSettings, Qt, pyqtSlot
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtNetwork import QLocalServer, QLocalSocket
from PyQt5.QtWidgets import QApplication
from legendary.models.game import SaveGameStatus

from rare.components.dialogs.cloud_save_dialog import CloudSaveDialog
from rare.lgndr.core import LegendaryCore
from rare.models.base_game import RareGameSlim
from rare.models.launcher import ErrorModel, Actions, FinishedModel, BaseModel, StateChangedModel
from rare.widgets.rare_app import RareApp, RareAppException
from .console import Console
from .lgd_helper import get_launch_args, InitArgs, get_configured_process, LaunchArgs, GameArgsError

DETACHED_APP_NAMES = [
    "0a2d9f6403244d12969e11da6713137b"  # Fall Guys
    "Fortnite"
]


class PreLaunchThread(QRunnable):
    class Signals(QObject):
        ready_to_launch = pyqtSignal(LaunchArgs)
        started_pre_launch_command = pyqtSignal()
        pre_launch_command_finished = pyqtSignal(int)  # exit_code
        error_occurred = pyqtSignal(str)

    def __init__(self, core: LegendaryCore, args: InitArgs, rgame: RareGameSlim, sync_action=None):
        super(PreLaunchThread, self).__init__()
        self.logger = getLogger(type(self).__name__)
        self.core = core
        self.signals = self.Signals()
        self.args = args
        self.rgame = rgame
        self.sync_action = sync_action

    def run(self) -> None:
        self.logger.info(f"Sync action: {self.sync_action}")
        if self.sync_action == CloudSaveDialog.UPLOAD:
            self.rgame.upload_saves(False)
        elif self.sync_action == CloudSaveDialog.DOWNLOAD:
            self.rgame.download_saves(False)
        else:
            self.logger.info("No sync action")

        args = self.prepare_launch(self.args)
        if not args:
            return
        self.signals.ready_to_launch.emit(args)

    def prepare_launch(self, args: InitArgs) -> Optional[LaunchArgs]:
        try:
            launch_args = get_launch_args(self.core, args)
        except Exception as e:
            self.signals.error_occurred.emit(str(e))
            return None
        if not launch_args:
            return None

        if launch_args.pre_launch_command:
            proc = get_configured_process()
            proc.setProcessEnvironment(launch_args.environment)
            self.signals.started_pre_launch_command.emit()
            proc.start(launch_args.pre_launch_command[0], launch_args.pre_launch_command[1:])
            if launch_args.pre_launch_wait:
                proc.waitForFinished(-1)
        return launch_args


class SyncCheckWorker(QRunnable):
    class Signals(QObject):
        sync_state_ready = pyqtSignal()
        error_occurred = pyqtSignal(str)

    def __init__(self, core: LegendaryCore, rgame: RareGameSlim):
        super().__init__()
        self.signals = self.Signals()
        self.core = core
        self.rgame = rgame

    def run(self) -> None:
        try:
            self.rgame.update_saves()
        except Exception as e:
            self.signals.error_occurred.emit(str(e))
            return
        self.signals.sync_state_ready.emit()


class RareLauncherException(RareAppException):
    def __init__(self, app: 'RareLauncher', args: Namespace, parent=None):
        super(RareLauncherException, self).__init__(parent=parent)
        self.__app = app
        self.__args = args

    def _handler(self, exc_type, exc_value, exc_tb) -> bool:
        try:
            self.__app.send_message(ErrorModel(
                app_name=self.__args.app_name,
                action=Actions.error,
                error_string="".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            ))
        except RuntimeError:
            pass
        return False


class RareLauncher(RareApp):
    exit_app = pyqtSignal()

    def __init__(self, args: InitArgs):
        super(RareLauncher, self).__init__(args, f"{type(self).__name__}_{args.app_name}_{{0}}.log")
        self.socket: Optional[QLocalSocket] = None
        self.console: Optional[Console] = None
        self.game_process: QProcess = QProcess(self)
        self.server: QLocalServer = QLocalServer(self)

        self._hook.deleteLater()
        self._hook = RareLauncherException(self, args, self)

        self.success: bool = False
        self.no_sync_on_exit = False
        self.args = args
        self.core = LegendaryCore()
        game = self.core.get_game(args.app_name)
        if not game:
            self.logger.error(f"Game {args.app_name} not found. Exiting")
            return
        self.rgame = RareGameSlim(self.core, game)

        lang = self.settings.value("language", self.core.language_code, type=str)
        self.load_translator(lang)

        if QSettings().value("show_console", False, bool):
            self.console = Console()
            self.console.show()

        self.game_process.finished.connect(self.__process_finished)
        self.game_process.errorOccurred.connect(self.__process_errored)
        if self.console:
            self.game_process.readyReadStandardOutput.connect(self.__proc_log_stdout)
            self.game_process.readyReadStandardError.connect(self.__proc_log_stderr)
            self.console.term.connect(self.__proc_term)
            self.console.kill.connect(self.__proc_kill)

        ret = self.server.listen(f"rare_{args.app_name}")
        if not ret:
            self.logger.error(self.server.errorString())
            self.logger.info("Server is running")
            self.server.close()
            return
        self.server.newConnection.connect(self.new_server_connection)

        self.success = True
        self.start_time = time.time()

    @pyqtSlot()
    def __proc_log_stdout(self):
        self.console.log(
            self.game_process.readAllStandardOutput().data().decode("utf-8", "ignore")
        )

    @pyqtSlot()
    def __proc_log_stderr(self):
        self.console.error(
            self.game_process.readAllStandardError().data().decode("utf-8", "ignore")
        )

    @pyqtSlot()
    def __proc_term(self):
        self.game_process.terminate()

    @pyqtSlot()
    def __proc_kill(self):
        self.game_process.kill()

    def new_server_connection(self):
        if self.socket is not None:
            try:
                self.socket.disconnectFromServer()
            except RuntimeError:
                pass
        self.logger.info("New connection")
        self.socket = self.server.nextPendingConnection()
        self.socket.disconnected.connect(self.socket_disconnected)
        self.socket.flush()

    def socket_disconnected(self):
        self.logger.info("Server disconnected")
        self.socket.deleteLater()
        self.socket = None

    def send_message(self, message: BaseModel):
        if self.socket:
            self.socket.write(json.dumps(vars(message)).encode("utf-8"))
            self.socket.flush()
        else:
            self.logger.error("Can't send message")

    def check_saves_finished(self, exit_code: int):
        self.rgame.signals.widget.update.connect(lambda: self.on_exit(exit_code))

        state, (dt_local, dt_remote) = self.rgame.save_game_state

        if state == SaveGameStatus.LOCAL_NEWER and not self.no_sync_on_exit:
            action = CloudSaveDialog.UPLOAD
        else:
            action = CloudSaveDialog(self.rgame.igame, dt_local, dt_remote).get_action()

        if action == CloudSaveDialog.UPLOAD:
            if self.console:
                self.console.log("Uploading saves...")
            self.rgame.upload_saves()
        elif action == CloudSaveDialog.DOWNLOAD:
            if self.console:
                self.console.log("Downloading saves...")
            self.rgame.download_saves()
        else:
            self.on_exit(exit_code)

    @pyqtSlot(int, QProcess.ExitStatus)
    def __process_finished(self, exit_code: int, exit_status: QProcess.ExitStatus):
        self.logger.info("Game finished")

        if self.rgame.auto_sync_saves:
            self.check_saves_finished(exit_code)
        else:
            self.on_exit(exit_code)

    @pyqtSlot(QProcess.ProcessError)
    def __process_errored(self, error: QProcess.ProcessError):
        self.error_occurred(self.game_process.errorString())

    def on_exit(self, exit_code: int):
        if self.console:
            self.console.on_process_exit(self.core.get_game(self.rgame.app_name).app_title, exit_code)

        self.send_message(
            FinishedModel(
                action=Actions.finished,
                app_name=self.rgame.app_name,
                exit_code=exit_code,
                playtime=int(time.time() - self.start_time)
            )

        )
        self.stop()

    @pyqtSlot(object)
    def launch_game(self, args: LaunchArgs):
        # should never happen
        if not args:
            self.stop()
            return
        if self.console:
            self.console.set_env(args.environment)
        self.start_time = time.time()

        if args.is_origin_game:
            QDesktopServices.openUrl(QUrl(args.executable))
            self.stop()  # stop because it is no subprocess
            return

        if args.working_directory:
            self.game_process.setWorkingDirectory(args.working_directory)
        self.game_process.setProcessEnvironment(args.environment)
        # send start message after process started
        self.game_process.started.connect(lambda: self.send_message(
            StateChangedModel(
                action=Actions.state_update, app_name=self.rgame.app_name,
                new_state=StateChangedModel.States.started
            )
        ))
        if self.rgame.app_name in DETACHED_APP_NAMES and platform.system() == "Windows":
            self.game_process.deleteLater()
            subprocess.Popen([args.executable] + args.arguments, cwd=args.working_directory,
                             env={i: args.environment.value(i) for i in args.environment.keys()})
            if self.console:
                self.console.log("Launching game as a detached process")
            self.stop()
            return
        if self.args.dry_run:
            self.logger.info("Dry run activated")
            if self.console:
                self.console.log(f"{args.executable} {' '.join(args.arguments)}")
                self.console.log(f"Do not start {self.rgame.app_name}")
                self.console.accept_close = True
            print(args.executable, " ".join(args.arguments))
            self.stop()
            return
        self.game_process.start(args.executable, args.arguments)

    def error_occurred(self, error_str: str):
        self.logger.warning(error_str)
        if self.console:
            self.console.on_process_exit(self.core.get_game(self.rgame.app_name).app_title, error_str)
        self.send_message(ErrorModel(
            error_string=error_str, app_name=self.rgame.app_name,
            action=Actions.error)
        )
        self.stop()

    def start_prepare(self, sync_action=None):
        worker = PreLaunchThread(self.core, self.args, self.rgame, sync_action)
        worker.signals.ready_to_launch.connect(self.launch_game)
        worker.signals.error_occurred.connect(self.error_occurred)
        # worker.signals.started_pre_launch_command(None)

        QThreadPool.globalInstance().start(worker)

    def sync_ready(self):
        if self.rgame.is_save_up_to_date:
            if self.console:
                self.console.log("Sync worker ready. Sync not required")
            self.start_prepare()
            return

        _, (dt_local, dt_remote) = self.rgame.save_game_state
        dlg = CloudSaveDialog(self.rgame.igame, dt_local, dt_remote)
        action = dlg.get_action()
        if action == CloudSaveDialog.CANCEL:
            self.no_sync_on_exit = True
        if self.console:
            if action == CloudSaveDialog.DOWNLOAD:
                self.console.log("Downloading saves...")
            elif action == CloudSaveDialog.UPLOAD:
                self.console.log("Uploading saves...")
        self.start_prepare(action)

    def start(self, args: InitArgs):
        if not args.offline:
            try:
                if not self.core.login():
                    raise ValueError("You are not logged in")
            except ValueError:
                # automatically launch offline if available
                self.logger.error("Not logged in. Trying to launch the game in offline mode")
                args.offline = True

        if not args.offline and self.rgame.auto_sync_saves:
            self.logger.info("Start sync worker")
            worker = SyncCheckWorker(self.core, self.rgame)
            worker.signals.error_occurred.connect(self.error_occurred)
            worker.signals.sync_state_ready.connect(self.sync_ready)
            QThreadPool.globalInstance().start(worker)
            return
        else:
            self.start_prepare()

    def stop(self):
        try:
            if self.console:
                self.game_process.readyReadStandardOutput.disconnect()
                self.game_process.readyReadStandardError.disconnect()
            if self.game_process.receivers(self.game_process.finished):
                self.game_process.finished.disconnect()
            if self.game_process.receivers(self.game_process.errorOccurred):
                self.game_process.errorOccurred.disconnect()
        except TypeError as e:
            self.logger.error(f"Failed to disconnect process signals: {e}")

        self.logger.info("Stopping server")
        try:
            self.server.close()
            self.server.deleteLater()
        except RuntimeError:
            pass
        self.processEvents()
        if not self.console:
            self.exit()
        else:
            self.console.on_process_exit(self.rgame.app_name, 0)


def launch(args: Namespace) -> int:
    args = InitArgs.from_argparse(args)

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = RareLauncher(args)
    app.setQuitOnLastWindowClosed(True)

    # This prevents ghost QLocalSockets, which block the name, which makes it unable to start
    # No handling for SIGKILL
    def sighandler(s, frame):
        app.logger.info(f"{strsignal(s)} received. Stopping")
        app.stop()
        app.exit(1)
    signal(SIGINT, sighandler)
    signal(SIGTERM, sighandler)

    if not app.success:
        app.stop()
        app.exit(1)
        return 1
    app.start(args)
    # app.exit_app.connect(lambda: app.exit(0))

    return app.exec_()
