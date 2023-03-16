import os
from argparse import Namespace
from logging import getLogger

from PyQt5.QtCore import pyqtSignal, QObject

from rare.lgndr.cli import LegendaryCLI
from rare.lgndr.core import LegendaryCore
from rare.lgndr.glue.arguments import LgndrVerifyGameArgs
from rare.lgndr.glue.monkeys import LgndrIndirectStatus
from rare.models.game import RareGame
from .worker import QueueWorker, QueueWorkerInfo

logger = getLogger("VerifyWorker")


class VerifyWorker(QueueWorker):
    class Signals(QObject):
        progress = pyqtSignal(RareGame, int, int, float, float)
        result = pyqtSignal(RareGame, bool, int, int)
        error = pyqtSignal(RareGame, str)

    # num: int = 0
    # total: int = 1  # set default to 1 to avoid DivisionByZero before it is initialized

    def __init__(self, core: LegendaryCore, args: Namespace, rgame: RareGame):
        super(VerifyWorker, self).__init__()
        self.signals = VerifyWorker.Signals()
        self.core = core
        self.args = args
        self.rgame = rgame

    def status_callback(self, num: int, total: int, percentage: float, speed: float):
        self.rgame.signals.progress.update.emit(num * 100 // total)
        self.signals.progress.emit(self.rgame, num, total, percentage, speed)

    def worker_info(self) -> QueueWorkerInfo:
        return QueueWorkerInfo(
            app_name=self.rgame.app_name, app_title=self.rgame.app_title, worker_type="Verify", state=self.state
        )

    def run_real(self):
        self.rgame.signals.progress.start.emit()

        cli = LegendaryCLI(self.core)
        status = LgndrIndirectStatus()
        args = LgndrVerifyGameArgs(
            app_name=self.rgame.app_name, indirect_status=status, verify_stdout=self.status_callback
        )

        # lk: first pass, verify with the current manifest
        repair_mode = False
        result = cli.verify_game(
            args, print_command=False, repair_mode=repair_mode, repair_online=not self.args.offline
        )
        if result is None:
            # lk: second pass with downloading the latest manifest
            # lk: this happens if the manifest was not found and repair_mode was not requested
            # lk: we already have checked if the directory exists before starting the worker
            try:
                # lk: this try-except block handles the exception caused by a missing manifest
                # lk: and is raised only in the case we are offline
                repair_mode = True
                result = cli.verify_game(
                    args, print_command=False, repair_mode=repair_mode, repair_online=not self.args.offline
                )
                if result is None:
                    raise ValueError
            except ValueError:
                self.rgame.signals.progress.finish.emit(True)
                self.signals.error.emit(self.rgame, status.message)
                return

        success = result is not None and not any(result)
        if success:
            # lk: if verification was successful we delete the repair file and run the clean procedure
            # lk: this could probably be cut down to what is relevant for this use-case and skip the `cli` call
            repair_file = os.path.join(self.core.lgd.get_tmp_path(), f"{self.rgame.app_name}.repair")
            cli.install_game_cleanup(
                game=self.rgame.game, igame=self.rgame.igame, repair_mode=True, repair_file=repair_file
            )
            self.rgame.needs_verification = False
            self.rgame.update_rgame()

        self.rgame.signals.progress.finish.emit(False)
        self.signals.result.emit(self.rgame, success, *result)
