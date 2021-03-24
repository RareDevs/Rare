from PyQt5.QtCore import QSize
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QTabBar, QToolButton, QMenu, QWidgetAction
from Rare.Components.Tabs.Account.AccountWidget import MiniWidget
from qtawesome import icon


class TabBar(QTabBar):
    def __init__(self, expanded):
        super(TabBar, self).__init__()
        self._expanded = expanded
        self.setObjectName("main_tab_bar")
        self.setFont(QFont("Arial", 13))
        # self.setContentsMargins(0,10,0,10)

    def tabSizeHint(self, index):
        size = super(TabBar, self).tabSizeHint(index)
        if index == self._expanded:
            offset = self.width()
            for index in range(self.count()):
                offset -= super(TabBar, self).tabSizeHint(index).width()
            size.setWidth(max(size.width(), size.width() + offset))
        return size


class TabButtonWidget(QToolButton):
    def __init__(self, core):
        super(TabButtonWidget, self).__init__()
        self.setText("Icon")
        self.setPopupMode(QToolButton.InstantPopup)
        self.setIcon(icon("mdi.account-circle", color="white", scale_factor=1.25))
        self.setToolTip("Account")
        self.setIconSize(QSize(25, 25))
        self.setMenu(QMenu())
        action = QWidgetAction(self)
        action.setDefaultWidget(MiniWidget(core))
        self.menu().addAction(action)
