from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QShortcut
from PySide6.QtWidgets import QMenu, QTabWidget, QWidget, QWidgetAction, QMessageBox

from rare.shared import RareCore, LegendaryCoreSingleton, GlobalSignalsSingleton, ArgumentsSingleton
from rare.utils.misc import qta_icon, ExitCodes
from .account import AccountWidget
from .downloads import DownloadsTab
from .library import GamesLibrary
from .settings import SettingsTab
from .store import StoreTab
from .tab_widgets import MainTabBar, TabButtonWidget


class MainTabWidget(QTabWidget):
    # int: exit code
    exit_app: Signal = Signal(int)

    def __init__(self, parent):
        super(MainTabWidget, self).__init__(parent=parent)

        self.rcore = RareCore.instance()
        self.core = LegendaryCoreSingleton()
        self.signals = GlobalSignalsSingleton()
        self.args = ArgumentsSingleton()

        self.tab_bar = MainTabBar(parent=self)
        self.setTabBar(self.tab_bar)

        # Generate Tabs
        self.games_tab = GamesLibrary(self)
        self.games_index = self.addTab(self.games_tab, self.tr("Games"))

        # Downloads Tab after Games Tab to use populated RareCore games list
        self.downloads_tab = DownloadsTab(self)
        self.downloads_index = self.addTab(self.downloads_tab, "")
        self.downloads_tab.update_title.connect(self.__on_downloads_update_title)
        self.downloads_tab.update_queues_count()
        self.setTabEnabled(self.downloads_index, not self.args.offline)

        if not self.args.offline:
            self.store_tab = StoreTab(self.core, parent=self)
            self.store_index = self.addTab(self.store_tab, self.tr("Store (Beta)"))
            self.setTabEnabled(self.store_index, not self.args.offline)

        # Space Tab
        space_index = self.addTab(QWidget(self), "")
        self.setTabEnabled(space_index, False)
        self.tab_bar.expanded = space_index

        # Settings Tab
        self.settings_tab = SettingsTab(self)
        self.settings_index = self.addTab(self.settings_tab, qta_icon("fa.gear"), "")
        self.settings_tab.about.update_available_ready.connect(
            lambda: self.tab_bar.setTabText(self.settings_index, "(!)")
        )

        # Account Button
        self.account_widget = AccountWidget(self)
        self.account_widget.exit_app.connect(self.__on_exit_app)
        account_action = QWidgetAction(self)
        account_action.setDefaultWidget(self.account_widget)
        account_button = TabButtonWidget(qta_icon("mdi.account-circle", fallback="fa.user"), tooltip="Menu")
        account_menu = QMenu(account_button)
        account_menu.addAction(account_action)
        account_button.setMenu(account_menu)
        self.tab_bar.setButton(account_button)

        # Open game list on click on Games tab button
        self.tabBarClicked.connect(self.mouse_clicked)

        # shortcuts
        QShortcut("Alt+1", self).activated.connect(lambda: self.setCurrentIndex(self.games_index))
        if not self.args.offline:
            QShortcut("Alt+2", self).activated.connect(lambda: self.setCurrentIndex(self.downloads_index))
            QShortcut("Alt+3", self).activated.connect(lambda: self.setCurrentIndex(self.store_index))
        QShortcut("Alt+4", self).activated.connect(lambda: self.setCurrentIndex(self.settings_index))

    @Slot(int)
    def __on_downloads_update_title(self, num_downloads: int):
        self.setTabText(self.indexOf(self.downloads_tab), self.tr("Downloads ({})").format(num_downloads))

    def mouse_clicked(self, index):
        if index == self.games_index:
            self.games_tab.setCurrentWidget(self.games_tab.games_page)

    def resizeEvent(self, event):
        self.tab_bar.setMinimumWidth(self.width())
        super(MainTabWidget, self).resizeEvent(event)

    @Slot(int)
    def __on_exit_app(self, exit_code: int):
        # FIXME: Don't allow logging out if there are active downloads
        if self.downloads_tab.is_download_active:
            QMessageBox.warning(
                self,
                self.tr("Quit") if exit_code == ExitCodes.EXIT else self.tr("Logout"),
                self.tr("There are active downloads. Stop them before trying to quit."),
            )
            return
        # FIXME: End of FIXME
        if exit_code == ExitCodes.LOGOUT:
            reply = QMessageBox.question(
                self,
                self.tr("Logout"),
                self.tr("Do you really want to logout <b>{}</b>?").format(self.core.lgd.userdata.get("display_name")),
                buttons=(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No),
                defaultButton=QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.core.lgd.invalidate_userdata()
            else:
                return
        self.exit_app.emit(exit_code)  # restart exit code
