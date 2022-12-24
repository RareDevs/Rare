import os
from logging import getLogger

from PyQt5.QtCore import pyqtSignal, QObject, QRunnable

from rare.lgndr.cli import LegendaryCLI
from rare.lgndr.glue.arguments import LgndrVerifyGameArgs
from rare.lgndr.glue.monkeys import LgndrIndirectStatus
from rare.shared import LegendaryCoreSingleton, ArgumentsSingleton

logger = getLogger("VerificationWorker")


class VerifyWorker(QRunnable):
    class Signals(QObject):
        status = pyqtSignal(str, int, int, float, float)
        result = pyqtSignal(str, bool, int, int)
        error = pyqtSignal(str, str)

    num: int = 0
    total: int = 1  # set default to 1 to avoid DivisionByZero before it is initialized

    def __init__(self, app_name):
        super(VerifyWorker, self).__init__()
        self.signals = VerifyWorker.Signals()
        self.setAutoDelete(True)
        self.core = LegendaryCoreSingleton()
        self.args = ArgumentsSingleton()
        self.app_name = app_name

    def status_callback(self, num: int, total: int, percentage: float, speed: float):
        self.signals.status.emit(self.app_name, num, total, percentage, speed)

    def run(self):
        cli = LegendaryCLI(self.core)
        status = LgndrIndirectStatus()
        args = LgndrVerifyGameArgs(
            app_name=self.app_name, indirect_status=status, verify_stdout=self.status_callback
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
                self.signals.error.emit(self.app_name, status.message)
                return

        success = result is not None and not any(result)
        if success:
            # lk: if verification was successful we delete the repair file and run the clean procedure
            # lk: this could probably be cut down to what is relevant for this use-case and skip the `cli` call
            igame = self.core.get_installed_game(self.app_name)
            game = self.core.get_game(self.app_name, platform=igame.platform)
            repair_file = os.path.join(self.core.lgd.get_tmp_path(), f"{self.app_name}.repair")
            cli.install_game_cleanup(game=game, igame=igame, repair_mode=True, repair_file=repair_file)

        self.signals.result.emit(self.app_name, success, *result)
