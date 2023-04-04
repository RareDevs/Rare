from PyQt5.QtCore import QEvent, QObject
from PyQt5.QtCore import Qt
from PyQt5.QtGui import (
    QPixmap,
    QImage,
    QMovie,
    QShowEvent,
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
        self.movie = QMovie(":/images/loader.gif", parent=self)
        self.setFixedSize(128, 128)
        self.setMovie(self.movie)
        if self.parent() is not None:
            self.parent().installEventFilter(self)
        if autostart:
            self.movie.start()

    def __center_on_parent(self):
        rect = self.rect()
        rect.moveCenter(self.parent().contentsRect().center())
        self.setGeometry(rect)

    def event(self, e: QEvent) -> bool:
        if e.type() == QEvent.ParentAboutToChange:
            if self.parent() is not None:
                self.parent().removeEventFilter(self)
        if e.type() == QEvent.ParentChange:
            if self.parent() is not None:
                self.parent().installEventFilter(self)
        return super().event(e)

    def showEvent(self, a0: QShowEvent) -> None:
        self.__center_on_parent()

    def eventFilter(self, a0: QObject, a1: QEvent) -> bool:
        if a0 is self.parent() and a1.type() == QEvent.Resize:
            self.__center_on_parent()
            return a0.event(a1)
        return False

    def start(self):
        self.setVisible(True)
        self.movie.start()

    def stop(self):
        self.setVisible(False)
        self.movie.stop()


class IconWidget(object):
    def __init__(self):
        self.mini_widget: QWidget = None
        self.title_label: QLabel = None
        self.developer_label: QLabel = None
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
        self.title_label.setAlignment(Qt.AlignTop)
        self.title_label.setAutoFillBackground(False)
        self.title_label.setWordWrap(True)

        # information below title
        self.developer_label = QLabel(parent=self.mini_widget)
        self.developer_label.setObjectName(f"{type(self).__name__}TooltipLabel")
        self.developer_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.developer_label.setAutoFillBackground(False)

        self.price_label = QLabel(parent=self.mini_widget)
        self.price_label.setObjectName(f"{type(self).__name__}TooltipLabel")
        self.price_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.price_label.setAutoFillBackground(False)

        self.discount_label = QLabel(parent=self.mini_widget)
        self.discount_label.setObjectName(f"{type(self).__name__}TooltipLabel")
        self.discount_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
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
        row_layout.addWidget(self.developer_label, stretch=2)
        row_layout.addWidget(self.price_label)
        row_layout.addWidget(self.discount_label)
        mini_layout.addWidget(self.title_label)
        mini_layout.addLayout(row_layout)
        self.mini_widget.setLayout(mini_layout)

        image_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding))
        image_layout.addWidget(self.mini_widget)
        widget.setLayout(image_layout)


class ShopImageWidget(ImageWidget):
    def __init__(self, manager: QtRequestManager, parent=None):
        super(ShopImageWidget, self).__init__(parent=parent)
        self.ui = IconWidget()
        self.spinner = WaitingSpinner(parent=self)
        self.spinner.setVisible(False)
        self.manager = manager

    def fetchPixmap(self, url):
        self.setPixmap(QPixmap())
        self.spinner.setFixedSize(self._image_size.size)
        self.spinner.start()
        self.manager.get(url, self.__on_image_ready, params={
            "resize": 1,
            "w": self._image_size.base.size.width(),
            "h": self._image_size.base.size.height(),
        })

    def __on_image_ready(self, data):
        cover = QImage()
        cover.loadFromData(data)
        # cover = cover.scaled(self._image_size.size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        cover.setDevicePixelRatio(self._image_size.base.pixel_ratio)
        cover = cover.convertToFormat(QImage.Format_ARGB32_Premultiplied)
        cover = QPixmap(cover)
        self.setPixmap(cover)
        self.spinner.stop()
