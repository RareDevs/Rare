from logging import getLogger
from typing import Union, Protocol

from PySide6.QtCore import (
    Qt,
    QRect,
    QSize,
    QPoint,
    Signal,
)
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import (
    QStyle,
    QLabel,
    QWidget,
    QStyleOptionTab,
    QStylePainter,
    QTabBar,
    QTabWidget,
    QVBoxLayout,
    QScrollArea, QLayout, QSizePolicy,
)

from rare.utils.misc import qta_icon

logger = getLogger("SideTab")


class SideTabBar(QTabBar):
    def __init__(self, padding: int = -1, parent=None):
        super(SideTabBar, self).__init__(parent=parent)
        self.setObjectName(type(self).__name__)
        self.padding = padding
        self.fm = QFontMetrics(self.font())

    # NOTE: if we ever implement a QProxyStyle, this is likely to conflict

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
            painter.save()
            painter.drawControl(QStyle.ControlElement.CE_TabBarTabShape, opt)
            opt.shape = QTabBar.Shape.RoundedNorth
            painter.drawControl(QStyle.ControlElement.CE_TabBarTabLabel, opt)
            painter.restore()


class SideTabContents(object):
    # str: title
    set_title = Signal(str)
    implements_scrollarea: bool = False


class SideTabContentsProtocol(Protocol):
    implements_scrollarea: bool

    def layout(self) -> QLayout:
        pass

    def set_title(self) -> Signal:
        pass

    def sizeHint(self) -> QSize:
        pass


class SideTabContainer(QWidget):
    def __init__(self, widget: Union[QWidget, SideTabContentsProtocol], title: str = "", parent: QWidget = None):
        super(SideTabContainer, self).__init__(parent=parent)
        self.title = QLabel(self)
        self.setTitle(title)

        if widget.layout():
            widget.layout().setAlignment(Qt.AlignmentFlag.AlignTop)
            widget.layout().setContentsMargins(0, 0, 3, 0)
        if hasattr(widget, "set_title"):
            widget.set_title.connect(self.setTitle)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)

        if not hasattr(widget, "implements_scrollarea") or not widget.implements_scrollarea:
            scrollarea = QScrollArea(self)
            scrollarea.setSizeAdjustPolicy(QScrollArea.SizeAdjustPolicy.AdjustToContents)
            scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scrollarea.setFrameStyle(QScrollArea.Shape.NoFrame)
            scrollarea.setMinimumWidth(
                widget.sizeHint().width() + scrollarea.verticalScrollBar().sizeHint().width()
            )
            scrollarea.setWidgetResizable(True)
            widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            scrollarea.setWidget(widget)
            scrollarea.widget().setAutoFillBackground(False)
            scrollarea.viewport().setAutoFillBackground(False)
            layout.addWidget(scrollarea)
        else:
            layout.addWidget(widget)

        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    def setTitle(self, text: str) -> None:
        self.title.setText(f"<h2>{text}</h2>")
        self.title.setVisible(bool(text))


class SideTabWidget(QTabWidget):
    back_clicked = Signal()

    def __init__(self, show_back: bool = False, padding: int = -1, parent=None):
        super(SideTabWidget, self).__init__(parent=parent)
        self.setTabBar(SideTabBar(padding=padding, parent=self))
        self.setDocumentMode(True)
        self.setTabPosition(QTabWidget.TabPosition.West)
        if show_back:
            super(SideTabWidget, self).addTab(
                QWidget(self), qta_icon("mdi.keyboard-backspace", "ei.backward"), self.tr("Back")
            )
            self.tabBarClicked.connect(self.back_func)

    def back_func(self, tab):
        # shortcut for tab == 0
        if not tab:
            self.back_clicked.emit()

    def addTab(self, widget: Union[QWidget, SideTabContentsProtocol], a1: str, title: str = "") -> int:
        container = SideTabContainer(widget, title, parent=self)
        return super(SideTabWidget, self).addTab(container, a1)
