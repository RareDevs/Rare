import datetime
from dataclasses import dataclass
from logging import getLogger

from PyQt5.QtCore import QObject, pyqtSignal, QRunnable

from legendary.models.game import SaveGameFile
from rare import shared

logger = getLogger("Cloud Save Utils")


@dataclass
class UploadModel:
    app_name: str
    date_time: datetime.datetime
    path: str


@dataclass
class DownloadModel:
    app_name: str
    latest_save: SaveGameFile
    path: str


class WorkerSignals(QObject):
    error_message = pyqtSignal(str)


class UploadWorker(QRunnable):
    signals = WorkerSignals()

    def __init__(self, upload_model: UploadModel):
        super(UploadWorker, self).__init__()

        self.model: UploadModel = upload_model
        self.setAutoDelete(True)

    def run(self) -> None:
        try:
            shared.core.upload_save(self.model.app_name, self.model.path, self.model.date_time)
        except Exception as e:
            self.signals.error_message.emit(str(e))
            logger.error(str(e))
            return
        self.signals.error_message.emit("")


class DownloadWorker(QRunnable):
    signals = WorkerSignals()

    def __init__(self, dl_model: DownloadModel):
        super(DownloadWorker, self).__init__()

        self.model: dl_model = dl_model
        self.setAutoDelete(True)

    def run(self) -> None:
        try:
            shared.core.download_saves(self.model.app_name, self.model.latest_save.manifest_name, self.model.path)
        except Exception as e:
            self.signals.error_message.emit(str(e))
            logger.error(str(e))
            return
        self.signals.error_message.emit("")
