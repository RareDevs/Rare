from PySide6.QtCore import QEvent, QObject, Signal, Slot
from PySide6.QtGui import QShortcut, Qt
from PySide6.QtWidgets import QMenu, QMessageBox, QTabWidget, QWidget, QWidgetAction

from rare.models.settings import RareAppSettings
from rare.shared import RareCore
from rare.utils.misc import ExitCodes, qta_icon

from .account import AccountWidget
from .downloads import DownloadsTab
from .integrations import IntegrationsTab
from .library import GamesLibrary
from .settings import SettingsTab
from .store import StoreTab
from .tab_widgets import MainTabBar


class MainTabWidget(QTabWidget):
    # int: exit code
    exit_app: Signal = Signal(int)

    def __init__(self, settings: RareAppSettings, rcore: RareCore, parent):
        super(MainTabWidget, self).__init__(parent=parent)
        self.setObjectName(type(self).__name__)

        self.settings = settings
        self.rcore = rcore
        self.core = rcore.core()
        self.signals = rcore.signals()
        self.args = rcore.args()

        self.main_bar = MainTabBar(parent=self)
        self.main_bar.installEventFilter(self)
        self.setTabBar(self.main_bar)

        # Generate Tabs
        self.games_tab = GamesLibrary(self.settings, self.rcore, self)
        self.games_tab.import_clicked.connect(self.show_import)
        self.games_index = self.addTab(self.games_tab, self.tr("Games"))

        # Downloads Tab after Games Tab to use populated RareCore games list
        self.downloads_tab = DownloadsTab(self.settings, self.rcore, self)
        self.downloads_index = self.addTab(self.downloads_tab, "")
        self.downloads_tab.update_title.connect(self.__on_downloads_update_title)
        self.downloads_tab.update_queues_count()
        self.setTabEnabled(self.downloads_index, not self.args.offline)

        if not self.args.offline:
            self.store_tab = StoreTab(self.core, parent=self)
            self.store_index = self.addTab(self.store_tab, self.tr("Store (Beta)"))
            self.setTabEnabled(self.store_index, not self.args.offline)

        # Space Tab
        space_index = self.addTab(QWidget(self), "Rare")
        self.setTabEnabled(space_index, False)
        self.main_bar.expanded_idx = space_index

        # Integrations Tab
        self.integrations_tab = IntegrationsTab(self.rcore, self)
        self.integrations_index = self.addTab(self.integrations_tab, self.tr("Integrations"))

        # Account Tab
        self.account_widget = AccountWidget(self.signals, self.core, self)
        self.account_widget.exit_app.connect(self.__on_exit_app)
        account_action = QWidgetAction(self)
        account_action.setDefaultWidget(self.account_widget)
        self.account_menu = QMenu(self)
        self.account_menu.addAction(account_action)
        self.account_tab = QWidget(self)
        self.account_index = self.addTab(
            self.account_tab, qta_icon("mdi.account-circle", "fa5s.user"), self.core.lgd.userdata.get("displayName")
        )

        # Settings Tab
        self.settings_tab = SettingsTab(settings, rcore, self)
        self.settings_index = self.addTab(self.settings_tab, qta_icon("fa.gear", "fa6s.gear"), "")
        self.settings_tab.about.update_available_ready.connect(lambda: self.main_bar.setTabText(self.settings_index, "(!)"))

        # Open game list on click on Games tab button
        self.tabBarClicked.connect(self.mouse_clicked)

        # shortcuts
        QShortcut("Alt+1", self).activated.connect(lambda: self.setCurrentIndex(self.games_index))
        if not self.args.offline:
            QShortcut("Alt+2", self).activated.connect(lambda: self.setCurrentIndex(self.downloads_index))
            QShortcut("Alt+3", self).activated.connect(lambda: self.setCurrentIndex(self.store_index))
        QShortcut("Alt+4", self).activated.connect(lambda: self.setCurrentIndex(self.integrations_index))
        QShortcut("Alt+5", self).activated.connect(lambda: self.setCurrentIndex(self.settings_index))

        self.setCurrentIndex(self.games_index)

    def eventFilter(self, w: QObject, e: QEvent) -> bool:
        if not isinstance(e, QEvent):
            return True
        if w is self.main_bar and e.type() == QEvent.Type.MouseButtonPress:
            tab_idx = self.main_bar.tabAt(e.pos())
            if tab_idx == self.account_index:
                if e.button() == Qt.MouseButton.LeftButton:
                    self.account_menu.exec(
                        self.mapToGlobal(self.main_bar.tabRect(tab_idx).bottomRight() - self.account_menu.rect().topRight())
                    )
                return True
        return False

    @Slot()
    @Slot(str)
    def show_import(self, app_name: str = None):
        self.setCurrentWidget(self.integrations_tab)
        self.integrations_tab.show_import(app_name)

    @Slot()
    def show_egl_sync(self):
        self.setCurrentWidget(self.integrations_tab)
        self.integrations_tab.show_egl_sync()

    @Slot()
    def show_eos(self):
        self.setCurrentWidget(self.integrations_tab)
        self.integrations_tab.show_eos()

    @Slot()
    def show_ubisoft(self):
        self.setCurrentWidget(self.integrations_tab)
        self.integrations_tab.show_ubisoft()

    @Slot(int)
    def __on_downloads_update_title(self, num_downloads: int):
        self.setTabText(
            self.indexOf(self.downloads_tab),
            self.tr("Downloads ({})").format(num_downloads),
        )

    def mouse_clicked(self, index):
        if index == self.games_index:
            self.games_tab.show_library()
        if index == self.integrations_index:
            self.integrations_tab.show_import()

    def resizeEvent(self, event):
        self.main_bar.setMinimumWidth(self.width())
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
