from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QTabWidget, QTabBar, QWidget, QToolButton, QWidgetAction, QMenu
from Rare import style_path
from Rare.Components.Tabs.Account.AccountWidget import MiniWidget
from Rare.Components.Tabs.Games.Games import Games


class TabWidget(QTabWidget):
    def __init__(self, core):
        super(TabWidget, self).__init__()
        self.setTabBar(TabBar(2))

        self.game_list = Games(core)

        self.addTab(self.game_list, self.tr("Games"))

        self.downloads = QWidget()
        self.addTab(self.downloads, "Downloads")

        # Space Tab
        self.addTab(QWidget(), "")
        self.setTabEnabled(2, False)

        self.account = QWidget()
        self.addTab(self.account, "")
        self.setTabEnabled(3, False)

        # self.settings = SettingsTab(core)
        self.settings = QWidget()
        self.addTab(self.settings, QIcon(style_path + "/Icons/settings.png"), "")

        self.tabBar().setTabButton(3, self.tabBar().RightSide, TabButtonWidget(core))

    def resizeEvent(self, event):
        self.tabBar().setMinimumWidth(self.width())
        super(TabWidget, self).resizeEvent(event)

    def download(self):
        self.downloads.download()


class TabBar(QTabBar):
    def __init__(self, expanded):
        super(TabBar, self).__init__()
        self._expanded = expanded

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
        self.setIcon(QIcon(style_path+"/Icons/account.png"))
        self.setToolTip("Account")
        self.setMenu(QMenu())
        action = QWidgetAction(self)
        action.setDefaultWidget(MiniWidget(core))
        self.menu().addAction(action)
