import sys
from datetime import datetime
from enum import IntEnum
from logging import getLogger

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QDialog
from legendary.core import LegendaryCore
from legendary.models.game import InstalledGame

from rare.ui.components.tabs.games.game_info.cloud_sync_widget import Ui_CloudSyncWidget
from rare.utils.misc import qta_icon
from rare.widgets.dialogs import ButtonDialog, game_title

logger = getLogger("CloudSyncDialog")


class CloudSyncDialogResult(IntEnum):
    DOWNLOAD = 2
    UPLOAD = 1
    CANCEL = 0
    SKIP = 3


class CloudSyncDialog(ButtonDialog):
    result_ready: Signal = Signal(CloudSyncDialogResult)

    def __init__(self, igame: InstalledGame, dt_local: datetime, dt_remote: datetime, parent=None):
        super(CloudSyncDialog, self).__init__(parent=parent)
        header = self.tr("Cloud saves for")
        self.setWindowTitle(game_title(header, igame.title))

        title_label = QLabel(f"<h4>{game_title(header, igame.title)}</h4>", self)

        sync_widget = QWidget(self)
        self.sync_ui = Ui_CloudSyncWidget()
        self.sync_ui.setupUi(sync_widget)

        layout = QVBoxLayout()
        layout.addWidget(title_label)
        layout.addWidget(sync_widget)

        self.accept_button.setText(self.tr("Skip"))
        self.accept_button.setIcon(qta_icon("fa.chevron-right"))

        self.setCentralLayout(layout)

        self.status = CloudSyncDialogResult.CANCEL

        newer = self.tr("Newer")
        if dt_remote and dt_local:
            self.sync_ui.age_label_local.setText(f"<b>{newer}</b>" if dt_remote < dt_local else " ")
            self.sync_ui.age_label_remote.setText(f"<b>{newer}</b>" if dt_remote > dt_local else " ")
        # Set status, if one of them is None
        elif dt_remote and not dt_local:
            self.status = CloudSyncDialogResult.DOWNLOAD
        elif not dt_remote and dt_local:
            self.status = CloudSyncDialogResult.UPLOAD
        else:
            self.status = CloudSyncDialogResult.SKIP

        local_tz = datetime.now().astimezone().tzinfo
        self.sync_ui.date_info_local.setText(
            dt_local.astimezone(local_tz).strftime("%A, %d %B %Y %X") if dt_local else "None")
        self.sync_ui.date_info_remote.setText(
            dt_remote.astimezone(local_tz).strftime("%A, %d %B %Y %X") if dt_remote else "None")

        self.sync_ui.icon_local.setPixmap(qta_icon("mdi.harddisk", "fa.desktop").pixmap(128, 128))
        self.sync_ui.icon_remote.setPixmap(qta_icon("mdi.cloud-outline", "ei.cloud").pixmap(128, 128))

        self.sync_ui.upload_button.clicked.connect(self.__on_upload)
        self.sync_ui.download_button.clicked.connect(self.__on_download)

        if self.status == CloudSyncDialogResult.SKIP:
            self.accept()

    def __on_upload(self):
        self.status = CloudSyncDialogResult.UPLOAD
        self.done(QDialog.DialogCode.Accepted)

    def __on_download(self):
        self.status = CloudSyncDialogResult.DOWNLOAD
        self.done(QDialog.DialogCode.Accepted)

    def done_handler(self):
        self.result_ready.emit(self.status)

    def accept_handler(self):
        self.status = CloudSyncDialogResult.SKIP

    def reject_handler(self):
        self.status = CloudSyncDialogResult.CANCEL


if __name__ == "__main__":
    app = QApplication(sys.argv)
    core = LegendaryCore()

    @Slot(int)
    def __callback(status: int):
        print(repr(CloudSyncDialogResult(status)))

    dlg = CloudSyncDialog(core.get_installed_list()[0], datetime.now(), datetime.strptime("2021,1", "%Y,%M"))
    dlg.result_ready.connect(__callback)
    dlg.open()
    app.exec()
