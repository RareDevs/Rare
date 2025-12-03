from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QTabBar


class MainTabBar(QTabBar):
    def __init__(self, parent=None):
        super(MainTabBar, self).__init__(parent=parent)
        self.setObjectName(type(self).__name__)
        self.setProperty("drawBase", False)

        font = self.font()
        font.setPointSize(font.pointSize() + 1)
        font.setBold(True)
        self.setFont(font)

        self.expanded = -1

    def tabSizeHint(self, index):
        size = super(MainTabBar, self).tabSizeHint(index)
        if index == self.expanded:
            offset = self.width()
            for index in range(self.count()):
                offset -= super(MainTabBar, self).tabSizeHint(index).width()
            size.setWidth(max(size.width(), size.width() + offset))
        return size

    def resizeEvent(self, e: QResizeEvent):
        super().resizeEvent(e)

    def event(self, e):
        return super().event(e)
