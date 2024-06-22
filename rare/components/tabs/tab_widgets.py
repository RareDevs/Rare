from PyQt5.QtCore import QEvent, QPoint
from PyQt5.QtGui import QIcon, QResizeEvent
from PyQt5.QtWidgets import QTabBar, QSizePolicy, QPushButton


class MainTabBar(QTabBar):
    def __init__(self, parent=None):
        super(MainTabBar, self).__init__(parent=parent)
        self.setObjectName(type(self).__name__)
        font = self.font()
        font.setPointSize(font.pointSize() + 1)
        font.setBold(True)
        self.setFont(font)

        self.expanded = -1
        self.button: TabButtonWidget = None

    def tabSizeHint(self, index):
        size = super(MainTabBar, self).tabSizeHint(index)
        if index == self.expanded:
            offset = self.width()
            for index in range(self.count()):
                offset -= super(MainTabBar, self).tabSizeHint(index).width()
            size.setWidth(max(size.width(), size.width() + offset))
        return size

    def __center_button(self):
        self.button.move(QPoint(
            self.tabRect(self.expanded).right() - self.button.width() - self.style().PixelMetric.PM_DefaultFrameWidth,
            self.tabRect(self.expanded).bottom() - self.button.height()
        ))

    def resizeEvent(self, e: QResizeEvent):
        super().resizeEvent(e)
        self.__center_button()

    def event(self, e):
        if e.type() == QEvent.Type.StyleChange:
            self.__center_button()
        return super().event(e)

    def setButton(self, widget: QPushButton):
        widget.setParent(self)
        widget.setFixedHeight(self.style().PixelMetric.PM_TabBarTabVSpace)
        widget.setFixedWidth(widget.minimumSizeHint().width())
        self.button = widget


class TabButtonWidget(QPushButton):
    def __init__(self, icon: QIcon, tooltip: str = "", parent=None):
        super(TabButtonWidget, self).__init__(parent=parent)
        self.setObjectName(type(self).__name__)
        self.setIcon(icon)
        self.setToolTip(tooltip)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
