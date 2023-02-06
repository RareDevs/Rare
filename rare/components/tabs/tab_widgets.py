from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QTabBar, QToolButton

from rare.utils.misc import icon


class MainTabBar(QTabBar):
    def __init__(self, parent=None):
        super(MainTabBar, self).__init__(parent=parent)
        self.setObjectName("MainTabBar")
        font = self.font()
        font.setPointSize(font.pointSize() + 2)
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


class TabButtonWidget(QToolButton):
    def __init__(self, button_icon: str, tool_tip: str, fallback_icon=None, parent=None):
        super(TabButtonWidget, self).__init__(parent=parent)
        self.setText("Icon")
        self.setPopupMode(QToolButton.InstantPopup)
        self.setIcon(icon(button_icon, fallback_icon, scale_factor=1.25))
        self.setToolTip(tool_tip)
        self.setIconSize(QSize(25, 25))
