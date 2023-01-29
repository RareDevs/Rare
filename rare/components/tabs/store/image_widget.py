from typing import Dict

from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import (
    QPixmap,
    QImage, QMovie,
)
from PyQt5.QtWidgets import QLabel

from rare.utils.qt_requests import QtRequestManager
from rare.widgets.image_widget import ImageWidget


class WaitingSpinner(QLabel):
    def __init__(self, autostart=False, parent=None):
        super(WaitingSpinner, self).__init__(parent=parent)
        self.setObjectName(type(self).__name__)
        self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.movie = QMovie(":/images/loader.gif")
        self.setMovie(self.movie)
        if autostart:
            self.movie.start()

    def setGeometry(self, a0: QRect) -> None:
        self.rect().moveCenter(self.parent().rect().center())
        super(WaitingSpinner, self).setGeometry(self.rect())

    def start(self):
        self.movie.start()

    def stop(self):
        self.movie.stop()


class ShopImageWidget(ImageWidget):
    __image_cache: Dict[str, Dict[str, QPixmap]] = {}

    def __init__(self, parent=None):
        super(ShopImageWidget, self).__init__(parent=parent)
        self.spinner = WaitingSpinner(parent=self)
        self.spinner.setVisible(False)
        self.manager = QtRequestManager("bytes")
        self.app_id = ""
        self.orientation = ""

    def fetchPixmap(self, url, app_id: str, title: str = ""):
        self.setPixmap(QPixmap())
        self.app_id = app_id
        if self._image_size.size.width() > self._image_size.size.height():
            self.orientation = "wide"
        else:
            self.orientation = "tall"

        if ShopImageWidget.__image_cache.get(self.app_id, None) is not None:
            if pixmap := ShopImageWidget.__image_cache[self.app_id].get(self.orientation, None):
                self.setPixmap(pixmap)
                return
        self.spinner.setFixedSize(self._image_size.size)
        self.spinner.setVisible(True)
        self.spinner.start()
        self.manager.get(
            url, self.__on_image_ready, payload={
                "resize": 1, "w": self._image_size.size.width(), "h": self._image_size.size.height()
            }
        )

    def __on_image_ready(self, data):
        cover = QImage()
        cover.loadFromData(data)
        cover = cover.scaled(self._image_size.size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        cover = cover.convertToFormat(QImage.Format_ARGB32_Premultiplied)
        cover = QPixmap(cover)
        ShopImageWidget.__image_cache.update({self.app_id: {self.orientation: cover}})
        super(ShopImageWidget, self).setPixmap(cover)
        self.spinner.stop()
        self.spinner.setVisible(False)
