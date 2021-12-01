from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QMenu, QTabWidget, QWidget, QWidgetAction, QShortcut
from qtawesome import icon

from rare import shared
from rare.components.tabs.account import MiniWidget
from rare.components.tabs.downloads import DownloadsTab
from rare.components.tabs.games import GamesTab
from rare.components.tabs.settings import SettingsTab
from rare.components.tabs.settings.debug import DebugSettings
from rare.components.tabs.shop import Shop
from rare.components.tabs.tab_utils import MainTabBar, TabButtonWidget


class TabWidget(QTabWidget):
    def __init__(self, parent):
        super(TabWidget, self).__init__(parent=parent)
        disabled_tab = 3 if not shared.args.offline else 1
        self.core = shared.core
        self.signals = shared.signals
        self.setTabBar(MainTabBar(disabled_tab))
        # lk: Figure out why this adds a white line at the top
        # lk: despite setting qproperty-drawBase to 0 in the stylesheet
        # self.setDocumentMode(True)
        # Generate Tabs
        self.games_tab = GamesTab()
        self.addTab(self.games_tab, self.tr("Games"))

        if not shared.args.offline:
            # updates = self.games_tab.default_widget.game_list.updates
            self.downloadTab = DownloadsTab(self.games_tab.updates)
            self.addTab(self.downloadTab, "Downloads" + (
                " (" + str(len(self.games_tab.updates)) + ")" if len(self.games_tab.updates) != 0 else ""))
            self.store = Shop(self.core)
            self.addTab(self.store, self.tr("Store (Beta)"))

        self.settings = SettingsTab(self)
        if shared.args.debug:
            self.settings.addTab(DebugSettings(), "Debug")

        # Space Tab
        self.addTab(QWidget(), "")
        self.setTabEnabled(disabled_tab, False)
        # Button
        self.account = QWidget()
        self.addTab(self.account, "")
        self.setTabEnabled(disabled_tab + 1, False)

        self.mini_widget = MiniWidget()
        account_action = QWidgetAction(self)
        account_action.setDefaultWidget(self.mini_widget)
        account_button = TabButtonWidget('mdi.account-circle', 'Account')
        account_button.setMenu(QMenu())
        account_button.menu().addAction(account_action)
        self.tabBar().setTabButton(disabled_tab + 1, self.tabBar().RightSide, account_button)

        self.addTab(self.settings, icon("fa.gear"), "")

        self.settings.about.update_available_ready.connect(lambda: self.tabBar().setTabText(5, "(!)"))
        # Signals
        # set current index
        self.signals.set_main_tab_index.connect(self.setCurrentIndex)

        # update dl tab text
        self.signals.update_download_tab_text.connect(self.update_dl_tab_text)

        # Open game list on click on Games tab button
        self.tabBarClicked.connect(self.mouse_clicked)
        self.setIconSize(QSize(25, 25))

        # shortcuts
        QShortcut("Alt+1", self).activated.connect(lambda: self.setCurrentIndex(0))
        QShortcut("Alt+2", self).activated.connect(lambda: self.setCurrentIndex(1))
        QShortcut("Alt+3", self).activated.connect(lambda: self.setCurrentIndex(2))
        QShortcut("Alt+4", self).activated.connect(lambda: self.setCurrentIndex(5))

    def update_dl_tab_text(self):
        num_downloads = len(set([i.options.app_name for i in self.downloadTab.dl_queue] + [i for i in
                                                                                           self.downloadTab.update_widgets.keys()]))

        if num_downloads != 0:
            self.setTabText(1, f"Downloads ({num_downloads})")
        else:
            self.setTabText(1, "Downloads")

    def mouse_clicked(self, tab_num):
        if tab_num == 0:
            self.games_tab.layout().setCurrentIndex(0)

        if not shared.args.offline and tab_num == 2:
            self.store.load()

    def resizeEvent(self, event):
        self.tabBar().setMinimumWidth(self.width())
        super(TabWidget, self).resizeEvent(event)
