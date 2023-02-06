from PyQt5.QtCore import QSize, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QMenu, QTabWidget, QWidget, QWidgetAction, QShortcut, QMessageBox

from rare.shared import RareCore, LegendaryCoreSingleton, GlobalSignalsSingleton, ArgumentsSingleton
from rare.utils.misc import icon
from .account import AccountWidget
from .downloads import DownloadsTab
from .games import GamesTab
from .settings import SettingsTab
from .settings.debug import DebugSettings
from .shop import Shop
from .tab_widgets import MainTabBar, TabButtonWidget


class MainTabWidget(QTabWidget):
    # int: exit code
    exit_app: pyqtSignal = pyqtSignal(int)

    def __init__(self, parent):
        super(MainTabWidget, self).__init__(parent=parent)
        self.rcore = RareCore.instance()
        self.core = LegendaryCoreSingleton()
        self.signals = GlobalSignalsSingleton()
        self.args = ArgumentsSingleton()

        self.tab_bar = MainTabBar(parent=self)
        self.setTabBar(self.tab_bar)

        # Generate Tabs
        self.games_tab = GamesTab(self)
        self.games_index = self.addTab(self.games_tab, self.tr("Games"))

        # Downloads Tab after Games Tab to use populated RareCore games list
        if not self.args.offline:
            self.downloads_tab = DownloadsTab(self)
            self.downloads_index = self.addTab(self.downloads_tab, "")
            self.downloads_tab.update_title.connect(self.__on_downloads_update_title)
            self.downloads_tab.update_queues_count()
            self.setTabEnabled(self.downloads_index, not self.args.offline)

            self.store_tab = Shop(self.core)
            self.store_index = self.addTab(self.store_tab, self.tr("Store (Beta)"))
            self.setTabEnabled(self.store_index, not self.args.offline)

        # Space Tab
        space_index = self.addTab(QWidget(self), "")
        self.setTabEnabled(space_index, False)
        self.tab_bar.expanded = space_index
        # Button
        button_index = self.addTab(QWidget(self), "")
        self.setTabEnabled(button_index, False)

        self.account_widget = AccountWidget(self)
        self.account_widget.logout.connect(self.logout)
        account_action = QWidgetAction(self)
        account_action.setDefaultWidget(self.account_widget)
        account_button = TabButtonWidget("mdi.account-circle", "Account", fallback_icon="fa.user")
        account_button.setMenu(QMenu())
        account_button.menu().addAction(account_action)
        self.tab_bar.setTabButton(
            button_index, MainTabBar.RightSide, account_button
        )

        self.settings_tab = SettingsTab(self)
        self.settings_index = self.addTab(self.settings_tab, icon("fa.gear"), "")
        self.settings_tab.about.update_available_ready.connect(
            lambda: self.tab_bar.setTabText(self.settings_index, "(!)")
        )

        # Open game list on click on Games tab button
        self.tabBarClicked.connect(self.mouse_clicked)
        self.setIconSize(QSize(24, 24))

        # shortcuts
        QShortcut("Alt+1", self).activated.connect(lambda: self.setCurrentIndex(self.games_index))
        if not self.args.offline:
            QShortcut("Alt+2", self).activated.connect(lambda: self.setCurrentIndex(self.downloads_index))
            QShortcut("Alt+3", self).activated.connect(lambda: self.setCurrentIndex(self.store_index))
        QShortcut("Alt+4", self).activated.connect(lambda: self.setCurrentIndex(self.settings_index))

    @pyqtSlot(int)
    def __on_downloads_update_title(self, num_downloads: int):
        self.setTabText(self.indexOf(self.downloads_tab), self.tr("Downloads ({})").format(num_downloads))

    def mouse_clicked(self, index):
        if index == self.games_index:
            self.games_tab.setCurrentWidget(self.games_tab.games_page)

        if not self.args.offline and index == self.store_index:
            self.store_tab.load()

    def resizeEvent(self, event):
        self.tab_bar.setMinimumWidth(self.width())
        super(MainTabWidget, self).resizeEvent(event)

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
