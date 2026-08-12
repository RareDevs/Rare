# from logging import getLogger
from datetime import datetime

from legendary.models.game import SaveGameStatus
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from rare.utils.misc import qta_icon


class CloudSyncItemWidget(QGroupBox):
    button_clicked = Signal()

    def __init__(self, title: str, icon: QPixmap, text: str, parent=None):
        super(CloudSyncItemWidget, self).__init__(title, parent=parent)
        # self.logger = getLogger(type(self).__name__)

        self.date_label = QLabel(self)
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label = QLabel(self)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setPixmap(icon)
        self.age_label = QLabel(self)
        self.age_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.button = QPushButton(text, self)
        self.button.clicked.connect(self.button_clicked)

        layout = QVBoxLayout(self)
        layout.addWidget(self.date_label)
        layout.addWidget(self.icon_label)
        layout.addWidget(self.age_label)
        layout.addWidget(self.button)


class CloudSyncWidget(QWidget):
    upload_clicked = Signal()
    download_clicked = Signal()

    def __init__(self, parent=None):
        super(CloudSyncWidget, self).__init__(parent=parent)
        # self.logger = getLogger(type(self).__name__)

        self.local = CloudSyncItemWidget(
            self.tr('Local'),
            qta_icon('mdi.harddisk', 'fa5s.desktop').pixmap(128, 128),
            self.tr('Upload'),
        )
        self.local.button_clicked.connect(self.upload_clicked)

        self.remote = CloudSyncItemWidget(
            self.tr('Remote'),
            qta_icon('mdi.cloud-outline', 'fa5s.cloud').pixmap(128, 128),
            self.tr('Download'),
        )
        self.remote.button_clicked.connect(self.download_clicked)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.local, stretch=2)
        layout.addWidget(self.remote, stretch=2)

    def update_widget(self, status: SaveGameStatus, dt_local: datetime | None, dt_remote: datetime | None):
        local_tz = datetime.now().astimezone().tzinfo
        self.local.date_label.setText(
            dt_local.astimezone(local_tz).strftime('%A, %d %B %Y %X') if dt_local else 'None'
        )
        self.remote.date_label.setText(
            dt_remote.astimezone(local_tz).strftime('%A, %d %B %Y %X') if dt_remote else 'None'
        )

        newer = self.tr('Newer')
        self.local.age_label.setText(f'<b>{newer}</b>' if status == SaveGameStatus.LOCAL_NEWER else ' ')
        self.remote.age_label.setText(f'<b>{newer}</b>' if status == SaveGameStatus.REMOTE_NEWER else ' ')

        self.local.button.setDisabled(not dt_local)
        self.remote.button.setDisabled(not dt_remote)
