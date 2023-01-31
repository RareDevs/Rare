import os
from logging import getLogger

from PyQt5.QtCore import QObject, pyqtSignal
from legendary.lfs.eos import EOSOverlayApp
from legendary.models.downloading import ConditionCheckResult

from rare.lgndr.cli import LegendaryCLI
from rare.lgndr.core import LegendaryCore
from rare.lgndr.glue.arguments import LgndrInstallGameArgs
from rare.lgndr.glue.exception import LgndrException
from rare.lgndr.glue.monkeys import LgndrIndirectStatus
from rare.models.install import InstallDownloadModel, InstallOptionsModel
from .worker import Worker

logger = getLogger("InstallInfoWorker")


class InstallInfoWorker(Worker):
    class Signals(QObject):
        result = pyqtSignal(InstallDownloadModel)
        failed = pyqtSignal(str)
        finished = pyqtSignal()

    def __init__(self, core: LegendaryCore, options: InstallOptionsModel):
        super(InstallInfoWorker, self).__init__()
        self.signals = InstallInfoWorker.Signals()
        self.core = core
        self.options = options

    def run_real(self):
        try:
            if not self.options.overlay:
                cli = LegendaryCLI(self.core)
                status = LgndrIndirectStatus()
                result = cli.install_game(
                    LgndrInstallGameArgs(**self.options.as_install_kwargs(), indirect_status=status)
                )
                if result:
                    download = InstallDownloadModel(*result)
                else:
                    raise LgndrException(status.message)
            else:
                if not os.path.exists(path := self.options.base_path):
                    os.makedirs(path)

                dlm, analysis, igame = self.core.prepare_overlay_install(
                    path=self.options.base_path
                )

                download = InstallDownloadModel(
                    dlm=dlm,
                    analysis=analysis,
                    igame=igame,
                    game=EOSOverlayApp,
                    repair=False,
                    repair_file="",
                    res=ConditionCheckResult(),  # empty
                )

            if not download.res or not download.res.failures:
                self.signals.result.emit(download)
            else:
                self.signals.failed.emit("\n".join(str(i) for i in download.res.failures))
        except LgndrException as ret:
            self.signals.failed.emit(ret.message)
        except Exception as e:
            self.signals.failed.emit(str(e))
        self.signals.finished.emit()
