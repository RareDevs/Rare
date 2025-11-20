from enum import Enum

from PySide6.QtCore import QObject, Signal

from rare.models.base_game import RareGameSlim

from .worker import QueueWorker, QueueWorkerInfo


class CloudSyncWorkerSignals(QObject):
    progress = Signal(RareGameSlim, int, int, float, float)
    result = Signal(RareGameSlim, bool, int, int)
    error = Signal(RareGameSlim, str)


class CloudSyncWorker(QueueWorker):
    class Mode(Enum):
        UPLOAD = 1
        DOWNLOAD = 2

    def __init__(self, rgame: RareGameSlim, mode: Mode):
        super(CloudSyncWorker, self).__init__()
        self.signals = CloudSyncWorkerSignals()

        self.rgame: RareGameSlim = rgame
        self.mode: CloudSyncWorker.Mode = mode

        # set RareGame's state as soon as the worker is instantiated to avoid conflicts
        # self.rgame.state = RareGameSlim.State.SYNCING

    def worker_info(self) -> QueueWorkerInfo:
        return QueueWorkerInfo(
            app_name=self.rgame.app_name,
            app_title=self.rgame.app_title,
            type=type(self).__name__,
            prefix="Syncing",
            state=self.state,
        )

    def run_real(self):
        if self.mode == CloudSyncWorker.Mode.UPLOAD:
            self.rgame.upload_saves()
        if self.mode == CloudSyncWorker.Mode.DOWNLOAD:
            self.rgame.download_saves()
        self.rgame.state = RareGameSlim.State.IDLE
