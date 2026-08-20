from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QShortcut
from PySide6.QtWidgets import QMessageBox, QTabWidget, QWidget

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

        self.navigation_bar = MainTabBar(parent=self)
        self.setTabBar(self.navigation_bar)
        self.setTabPosition(QTabWidget.TabPosition.West)

        self.collapse_index = self.addTab(
            QWidget(self), qta_icon('fa5s.bars', 'fa.bars'), self.tr('Toggle')
        )
        self.navigation_bar.setTabToolTip(self.collapse_index, self.tr('Toggle sidebar'))
        self.navigation_bar.collapse_index = self.collapse_index

        # Generate Tabs
        self.games_tab = GamesLibrary(self.settings, self.rcore, self)
        self.games_tab.import_clicked.connect(self.show_import)
        self.games_index = self.addTab(
            self.games_tab, qta_icon('ri.gamepad-line', 'fa5s.gamepad'), self.tr('Games')
        )
        self.navigation_bar.setTabToolTip(self.games_index, self.tr('Games'))

        # Downloads Tab after Games Tab to use populated RareCore games list
        self.downloads_tab = DownloadsTab(self.settings, self.rcore, self)
        self.downloads_index = self.addTab(self.downloads_tab, qta_icon('fa5s.download'), '')
        self.downloads_tab.update_title.connect(self.__on_downloads_update_title)
        self.downloads_tab.update_queues_count()
        self.setTabEnabled(self.downloads_index, not self.args.offline)

        if not self.args.offline:
            self.store_tab = StoreTab(self.core, parent=self)
            self.store_index = self.addTab(
                self.store_tab, qta_icon('fa5s.shopping-cart'), self.tr('Store')
            )
            self.navigation_bar.setTabToolTip(self.store_index, self.tr('Store'))
            self.setTabEnabled(self.store_index, not self.args.offline)

        # Space Tab
        space_index = self.addTab(QWidget(self), 'Rare')
        self.setTabEnabled(space_index, False)
        self.navigation_bar.expanded_index = space_index

        # Integrations Tab
        self.integrations_tab = IntegrationsTab(self.rcore, self)
        self.integrations_index = self.addTab(
            self.integrations_tab, qta_icon('fa5s.plug', 'fa5s.link'), self.tr('Integrations')
        )
        self.navigation_bar.setTabToolTip(self.integrations_index, self.tr('Integrations'))

        # Settings Tab
        self.settings_tab = SettingsTab(settings, rcore, self)
        self.settings_index = self.addTab(
            self.settings_tab, qta_icon('fa.gear', 'fa6s.gear'), self.tr('Settings')
        )
        self.navigation_bar.setTabToolTip(self.settings_index, self.tr('Settings'))
        self.settings_tab.update_available.connect(self._on_update_available)

        # Account Tab
        self.account_widget = AccountWidget(self.signals, self.core, self)
        self.account_widget.exit_app.connect(self._on_exit_app)
        self.account_index = self.addTab(
            self.account_widget, qta_icon('mdi.account-circle', 'fa5s.user'), self.core.lgd.userdata.get('displayName'),
        )

        # Open game list on click on Games tab button
        self.tabBarClicked.connect(self.mouse_clicked)

        # shortcuts
        QShortcut('Alt+1', self).activated.connect(self._on_shortcut_activated_games)
        if not self.args.offline:
            QShortcut('Alt+2', self).activated.connect(self._on_shortcut_activated_downloads)
            QShortcut('Alt+3', self).activated.connect(self._on_shortcut_activated_store)
        QShortcut('Alt+4', self).activated.connect(self._on_shortcut_activated_integrations)
        QShortcut('Alt+5', self).activated.connect(self._on_shortcut_activated_settings)

        self.setCurrentIndex(self.games_index)

    @Slot()
    def _on_shortcut_activated_games(self):
        self.setCurrentIndex(self.games_index)

    @Slot()
    def _on_shortcut_activated_downloads(self):
        self.setCurrentIndex(self.downloads_index)

    @Slot()
    def _on_shortcut_activated_store(self):
        self.setCurrentIndex(self.store_index)

    @Slot()
    def _on_shortcut_activated_integrations(self):
        self.setCurrentIndex(self.integrations_index)

    @Slot()
    def _on_shortcut_activated_settings(self):
        self.setCurrentIndex(self.settings_index)

    @Slot()
    def _on_update_available(self):
        self.setTabText(self.settings_index, self.tr('Settings (!)'))

    @Slot()
    @Slot(str)
    def show_import(self, app_name: str | None = None):
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
        suffix = '' if not num_downloads else f' ({num_downloads})'
        self.setTabText(self.downloads_index, self.tr('Downloads') + suffix)

    @Slot(int)
    def mouse_clicked(self, index):
        if index == self.games_index:
            self.games_tab.show_library()
        if index == self.integrations_index:
            self.integrations_tab.show_import()

    def resizeEvent(self, event):
        self.navigation_bar.setMinimumHeight(self.height() - 1)
        super(MainTabWidget, self).resizeEvent(event)

    @Slot(int)
    def _on_exit_app(self, exit_code: int):
        # FIXME: Don't allow logging out if there are active downloads
        if self.downloads_tab.is_download_active:
            QMessageBox.warning(
                self,
                self.tr('Quit') if exit_code == ExitCodes.EXIT else self.tr('Logout'),
                self.tr('There are active downloads. Stop them before trying to quit.'),
            )
            return
        # FIXME: End of FIXME
        if exit_code == ExitCodes.LOGOUT:
            reply = QMessageBox.question(
                self,
                self.tr('Logout'),
                self.tr('Do you really want to logout <b>{}</b>?').format(self.core.lgd.userdata.get('display_name')),
                buttons=(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No),
                defaultButton=QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.core.lgd.invalidate_userdata()
            else:
                return
        self.exit_app.emit(exit_code)  # restart exit code
