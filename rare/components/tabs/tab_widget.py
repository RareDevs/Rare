from PyQt5.QtCore import QSize, pyqtSignal
from PyQt5.QtWidgets import QMenu, QTabWidget, QWidget, QWidgetAction, QShortcut
from qtawesome import icon

from legendary.core import LegendaryCore
from rare.components.tabs.account import MiniWidget
from rare.components.tabs.cloud_saves import SyncSaves
from rare.components.tabs.downloads import DownloadTab
from rare.components.tabs.games import GamesTab
from rare.components.tabs.settings import SettingsTab
from rare.components.tabs.settings.debug_settings import DebugSettings
from rare.components.tabs.shop import Shop
from rare.components.tabs.tab_utils import TabBar, TabButtonWidget
from rare.utils.models import Signals


class TabWidget(QTabWidget):
    delete_presence = pyqtSignal()

    def __init__(self, core: LegendaryCore, signals: Signals, parent, args, api_results):
        super(TabWidget, self).__init__(parent=parent)
        self.offline = args.offline
        disabled_tab = 4 if not self.offline else 1
        self.core = core
        self.signals = signals
        self.setTabBar(TabBar(disabled_tab))
        # Generate Tabs
        self.games_tab = GamesTab(core, args.offline, self.signals, api_results)
        self.addTab(self.games_tab, self.tr("Games"))
        self.signals.tab_widget.connect(lambda x: self.handle_signal(*x))
        if not self.offline:
            # updates = self.games_tab.default_widget.game_list.updates
            self.downloadTab = DownloadTab(core, [], self.signals)
            self.addTab(self.downloadTab, "Downloads" + (" (" + str(len([])) + ")" if len([]) != 0 else ""))
            self.cloud_saves = SyncSaves(core, self.signals)
            self.addTab(self.cloud_saves, "Cloud Saves")
            self.store = Shop(self.core)
            self.addTab(self.store, self.tr("Store (Beta)"))
        self.settings = SettingsTab(core, self)

        if args.debug:
            self.settings.addTab(DebugSettings(), "Debug")

        # Space Tab
        self.addTab(QWidget(), "")
        self.setTabEnabled(disabled_tab, False)
        # Button
        self.account = QWidget()
        self.addTab(self.account, "")
        self.setTabEnabled(disabled_tab + 1, False)

        self.mini_widget = MiniWidget(core, self.signals)
        account_action = QWidgetAction(self)
        account_action.setDefaultWidget(self.mini_widget)
        account_button = TabButtonWidget(core, 'mdi.account-circle', 'Account')
        account_button.setMenu(QMenu())
        account_button.menu().addAction(account_action)
        self.tabBar().setTabButton(disabled_tab + 1, self.tabBar().RightSide, account_button)

        self.addTab(self.settings, icon("fa.gear"),
                    "(!)" if self.settings.about.update_available else "")

        # Signals
        # imported
        self.games_tab.import_widget.update_list.connect(self.game_imported)

        if not self.offline:
            # Finished sync
            self.cloud_saves.finished.connect(self.finished_sync)
        # Game finished
        self.games_tab.game_exited.connect(self.game_finished)

        # Open game list on click on Games tab button
        self.tabBarClicked.connect(self.mouse_clicked)
        self.setIconSize(QSize(25, 25))

        # shortcuts
        QShortcut("Alt+1", self).activated.connect(lambda: self.setCurrentIndex(0))
        QShortcut("Alt+2", self).activated.connect(lambda: self.setCurrentIndex(1))
        QShortcut("Alt+3", self).activated.connect(lambda: self.setCurrentIndex(2))
        QShortcut("Alt+4", self).activated.connect(lambda: self.setCurrentIndex(5))

    def handle_signal(self, action, data):
        if action == self.signals.actions.set_index:
            self.setCurrentIndex(data)
        if action == self.signals.actions.set_dl_tab_text:
            self.setTabText(1, "Downloads" + ((" (" + str(data) + ")") if data != 0 else ""))

    def mouse_clicked(self, tab_num):
        if tab_num == 0:
            self.games_tab.layout().setCurrentIndex(0)

        if not self.offline and tab_num == 3:
            self.store.load()

    def game_imported(self, app_name: str):
        igame = self.core.get_installed_game(app_name)
        if self.core.get_asset(app_name, False).build_version != igame.version:
            self.downloadTab.add_update(igame)
            downloads = len(self.downloadTab.dl_queue) + len(self.downloadTab.update_widgets.keys())
            self.setTabText(1, "Downloads" + ((" (" + str(downloads) + ")") if downloads != 0 else ""))
        self.games_tab.update_list(app_name)
        self.games_tab.setCurrentIndex(0)

    # Sync game and delete dc rpc
    def game_finished(self, app_name):
        self.delete_presence.emit()
        game = self.core.get_game(app_name)
        if game and game.supports_cloud_saves:
            self.cloud_saves.sync_game(app_name, True)

    def resizeEvent(self, event):
        self.tabBar().setMinimumWidth(self.width())
        super(TabWidget, self).resizeEvent(event)

    # Remove text "sync game"
    def finished_sync(self, app_name):
        if self.core.is_installed(app_name):
            self.games_tab.widgets[app_name][0].info_text = ""
            self.games_tab.widgets[app_name][0].info_label.setText("")
            self.games_tab.widgets[app_name][1].info_label.setText("")
