from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QTabBar, QToolButton
from qtawesome import icon


class MainTabBar(QTabBar):
    def __init__(self, expanded):
        super(MainTabBar, self).__init__()
        self._expanded = expanded
        self.setObjectName("MainTabBar")
        font = self.font()
        font.setPointSize(font.pointSize()+2)
        font.setBold(True)
        self.setFont(font)
        # self.setContentsMargins(0,10,0,10)

    def tabSizeHint(self, index):
        size = super(MainTabBar, self).tabSizeHint(index)
        if index == self._expanded:
            offset = self.width()
            for index in range(self.count()):
                offset -= super(MainTabBar, self).tabSizeHint(index).width()
            size.setWidth(max(size.width(), size.width() + offset))
        return size


class TabButtonWidget(QToolButton):
    def __init__(self, button_icon: str, tool_tip: str):
        super(TabButtonWidget, self).__init__()
        self.setText("Icon")
        self.setPopupMode(QToolButton.InstantPopup)
        self.setIcon(icon(button_icon, scale_factor=1.25))
        self.setToolTip(tool_tip)
        self.setIconSize(QSize(25, 25))
