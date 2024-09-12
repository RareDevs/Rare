from PySide6.QtCore import QEvent, QPoint
from PySide6.QtGui import QIcon, QResizeEvent
from PySide6.QtWidgets import QTabBar, QPushButton, QSizePolicy


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

    def __align_button(self):
        self.button.move(QPoint(
            self.tabRect(self.expanded).right() - self.button.width() - self.style().PixelMetric.PM_DefaultFrameWidth,
            self.tabRect(self.expanded).bottom() - self.button.height()
        ))

    def resizeEvent(self, e: QResizeEvent):
        super().resizeEvent(e)
        self.__align_button()

    def event(self, e):
        if e.type() == QEvent.Type.StyleChange:
            self.button.setFixedHeight(self.button.minimumSizeHint().height())
            self.button.setFixedWidth(self.button.minimumSizeHint().width())
            self.__align_button()
        return super().event(e)

    def setButton(self, widget: QPushButton):
        widget.setParent(self)
        widget.setFixedHeight(widget.minimumSizeHint().height())
        widget.setFixedWidth(widget.minimumSizeHint().width())
        self.button = widget


class TabButtonWidget(QPushButton):
    def __init__(self, icon: QIcon, text: str = "", tooltip: str = "", parent=None):
        super(TabButtonWidget, self).__init__(parent=parent)
        self.setObjectName(type(self).__name__)
        self.setIcon(icon)
        self.setText(text)
        self.setToolTip(tooltip)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
