from logging import getLogger

from PyQt5.QtCore import (
    Qt,
    QRect,
    QSize,
    QPoint,
    pyqtSignal,
)
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import (
    QStyle,
    QLabel,
    QWidget,
    QStyleOptionTab,
    QStylePainter,
    QTabBar,
    QTabWidget,
    QVBoxLayout,
    QScrollArea,
)

from rare.utils.misc import icon as qta_icon

logger = getLogger("SideTab")


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
