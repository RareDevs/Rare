import os
from logging import getLogger

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QMovie
from PyQt5.QtWidgets import (
    QStyle,
    QLabel,
    QHBoxLayout,
    QWidget,
    QPushButton,
    QLineEdit,
    QToolButton,
)

from rare.utils.misc import icon as qta_icon
from rare.utils.paths import tmp_dir
from rare.utils.qt_requests import QtRequestManager

logger = getLogger("ExtraWidgets")


class WaitingSpinner(QLabel):
    def __init__(self, parent=None):
        super(WaitingSpinner, self).__init__(parent=parent)
        self.setObjectName(type(self).__name__)
        self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.movie = QMovie(":/images/loader.gif")
        self.setMovie(self.movie)
        self.movie.start()


class SelectViewWidget(QWidget):
    toggled = pyqtSignal()

    def __init__(self, icon_view: bool, parent=None):
        super(SelectViewWidget, self).__init__(parent=parent)
        self.icon_view = icon_view
        self.icon_button = QPushButton(self)
        self.icon_button.setObjectName(f"{type(self).__name__}Button")
        self.list_button = QPushButton(self)
        self.list_button.setObjectName(f"{type(self).__name__}Button")

        if icon_view:
            self.icon_button.setIcon(qta_icon("mdi.view-grid-outline", "ei.th-large", color="orange"))
            self.list_button.setIcon(qta_icon("fa5s.list", "ei.th-list"))
        else:
            self.icon_button.setIcon(qta_icon("mdi.view-grid-outline", "ei.th-large"))
            self.list_button.setIcon(qta_icon("fa5s.list", "ei.th-list", color="orange"))

        self.icon_button.clicked.connect(self.icon)
        self.list_button.clicked.connect(self.list)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.icon_button)
        layout.addWidget(self.list_button)

        self.setLayout(layout)

    def isChecked(self):
        return self.icon_view

    def icon(self):
        self.icon_button.setIcon(qta_icon("mdi.view-grid-outline", "ei.th-large", color="orange"))
        self.list_button.setIcon(qta_icon("fa5s.list", "ei.th-list"))
        self.icon_view = False
        self.toggled.emit()

    def list(self):
        self.icon_button.setIcon(qta_icon("mdi.view-grid-outline", "ei.th-large"))
        self.list_button.setIcon(qta_icon("fa5s.list", "ei.th-list", color="orange"))
        self.icon_view = True
        self.toggled.emit()


class ImageLabel(QLabel):
    image = None
    img_size = None
    name = ""

    def __init__(self, parent=None):
        super(ImageLabel, self).__init__(parent=parent)
        self.path = tmp_dir()
        self.manager = QtRequestManager("bytes")

    def update_image(self, url, name="", size: tuple = (240, 320)):
        self.setFixedSize(*size)
        self.img_size = size
        self.name = name
        for c in r'<>?":|\/* ':
            self.name = self.name.replace(c, "")
        if self.img_size[0] > self.img_size[1]:
            name_extension = "wide"
        else:
            name_extension = "tall"
        self.name = f"{self.name}_{name_extension}.png"
        if not os.path.exists(os.path.join(self.path, self.name)):
            self.manager.get(url, self.image_ready)
            # self.request.finished.connect(self.image_ready)
        else:
            self.show_image()

    def image_ready(self, data):
        try:
            self.setPixmap(QPixmap())
        except Exception:
            logger.warning("C++ object already removed, when image ready")
            return
        image = QImage()
        image.loadFromData(data)
        image = image.scaled(
            *self.img_size[:2],
            Qt.KeepAspectRatio,
            transformMode=Qt.SmoothTransformation,
        )

        image.save(os.path.join(self.path, self.name))

        pixmap = QPixmap().fromImage(image)
        self.setPixmap(pixmap)

    def show_image(self):
        self.image = QPixmap(os.path.join(self.path, self.name)).scaled(
            *self.img_size, transformMode=Qt.SmoothTransformation
        )
        self.setPixmap(self.image)


class ButtonLineEdit(QLineEdit):
    buttonClicked = pyqtSignal()

    def __init__(self, icon_name, placeholder_text: str, parent=None):
        super(ButtonLineEdit, self).__init__(parent=parent)
        self.setObjectName(type(self).__name__)

        self.button = QToolButton(self)
        self.button.setObjectName(f"{type(self).__name__}Button")
        self.button.setIcon(qta_icon(icon_name, color="white"))
        self.button.setStyleSheet(
            f"QToolButton#{self.button.objectName()} {{border: 0px; padding: 0px;}}"
        )
        self.button.setCursor(Qt.ArrowCursor)
        self.button.clicked.connect(self.buttonClicked.emit)
        self.setPlaceholderText(placeholder_text)
        frame_width = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth)
        button_size = self.button.sizeHint()

        self.setStyleSheet(
            f"QLineEdit#{self.objectName()} {{padding-right: {(button_size.width() + frame_width + 1)}px; }}"
        )
        self.setMinimumSize(
            max(self.minimumSizeHint().width(), button_size.width() + frame_width * 2 + 2),
            max(
                self.minimumSizeHint().height(),
                button_size.height() + frame_width * 2 + 2,
            ),
        )

    def resizeEvent(self, event):
        frame_width = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth)
        button_size = self.button.sizeHint()
        self.button.move(
            self.rect().right() - frame_width - button_size.width(),
            (self.rect().bottom() - button_size.height() + 1) // 2,
        )
        super(ButtonLineEdit, self).resizeEvent(event)
