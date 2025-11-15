import json
import os
import platform
import shlex
import signal
import subprocess
import time
import traceback
from argparse import Namespace
from logging import getLogger
from typing import Optional

import shiboken6
from legendary.models.game import SaveGameStatus

# from PySide6.import sip
from PySide6.QtCore import (
    QMetaMethod,
    QObject,
    QProcess,
    QRunnable,
    Qt,
    QThreadPool,
    QTimer,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import QDesktopServices
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication

from rare.lgndr.core import LegendaryCore
from rare.models.base_game import RareGameSlim
from rare.models.launcher import Actions, BaseModel, ErrorModel, FinishedModel, StateChangedModel
from rare.utils.paths import get_rare_executable
from rare.widgets.rare_app import RareApp, RareAppException

from .cloud_sync_dialog import CloudSyncDialog, CloudSyncDialogResult
from .console_dialog import ConsoleDialog
from .lgd_helper import InitParams, LaunchParams, dict_to_qprocenv, get_configured_qprocess, get_launch_params

DETACHED_APP_NAMES = {
    "0a2d9f6403244d12969e11da6713137b",  # Fall Guys
    "Fortnite",
    "afdb5a85efcc45d8ae8e406e2121d81c",  # Fortnite Battle Royale
    "09e442f830a341f698b4da42abd98c9b",  # Fortnite Festival
    "d8f7763e07d74c209d760a679f9ed6ac",  # Lego Fortnite
    "Fortnite_Studio",  # Unreal Editor for Fortnite
    "dcfccf8d965a4f2281dddf9fead042de",  # Homeworld Remastered Collection (issue#376)
}


class PreLaunch(QRunnable):
    class Signals(QObject):
        ready_to_launch = Signal(LaunchParams)
        pre_launch_command_started = Signal()
        pre_launch_command_finished = Signal(int)  # exit_code
        error_occurred = Signal(str)

    def __init__(self, args: InitParams, rgame: RareGameSlim, sync_action=None):
        super(PreLaunch, self).__init__()
        self.signals = self.Signals()
        self.logger = getLogger(type(self).__name__)
        self.args = args
        self.rgame = rgame
        self.sync_action = sync_action

    def run(self) -> None:
        self.logger.info(f"Sync action: {self.sync_action}")
        if self.sync_action == CloudSyncDialogResult.UPLOAD:
            self.rgame.upload_saves(False)
        elif self.sync_action == CloudSyncDialogResult.DOWNLOAD:
            self.rgame.download_saves(False)
        else:
            self.logger.info("No sync action")

        if args := self.prepare_launch(self.args):
            self.signals.ready_to_launch.emit(args)
        else:
            return

    def prepare_launch(self, args: InitParams) -> Optional[LaunchParams]:
        try:
            launch = get_launch_params(self.rgame, args)
        except Exception as e:
            self.signals.error_occurred.emit(str(e))
            return None
        if not launch:
            return None

        if launch.pre_launch_command:
            proc = get_configured_qprocess(shlex.split(launch.pre_launch_command), launch.environment)
            proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
            proc.readyReadStandardOutput.connect(
                lambda: self.logger.info(str(proc.readAllStandardOutput().data(), "utf-8", "ignore"))
            )
            self.signals.pre_launch_command_started.emit()
            self.logger.info("Running pre-launch command %s, %s", proc.program(), proc.arguments())
            if launch.pre_launch_wait:
                proc.start()
                self.logger.info("Waiting for pre-launch command to finish")
                proc.waitForFinished(-1)
            else:
                proc.startDetached()
        return launch


class SyncCheckWorker(QRunnable):
    class Signals(QObject):
        sync_state_ready = Signal()
        error_occurred = Signal(str)

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
    def __init__(self, app: "RareLauncher", args: Namespace, parent=None):
        super(RareLauncherException, self).__init__(parent=parent)
        self.__app = app
        self.__args = args

    def _handler(self, exc_type, exc_value, exc_tb) -> bool:
        try:
            self.__app.send_message(
                ErrorModel(
                    app_name=self.__args.app_name,
                    action=Actions.error,
                    error_string="".join(traceback.format_exception(exc_type, exc_value, exc_tb)),
                )
            )
        except RuntimeError:
            pass
        return False


class RareLauncher(RareApp):
    exit_app = Signal()

    def __init__(self, args: InitParams):
        super(RareLauncher, self).__init__(args, f"{type(self).__name__}_{args.app_name}_{{0}}.log")
        self.socket: Optional[QLocalSocket] = None
        self.console: Optional[ConsoleDialog] = None
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
        self.rgame = RareGameSlim(self.settings, self.core, game)

        if args.show_console:
            self.console = ConsoleDialog(game.app_title)
            self.console.show()
            self.game_process.stateChanged.connect(
                lambda s: self.console.kill_button.setEnabled(
                    self.game_process.state() == QProcess.ProcessState.Running
                )
            )
            self.game_process.stateChanged.connect(
                lambda s: self.console.terminate_button.setEnabled(
                    self.game_process.state() == QProcess.ProcessState.Running
                )
            )

        self.sync_dialog: Optional[CloudSyncDialog] = None

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

        # This launches the application after it has been instantiated.
        # The timer's signal will be serviced once we call `exec()` on the application
        QTimer.singleShot(0, self.start)

    @Slot()
    def __proc_log_stdout(self):
        self.console.log_stdout(self.game_process.readAllStandardOutput().data().decode("utf-8", "ignore"))

    @Slot()
    def __proc_log_stderr(self):
        self.console.log_stderr(self.game_process.readAllStandardError().data().decode("utf-8", "ignore"))

    @Slot()
    def __proc_term(self):
        if platform.system() == "Windows":
            self.game_process.terminate()
        else:
            os.kill(self.game_process.processId(), signal.SIGINT)

    @Slot()
    def __proc_kill(self):
        if platform.system() == "Windows":
            self.game_process.kill()
        else:
            os.kill(self.game_process.processId(), signal.SIGINT)

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
            action = CloudSyncDialogResult.UPLOAD
            self.__check_saves_finished(exit_code, action)
        else:
            self.sync_dialog = CloudSyncDialog(self.rgame.igame, dt_local, dt_remote)
            self.sync_dialog.result_ready.connect(lambda a: self.__check_saves_finished(exit_code, a))
            self.sync_dialog.open()

    @Slot(int, int)
    @Slot(int, CloudSyncDialogResult)
    def __check_saves_finished(self, exit_code, action):
        if self.sync_dialog is not None:
            self.sync_dialog.deleteLater()
            self.sync_dialog = None
        action = CloudSyncDialogResult(action)
        if action == CloudSyncDialogResult.UPLOAD:
            if self.console:
                self.console.log("Uploading saves...")
            self.rgame.upload_saves()
        elif action == CloudSyncDialogResult.DOWNLOAD:
            if self.console:
                self.console.log("Downloading saves...")
            self.rgame.download_saves()
        else:
            self.on_exit(exit_code)

    @Slot(int, QProcess.ExitStatus)
    def __process_finished(self, exit_code: int, exit_status: QProcess.ExitStatus):
        self.logger.info("Game finished")

        if self.rgame.auto_sync_saves:
            self.check_saves_finished(exit_code)
        else:
            self.on_exit(exit_code)

    @Slot(QProcess.ProcessError)
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
                playtime=int(time.time() - self.start_time),
            )
        )
        self.stop()

    @Slot(object)
    def launch_game(self, params: LaunchParams):
        # should never happen
        if not params:
            self.stop()
            return
        if self.console:
            self.console.set_env(params.environment)
        self.start_time = time.time()

        if self.args.dry_run:
            self.logger.info("Dry run %s (%s)", self.rgame.app_title, self.rgame.app_name)
            self.logger.info("Command: %s, %s", params.executable, " ".join(params.arguments))
            if self.console:
                self.console.log(f"Dry run {self.rgame.app_title} ({self.rgame.app_name})")
                self.console.log(f"{shlex.join((params.executable, *params.arguments))}")
                self.console.accept_close = True
            self.stop()
            return

        if platform.system() == "Windows" and params.is_origin_game:
            # executable is a protocol link (link2ea://launchgame/...)
            QDesktopServices.openUrl(QUrl(params.executable))
            self.stop()  # stop because it is not a subprocess
            return

        self.logger.info("Starting %s (%s)", self.rgame.app_title, self.rgame.app_name)
        self.logger.info("Command: %s, %s", params.executable, " ".join(params.arguments))
        self.logger.debug("Working directory %s", params.working_directory)

        if self.rgame.app_name in DETACHED_APP_NAMES and platform.system() == "Windows":
            if self.console:
                self.console.log(f"Launching {params.executable} as a detached process")
            subprocess.Popen(
                (params.executable, *params.arguments),
                stdin=None,
                stdout=None,
                stderr=None,
                cwd=params.working_directory,
                env=params.environment,
                shell=True,
                creationflags=subprocess.DETACHED_PROCESS,
            )
            self.stop()  # stop because we do not attach to the output
            return

        if platform.system() in {"Linux", "FreeBSD"}:
            cmd_line = get_rare_executable()
            executable, arguments = cmd_line[0], cmd_line[1:]

            if appid := os.environ.get("SteamGameId", False):
                params.environment["SteamGameId"] = appid
            elif params.environment.get("SteamGameId", False):
                appid = params.environment["SteamGameId"]

            self.game_process.setProgram(executable)
            # TODO: Add "SteamLauch" and "AppId=xxxxxx" here for steamdeck/gamescope
            try:
                appid = int(appid) >> 32
            except ValueError:
                pass
            self.game_process.setArguments(
                [*arguments, "subreaper", "SteamLaunch", f"AppId={appid}", "--", params.executable, *params.arguments]
            )
            self.game_process.setUnixProcessParameters(
                QProcess.UnixProcessFlag.ResetSignalHandlers | QProcess.UnixProcessFlag.CreateNewSession
            )
        else:
            self.game_process.setProgram(params.executable)
            self.game_process.setArguments(params.arguments)

        if params.working_directory:
            self.game_process.setWorkingDirectory(params.working_directory)

        if self.args.debug and self.console:
            self.console.log(str(self.game_process.program()))
            self.console.log(shlex.join(self.game_process.arguments()))

        self.game_process.setProcessEnvironment(dict_to_qprocenv(params.environment))
        # send start message after process started
        self.game_process.started.connect(
            lambda: self.send_message(
                StateChangedModel(
                    action=Actions.state_update,
                    app_name=self.rgame.app_name,
                    new_state=StateChangedModel.States.started,
                )
            )
        )
        self.game_process.start()

    def error_occurred(self, error_str: str):
        self.logger.warning(error_str)
        if self.console:
            self.console.on_process_exit(self.core.get_game(self.rgame.app_name).app_title, error_str)
        self.send_message(ErrorModel(error_string=error_str, app_name=self.rgame.app_name, action=Actions.error))
        self.stop()

    def start_prepare(self, sync_action=None):
        worker = PreLaunch(self.args, self.rgame, sync_action)
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
        self.sync_dialog = CloudSyncDialog(self.rgame.igame, dt_local, dt_remote)
        self.sync_dialog.result_ready.connect(self.__sync_ready)
        self.sync_dialog.open()

    @Slot(int)
    @Slot(CloudSyncDialogResult)
    def __sync_ready(self, action: CloudSyncDialogResult):
        if self.sync_dialog is not None:
            self.sync_dialog.deleteLater()
            self.sync_dialog = None
        action = CloudSyncDialogResult(action)
        if action == CloudSyncDialogResult.CANCEL:
            self.no_sync_on_exit = True
        if self.console:
            if action == CloudSyncDialogResult.DOWNLOAD:
                self.console.log("Downloading saves...")
            elif action == CloudSyncDialogResult.UPLOAD:
                self.console.log("Uploading saves...")
        self.start_prepare(action)

    def start(self):
        if not self.args.offline:
            try:
                if not self.core.login():
                    raise ValueError("You are not logged in")
            except ValueError:
                # automatically launch offline if available
                self.logger.error("Not logged in. Trying to launch the game in offline mode")
                self.args.offline = True

        if not self.args.offline and self.rgame.auto_sync_saves:
            self.logger.info("Start sync worker")
            worker = SyncCheckWorker(self.core, self.rgame)
            worker.signals.error_occurred.connect(self.error_occurred)
            worker.signals.sync_state_ready.connect(self.sync_ready)
            QThreadPool.globalInstance().start(worker)
        else:
            self.start_prepare()

    def stop(self, sig: int = signal.SIGINT):
        try:
            if self.console:
                self.game_process.readyReadStandardOutput.disconnect()
                self.game_process.readyReadStandardError.disconnect()
            if self.game_process.isSignalConnected(QMetaMethod.fromSignal(self.game_process.finished)):
                self.game_process.finished.disconnect()
            if self.game_process.isSignalConnected(QMetaMethod.fromSignal(self.game_process.errorOccurred)):
                self.game_process.errorOccurred.disconnect()
        except (TypeError, RuntimeError) as e:
            self.logger.error("Failed to disconnect process signals: %s", e)

        if shiboken6.isValid(self.game_process):  # pylint: disable=E1101
            if self.game_process.state() != QProcess.ProcessState.NotRunning:
                if sig == signal.SIGTERM:
                    self.__proc_term()
                elif sig == signal.SIGINT:
                    self.__proc_kill()
            self.game_process.waitForFinished()
            exit_code = self.game_process.exitCode()
            self.game_process.deleteLater()
        else:
            exit_code = 0

        self.logger.info("Stopping server %s", self.server.socketDescriptor())
        try:
            self.server.close()
            self.server.deleteLater()
        except RuntimeError as e:
            self.logger.error("Error occurred while stopping server: %s", e)

        self.processEvents()
        if not self.console:
            self.exit(exit_code)
        else:
            self.console.on_process_exit(self.rgame.app_title, exit_code)


def launcher(args: Namespace) -> int:
    args = InitParams.from_argparse(args)

    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = RareLauncher(args)
    app.setQuitOnLastWindowClosed(True)

    # This prevents ghost QLocalSockets, which block the name, which makes it unable to start
    # No handling for SIGKILL
    def signal_handler(sig, frame):
        app.logger.info("%s received. Stopping", signal.strsignal(sig))
        app.stop(sig)
        app.exit(1)
        return 1

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    if not app.success:
        app.stop(signal.SIGINT)
        app.exit(1)
        return 1

    try:
        exit_code = app.exec()
    except Exception as e:
        app.logger.error("Unhandled error %s", e)
        exit_code = 1
    finally:
        pass
        # if not sip.isdeleted(app.server):
        #     app.server.close()
    return exit_code


__all__ = ["launcher"]
