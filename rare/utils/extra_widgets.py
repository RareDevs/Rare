import os
from logging import getLogger

from PyQt5.QtCore import (
    Qt,
    QRect,
    QSize,
    QPoint,
    pyqtSignal,
)
from PyQt5.QtGui import QMovie, QPixmap, QFontMetrics, QImage
from PyQt5.QtWidgets import (
    QStyle,
    QLabel,
    QHBoxLayout,
    QWidget,
    QPushButton,
    QStyleOptionTab,
    QStylePainter,
    QTabBar,
    QLineEdit,
    QToolButton,
    QTabWidget,
    QVBoxLayout,
    QScrollArea,
)

from rare.utils.misc import icon as qta_icon
from rare.utils.paths import tmp_dir
from rare.utils.qt_requests import QtRequestManager

logger = getLogger("ExtraWidgets")


class SideTabBar(QTabBar):
    def __init__(self, padding: int = -1, parent=None):
        super(SideTabBar, self).__init__(parent=parent)
        self.setObjectName("SideTabBar")
        self.padding = padding
        self.fm = QFontMetrics(self.font())

    def tabSizeHint(self, index):
        width = QTabBar.tabSizeHint(self, index).height()
        if self.padding < 0:
            width += QTabBar.tabSizeHint(self, index).width()
        else:
            width += self.padding
        return QSize(width, self.fm.height() + 18)

    def paintEvent(self, event):
        painter = QStylePainter(self)
        opt = QStyleOptionTab()

        for i in range(self.count()):
            self.initStyleOption(opt, i)
            painter.drawControl(QStyle.CE_TabBarTabShape, opt)
            painter.save()

            s = opt.rect.size()
            s.transpose()
            r = QRect(QPoint(), s)
            r.moveCenter(opt.rect.center())
            opt.rect = r

            c = self.tabRect(i).center()
            painter.translate(c)
            painter.rotate(90)
            painter.translate(-c)
            painter.drawControl(QStyle.CE_TabBarTabLabel, opt)
            painter.restore()


class SideTabContainer(QWidget):
    def __init__(self, widget: QWidget, title: str = "", parent: QWidget = None):
        super(SideTabContainer, self).__init__(parent=parent)
        self.title = QLabel(self)
        self.setTitle(title)

        self.scrollarea = QScrollArea(self)
        self.scrollarea.setWidgetResizable(True)
        self.scrollarea.setSizeAdjustPolicy(QScrollArea.AdjustToContents)
        self.scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollarea.setFrameStyle(QScrollArea.NoFrame)
        if widget.layout():
            widget.layout().setAlignment(Qt.AlignTop)
            widget.layout().setContentsMargins(0, 0, 3, 0)
        widget.title = self.title
        widget.title.setTitle = self.setTitle
        self.scrollarea.setMinimumWidth(
            widget.sizeHint().width() + self.scrollarea.verticalScrollBar().sizeHint().width()
        )
        self.scrollarea.setWidget(widget)

        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(self.scrollarea)
        self.setLayout(layout)

    def setTitle(self, text: str) -> None:
        self.title.setText(f"<h2>{text}</h2>")
        self.title.setVisible(bool(text))


class SideTabWidget(QTabWidget):
    back_clicked = pyqtSignal()

    def __init__(self, show_back: bool = False, padding: int = -1, parent=None):
        super(SideTabWidget, self).__init__(parent=parent)
        self.setTabBar(SideTabBar(padding=padding, parent=self))
        self.setDocumentMode(True)
        self.setTabPosition(QTabWidget.West)
        if show_back:
            super(SideTabWidget, self).addTab(
                QWidget(), qta_icon("mdi.keyboard-backspace", "ei.backward"), self.tr("Back")
            )
            self.tabBarClicked.connect(self.back_func)

    def back_func(self, tab):
        # shortcut for tab == 0
        if not tab:
            self.back_clicked.emit()

    def addTab(self, widget: QWidget, a1: str, title: str = "") -> int:
        container = SideTabContainer(widget, title, parent=self)
        return super(SideTabWidget, self).addTab(container, a1)


class WaitingSpinner(QLabel):
    def __init__(self):
        super(WaitingSpinner, self).__init__()
        self.setStyleSheet(
            """
            margin-left: auto;
            margin-right: auto;
        """
        )
        self.movie = QMovie(":/images/loader.gif")
        self.setMovie(self.movie)
        self.movie.start()


class SelectViewWidget(QWidget):
    toggled = pyqtSignal()

    def __init__(self, icon_view: bool):
        super(SelectViewWidget, self).__init__()
        self.icon_view = icon_view
        self.setStyleSheet("""QPushButton{border: none; background-color: transparent}""")
        self.icon_button = QPushButton()
        self.list_button = QPushButton()
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

    def __init__(self):
        super(ImageLabel, self).__init__()
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
        super(ButtonLineEdit, self).__init__(parent)

        self.button = QToolButton(self)
        self.button.setIcon(qta_icon(icon_name, color="white"))
        self.button.setStyleSheet("border: 0px; padding: 0px;")
        self.button.setCursor(Qt.ArrowCursor)
        self.button.clicked.connect(self.buttonClicked.emit)
        self.setPlaceholderText(placeholder_text)
        frameWidth = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth)
        buttonSize = self.button.sizeHint()

        self.setStyleSheet("QLineEdit {padding-right: %dpx; }" % (buttonSize.width() + frameWidth + 1))
        self.setMinimumSize(
            max(self.minimumSizeHint().width(), buttonSize.width() + frameWidth * 2 + 2),
            max(
                self.minimumSizeHint().height(),
                buttonSize.height() + frameWidth * 2 + 2,
            ),
        )

    def resizeEvent(self, event):
        buttonSize = self.button.sizeHint()
        frameWidth = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth)
        self.button.move(
            self.rect().right() - frameWidth - buttonSize.width(),
            (self.rect().bottom() - buttonSize.height() + 1) // 2,
        )
        super(ButtonLineEdit, self).resizeEvent(event)
