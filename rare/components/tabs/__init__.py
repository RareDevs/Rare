from PyQt5.QtCore import QSize, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QMenu, QTabWidget, QWidget, QWidgetAction, QShortcut, QMessageBox

from rare.shared import RareCore, LegendaryCoreSingleton, GlobalSignalsSingleton, ArgumentsSingleton
from rare.components.tabs.account import AccountWidget
from rare.components.tabs.downloads import DownloadsTab
from rare.components.tabs.games import GamesTab
from rare.components.tabs.settings import SettingsTab
from rare.components.tabs.settings.debug import DebugSettings
from rare.components.tabs.shop import Shop
from rare.components.tabs.tab_utils import MainTabBar, TabButtonWidget
from rare.utils.misc import icon


class TabWidget(QTabWidget):
    # int: exit code
    exit_app: pyqtSignal = pyqtSignal(int)

    def __init__(self, parent):
        super(TabWidget, self).__init__(parent=parent)
        self.rcore = RareCore.instance()
        self.core = LegendaryCoreSingleton()
        self.signals = GlobalSignalsSingleton()
        self.args = ArgumentsSingleton()
        disabled_tab = 3 if not self.args.offline else 1
        self.setTabBar(MainTabBar(disabled_tab))

        # Generate Tabs
        self.games_tab = GamesTab(self)
        self.addTab(self.games_tab, self.tr("Games"))

        # Downloads Tab after Games Tab to use populated RareCore games list
        if not self.args.offline:
            self.downloads_tab = DownloadsTab(self)
            # update dl tab text
            self.addTab(self.downloads_tab, "")
            self.downloads_tab.update_title.connect(self.__on_downloads_update_title)
            self.downloads_tab.update_queues_count()
            self.store = Shop(self.core)
            self.addTab(self.store, self.tr("Store (Beta)"))

        self.settings_tab = SettingsTab(self)
        if self.args.debug:
            self.settings_tab.addTab(DebugSettings(), "Debug")

        # Space Tab
        self.addTab(QWidget(), "")
        self.setTabEnabled(disabled_tab, False)
        # Button
        self.addTab(QWidget(), "")
        self.setTabEnabled(disabled_tab + 1, False)

        self.account_widget = AccountWidget(self)
        self.account_widget.logout.connect(self.logout)
        account_action = QWidgetAction(self)
        account_action.setDefaultWidget(self.account_widget)
        account_button = TabButtonWidget("mdi.account-circle", "Account", fallback_icon="fa.user")
        account_button.setMenu(QMenu())
        account_button.menu().addAction(account_action)
        self.tabBar().setTabButton(
            disabled_tab + 1, self.tabBar().RightSide, account_button
        )

        self.addTab(self.settings_tab, icon("fa.gear"), "")

        self.settings_tab.about.update_available_ready.connect(
            lambda: self.tabBar().setTabText(5, "(!)")
        )

        # Open game list on click on Games tab button
        self.tabBarClicked.connect(self.mouse_clicked)
        self.setIconSize(QSize(24, 24))

        # shortcuts
        QShortcut("Alt+1", self).activated.connect(lambda: self.setCurrentWidget(self.games_tab))
        if not self.args.offline:
            QShortcut("Alt+2", self).activated.connect(lambda: self.setCurrentWidget(self.downloads_tab))
            QShortcut("Alt+3", self).activated.connect(lambda: self.setCurrentWidget(self.store))
        QShortcut("Alt+4", self).activated.connect(lambda: self.setCurrentWidget(self.settings_tab))

    @pyqtSlot(int)
    def __on_downloads_update_title(self, num_downloads: int):
        self.setTabText(self.indexOf(self.downloads_tab), self.tr("Downloads ({})").format(num_downloads))

    def mouse_clicked(self, tab_num):
        if tab_num == 0:
            self.games_tab.setCurrentWidget(self.games_tab.games_page)

        if not self.args.offline and tab_num == 2:
            self.store.load()

    def resizeEvent(self, event):
        self.tabBar().setMinimumWidth(self.width())
        super(TabWidget, self).resizeEvent(event)

    @pyqtSlot()
    def logout(self):
        # FIXME: Don't allow logging out if there are active downloads
        if self.downloads_tab.is_download_active:
            QMessageBox.warning(
                self,
                self.tr("Logout"),
                self.tr("There are active downloads. Stop them before logging out."),
            )
            return
        # FIXME: End of FIXME
        reply = QMessageBox.question(
            self,
            self.tr("Logout"),
            self.tr("Do you really want to logout <b>{}</b>?").format(self.core.lgd.userdata.get("display_name")),
            buttons=(QMessageBox.Yes | QMessageBox.No),
            defaultButton=QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.core.lgd.invalidate_userdata()
            self.exit_app.emit(-133742)  # restart exit code
