from legendary.lfs.eos import EOSOverlayApp
from legendary.models.downloading import ConditionCheckResult
from PySide6.QtCore import QObject, Signal

from rare.lgndr.cli import LegendaryCLI
from rare.lgndr.core import LegendaryCore
from rare.lgndr.glue.arguments import LgndrInstallGameArgs
from rare.lgndr.glue.exception import LgndrException
from rare.lgndr.glue.monkeys import LgndrIndirectStatus
from rare.models.game import RareEosOverlay, RareGame
from rare.models.install import InstallDownloadModel, InstallOptionsModel

from .worker import Worker


class InstallWorkerSignals(QObject):
    failed = Signal(str)
    finished = Signal()


class InstallDataWorkerSignals(InstallWorkerSignals):
    result = Signal(dict, list)


class InstallPrepareWorkerSignals(InstallWorkerSignals):
    result = Signal(InstallDownloadModel)


class InstallDataWorker(Worker):
    def __init__(self, rgame: RareEosOverlay | RareGame):
        super(InstallDataWorker, self).__init__()
        self.signals = InstallDataWorkerSignals()
        self.rgame = rgame

    def run_real(self):
        try:
            sdl_data = {}
            for platform in self.rgame.platforms:
                sdl_data[platform] = self.rgame.sdl_data(platform)
            pending_eulas = self.rgame.pending_eulas()

            # TODO: there is information about the files to be downloaded in analres, don't fetch the manifest again
            # TODO: see if you can re-use the one from selective downloads
            # new_manifest_data, _, _ = self.core.get_cdn_manifest(download.game, download.igame.platform, self._options.disable_https)
            # new_manifest = self.core.load_manifest(new_manifest_data)
            # self.file_filters.clear()
            # for e in new_manifest.file_manifest_list.elements:
            #     self.file_filters.add_item(e.filename.lower())

            self.signals.result.emit(sdl_data, pending_eulas)
        except Exception as e:  # noqa: BLE001
            self.signals.failed.emit(str(e))
        self.signals.finished.emit()


class InstallPrepareWorker(Worker):
    def __init__(self, core: LegendaryCore, options: InstallOptionsModel):
        super(InstallPrepareWorker, self).__init__()
        self.signals: InstallPrepareWorkerSignals = InstallPrepareWorkerSignals()
        self.core = core
        self.options = options

    def run_real(self):
        try:
            if not self.options.overlay:
                cli = LegendaryCLI(self.core)
                status = LgndrIndirectStatus()
                result = cli.install_game(LgndrInstallGameArgs(**self.options.as_install_kwargs(), indirect_status=status))
                if result:
                    download = InstallDownloadModel(*result)
                else:
                    raise LgndrException(status.message)
            else:
                dlm, analysis, igame = self.core.prepare_overlay_install(path=self.options.base_path)

                download = InstallDownloadModel(
                    dlm=dlm,
                    analysis=analysis,
                    igame=igame,
                    game=EOSOverlayApp,
                    repair=False,
                    repair_file='',
                    res=ConditionCheckResult(),  # empty
                )

            if not download.res or not download.res.failures:
                self.signals.result.emit(download)
            else:
                # self.signals.failed.emit("\n".join(str(i) for i in download.res.failures))
                self.signals.failed.emit('\n'.join(map(str, download.res.failures)))
        except LgndrException as ret:
            self.signals.failed.emit(ret.message)
        except Exception as e:  # noqa: BLE001
            self.signals.failed.emit(str(e))
        self.signals.finished.emit()
