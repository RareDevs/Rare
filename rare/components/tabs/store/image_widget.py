from typing import Dict

from PyQt5.QtCore import QRect
from PyQt5.QtCore import Qt
from PyQt5.QtGui import (
    QPixmap,
    QImage, QMovie,
)
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QSpacerItem,
    QSizePolicy,
    QHBoxLayout,
    QLabel,
)

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


class IconWidget(object):
    def __init__(self):
        self.mini_widget: QWidget = None
        self.title_label: QLabel = None
        self.price_label: QLabel = None
        self.discount_label: QLabel = None

    def setupUi(self, widget: QWidget):
        # on-hover popup
        self.mini_widget = QWidget(parent=widget)
        self.mini_widget.setObjectName(f"{type(self).__name__}MiniWidget")
        self.mini_widget.setFixedHeight(widget.height() // 4)

        # game title
        self.title_label = QLabel(parent=self.mini_widget)
        self.title_label.setObjectName(f"{type(self).__name__}TitleLabel")
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.title_label.setAlignment(Qt.AlignVCenter)
        self.title_label.setAutoFillBackground(False)
        self.title_label.setWordWrap(True)

        # information below title
        self.price_label = QLabel(parent=self.mini_widget)
        self.price_label.setObjectName(f"{type(self).__name__}TooltipLabel")
        self.price_label.setAlignment(Qt.AlignRight)
        self.price_label.setAutoFillBackground(False)

        self.discount_label = QLabel(parent=self.mini_widget)
        self.discount_label.setObjectName(f"{type(self).__name__}TooltipLabel")
        self.discount_label.setAlignment(Qt.AlignRight)
        self.discount_label.setAutoFillBackground(False)

        # Create layouts
        # layout on top of the image, holds the status label, a spacer item and the mini widget
        image_layout = QVBoxLayout()
        image_layout.setContentsMargins(2, 2, 2, 2)

        # layout for the mini widget, holds the top row and the info label
        mini_layout = QVBoxLayout()
        mini_layout.setSpacing(0)

        # layout for the top row, holds the title and the launch button
        row_layout = QHBoxLayout()
        row_layout.setSpacing(6)
        row_layout.setAlignment(Qt.AlignBottom)

        # Layout the widgets
        # (from inner to outer)
        row_layout.addWidget(self.price_label, stretch=2)
        row_layout.addWidget(self.discount_label)
        mini_layout.addWidget(self.title_label)
        mini_layout.addLayout(row_layout)
        self.mini_widget.setLayout(mini_layout)

        image_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding))
        image_layout.addWidget(self.mini_widget)
        widget.setLayout(image_layout)


class ShopImageWidget(ImageWidget):
    __image_cache: Dict[str, Dict[str, QPixmap]] = {}

    def __init__(self, parent=None):
        super(ShopImageWidget, self).__init__(parent=parent)
        self.ui = IconWidget()
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
