from abc import abstractmethod
from enum import IntEnum
from logging import getLogger
from typing import Protocol

from PySide6.QtCore import (
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import QFontMetrics, QKeyEvent, QPaintEvent
from PySide6.QtWidgets import (
    QLabel,
    QLayout,
    QScrollArea,
    QSizePolicy,
    QStyle,
    QStyleOptionTab,
    QStylePainter,
    QTabBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from rare.utils.misc import qta_icon

logger = getLogger('SideTab')


class SideTabBar(QTabBar):
    class TabOrientation(IntEnum):
        Horizontal = 0
        Vertical = 1

    def __init__(
        self,
        *,
        padding: int = -1,
        orientation: TabOrientation = TabOrientation.Horizontal,
        parent: QWidget | None = None
    ):
        super(SideTabBar, self).__init__(parent=parent)
        self.setObjectName(type(self).__name__)
        self.padding = padding
        self.orientation = orientation
        self.fm = QFontMetrics(self.font())

    # NOTE: if we ever implement a QProxyStyle, this is likely to conflict

    def tabSizeHint(self, index) -> QSize:
        if self.orientation == SideTabBar.TabOrientation.Vertical:
            return super(SideTabBar, self).tabSizeHint(index)

        width = QTabBar.tabSizeHint(self, index).height()
        if self.padding < 0:
            width += QTabBar.tabSizeHint(self, index).width()
        else:
            width += self.padding
        return QSize(width, self.fm.height() + 18)

    def paintEvent(self, event: QPaintEvent):
        if self.orientation == SideTabBar.TabOrientation.Vertical:
            super(SideTabBar, self).paintEvent(event)
            return

        painter = QStylePainter(self)
        opt = QStyleOptionTab()
        for i in range(self.count()):
            self.initStyleOption(opt, i)
            painter.save()
            painter.drawControl(QStyle.ControlElement.CE_TabBarTabShape, opt)
            opt.shape = QTabBar.Shape.RoundedNorth
            painter.drawControl(QStyle.ControlElement.CE_TabBarTabLabel, opt)
            painter.restore()
        event.setAccepted(True)


class SideTabContents:
    # str: title
    set_title = Signal(str)
    implements_scrollarea: bool = False


class SideTabContentsProtocol(Protocol):
    implements_scrollarea: bool

    @abstractmethod
    def layout(self) -> QLayout:
        pass

    @abstractmethod
    def set_title(self) -> Signal:
        pass

    @abstractmethod
    def sizeHint(self) -> QSize:
        pass


class SideTabContainer(QWidget):
    def __init__(
        self,
        widget: QWidget | SideTabContentsProtocol,
        title: str = '',
        *,
        parent: QWidget | None = None,
    ):
        super(SideTabContainer, self).__init__(parent=parent)
        self.title = QLabel(self)
        self.setTitle(title)

        if widget.layout():
            widget.layout().setAlignment(Qt.AlignmentFlag.AlignTop)
            widget.layout().setContentsMargins(0, 0, 3, 0)
        if hasattr(widget, 'set_title'):
            widget.set_title.connect(self.setTitle)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)

        if not hasattr(widget, 'implements_scrollarea') or not widget.implements_scrollarea:
            scrollarea = QScrollArea(self)
            scrollarea.setSizeAdjustPolicy(QScrollArea.SizeAdjustPolicy.AdjustToContents)
            scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scrollarea.setFrameStyle(QScrollArea.Shape.NoFrame)
            scrollarea.setMinimumWidth(widget.sizeHint().width() + scrollarea.verticalScrollBar().sizeHint().width())
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
        self.title.setText(f'<h2>{text}</h2>')
        self.title.setVisible(bool(text))


class SideTabWidget(QTabWidget):
    backClicked = Signal()

    def __init__(
        self,
        show_back: bool = False,
        *,
        padding: int = -1,
        tab_position: QTabWidget.TabPosition = QTabWidget.TabPosition.West,
        tab_orientation: SideTabBar.TabOrientation = SideTabBar.TabOrientation.Horizontal,
        parent: QWidget | None = None,
    ):
        super(SideTabWidget, self).__init__(parent=parent)
        self.setTabBar(SideTabBar(padding=padding, orientation=tab_orientation, parent=self))
        self.setTabPosition(tab_position)
        self.setDocumentMode(True)
        if show_back:
            super(SideTabWidget, self).addTab(
                QWidget(self),
                qta_icon('mdi.keyboard-backspace', 'ei.backward'),
                self.tr('Back'),
            )
            self.tabBarClicked.connect(self._on_tab_clicked)

    def _on_tab_clicked(self, tab):
        # shortcut for tab == 0
        if not tab:
            self.backClicked.emit()

    def keyPressEvent(self, a0: QKeyEvent):
        if a0.key() == Qt.Key.Key_Escape:
            self.backClicked.emit()

    def addTab(self, widget: QWidget | SideTabContentsProtocol, a1: str, title: str = '') -> int:
        container = SideTabContainer(widget, title, parent=self)
        return super(SideTabWidget, self).addTab(container, a1)
