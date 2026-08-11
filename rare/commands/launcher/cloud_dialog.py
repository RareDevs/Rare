import sys
from datetime import datetime, timezone
from enum import IntEnum
from logging import getLogger

from legendary.models.game import InstalledGame, SaveGameStatus
from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QApplication, QDialog, QLabel, QVBoxLayout

from rare.lgndr.core import LegendaryCore
from rare.utils.misc import qta_icon
from rare.widgets.cloudsync_widget import CloudSyncWidget
from rare.widgets.dialogs import ButtonDialog, game_title

logger = getLogger('CloudSyncDialog')


class CloudSyncDialogResult(IntEnum):
    DOWNLOAD = 2
    UPLOAD = 1
    CANCEL = 0
    SKIP = 3


class CloudSyncDialog(ButtonDialog):
    result_ready: Signal = Signal(CloudSyncDialogResult)

    def __init__(self, igame: InstalledGame, status: SaveGameStatus, dt_local: datetime | None, dt_remote: datetime | None, parent=None):
        super(CloudSyncDialog, self).__init__(parent=parent)
        header = self.tr('Cloud saves for')
        self.setWindowTitle(game_title(header, igame.title))

        title_label = QLabel(f'<h4>{game_title(header, igame.title)}</h4>', self)

        sync_widget = CloudSyncWidget(self)
        sync_widget.update_widget(status, dt_local, dt_remote)
        sync_widget.uploadClicked.connect(self._on_upload)
        sync_widget.downloadClicked.connect(self._on_download)

        min_width = max(sync_widget.local.minimumSizeHint().width(), sync_widget.remote.minimumSizeHint().width())
        sync_widget.local.setMinimumWidth(min_width)
        sync_widget.remote.setMinimumWidth(min_width)

        layout = QVBoxLayout()
        layout.addWidget(title_label)
        layout.addWidget(sync_widget)

        self.accept_button.setText(self.tr('Skip'))
        self.accept_button.setIcon(qta_icon('fa.chevron-right', 'fa5s.chevron-right'))

        self.setCentralLayout(layout)

        self.status = CloudSyncDialogResult.CANCEL

        if dt_remote and dt_local:
            pass
        # Set status, if one of them is None
        elif dt_remote and not dt_local:
            self.status = CloudSyncDialogResult.DOWNLOAD
        elif not dt_remote and dt_local:
            self.status = CloudSyncDialogResult.UPLOAD
        else:
            self.status = CloudSyncDialogResult.SKIP

        if self.status == CloudSyncDialogResult.SKIP:
            self.accept()

    def _on_upload(self):
        self.status = CloudSyncDialogResult.UPLOAD
        self.done(QDialog.DialogCode.Accepted)

    def _on_download(self):
        self.status = CloudSyncDialogResult.DOWNLOAD
        self.done(QDialog.DialogCode.Accepted)

    def done_handler(self):
        self.result_ready.emit(self.status)

    def accept_handler(self):
        self.status = CloudSyncDialogResult.SKIP

    def reject_handler(self):
        self.status = CloudSyncDialogResult.CANCEL


if __name__ == '__main__':
    app = QApplication(sys.argv)
    core = LegendaryCore()

    @Slot(int)
    def __callback(status: int):
        print(repr(CloudSyncDialogResult(status)))

    dlg = CloudSyncDialog(
        core.get_installed_list()[0],
        SaveGameStatus.LOCAL_NEWER,
        datetime.now(tz=timezone.utc),
        datetime.strptime('2021,1', '%Y,%M').replace(tzinfo=timezone.utc)
    )
    dlg.result_ready.connect(__callback)
    dlg.open()
    app.exec()
