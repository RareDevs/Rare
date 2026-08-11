# from logging import getLogger

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QResizeEvent
from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from rare.utils.misc import qta_icon


class CloudSyncItemWidget(QGroupBox):
    buttonClicked = Signal()

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
        self.button.clicked.connect(self.buttonClicked)

        layout = QVBoxLayout(self)
        layout.addWidget(self.date_label)
        layout.addWidget(self.icon_label)
        layout.addWidget(self.age_label)
        layout.addWidget(self.button)


class CloudSyncWidget(QWidget):
    uploadClicked = Signal()
    downloadClicked = Signal()

    def __init__(self, parent=None):
        super(CloudSyncWidget, self).__init__(parent=parent)
        # self.logger = getLogger(type(self).__name__)

        self.local = CloudSyncItemWidget(
            self.tr('Local'),
            qta_icon('mdi.harddisk', 'fa5s.desktop').pixmap(128, 128),
            self.tr('Upload'),
        )
        self.local.buttonClicked.connect(self.uploadClicked)

        self.remote = CloudSyncItemWidget(
            self.tr('Remote'),
            qta_icon('mdi.cloud-outline', 'fa5s.cloud').pixmap(128, 128),
            self.tr('Download'),
        )
        self.remote.buttonClicked.connect(self.downloadClicked)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.local, stretch=2)
        layout.addWidget(self.remote, stretch=2)
