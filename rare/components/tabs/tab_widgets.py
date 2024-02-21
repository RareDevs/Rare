from PyQt5.QtGui import QIcon
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

    def tabSizeHint(self, index):
        size = super(MainTabBar, self).tabSizeHint(index)
        if index == self.expanded:
            offset = self.width()
            for index in range(self.count()):
                offset -= super(MainTabBar, self).tabSizeHint(index).width()
            size.setWidth(max(size.width(), size.width() + offset))
        return size


class TabButtonWidget(QPushButton):
    def __init__(self, icon: QIcon, tooltip: str = "", parent=None):
        super(TabButtonWidget, self).__init__(parent=parent)
        self.setObjectName(type(self).__name__)
        self.setIcon(icon)
        self.setToolTip(tooltip)
