from PyQt5.QtCore import QSize, pyqtSignal
from PyQt5.QtWidgets import QMenu, QTabWidget, QWidget, QWidgetAction, QShortcut
from qtawesome import icon

from rare import shared
from rare.components.tabs.account import MiniWidget
from rare.components.tabs.cloud_saves import SyncSaves
from rare.components.tabs.downloads import DownloadTab
from rare.components.tabs.games import GamesTab
from rare.components.tabs.settings import SettingsTab
from rare.components.tabs.settings.debug import DebugSettings
from rare.components.tabs.shop import Shop
from rare.components.tabs.tab_utils import TabBar, TabButtonWidget
from rare.utils.models import InstallOptionsModel


class TabWidget(QTabWidget):
    delete_presence = pyqtSignal()

    def __init__(self, parent):
        super(TabWidget, self).__init__(parent=parent)
        disabled_tab = 4 if not shared.args.offline else 1
        self.core = shared.core
        self.signals = shared.signals
        self.setTabBar(TabBar(disabled_tab))
        # Generate Tabs
        self.games_tab = GamesTab()
        self.addTab(self.games_tab, self.tr("Games"))

        if not shared.args.offline:
            # updates = self.games_tab.default_widget.game_list.updates
            self.downloadTab = DownloadTab(self.games_tab.updates)
            self.addTab(self.downloadTab, "Downloads" + (
                " (" + str(len(self.games_tab.updates)) + ")" if len(self.games_tab.updates) != 0 else ""))
            self.cloud_saves = SyncSaves()
            self.addTab(self.cloud_saves, "Cloud Saves")
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

        self.addTab(self.settings, icon("fa.gear"),
                    "(!)" if self.settings.about.update_available else "")

        # Signals
        # set current index
        self.signals.set_main_tab_index.connect(self.setCurrentIndex)

        # update dl tab text
        self.signals.update_download_tab_text.connect(self.update_dl_tab_text)
        # imported
        # self.games_tab.import_widget.update_list.connect(self.game_imported)

        if not shared.args.offline:
            # install dlc
            self.games_tab.game_info_tabs.dlc.install_dlc.connect(
                lambda app_name, update: self.install_game(
                    InstallOptionsModel(app_name=app_name),
                    update=update))

            # Finished sync
            self.cloud_saves.finished.connect(self.finished_sync)
        # Game finished

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

        if not shared.args.offline and tab_num == 3:
            self.store.load()

    def game_imported(self, app_name: str):
        igame = self.core.get_installed_game(app_name)
        if self.core.get_asset(app_name, False).build_version != igame.version:
            self.downloadTab.add_update(igame)
            downloads = len(self.downloadTab.dl_queue) + len(self.downloadTab.update_widgets.keys())
            self.setTabText(1, "Downloads" + ((" (" + str(downloads) + ")") if downloads != 0 else ""))
        self.games_tab.update_list(app_name)
        self.games_tab.setCurrentIndex(0)

    def resizeEvent(self, event):
        self.tabBar().setMinimumWidth(self.width())
        super(TabWidget, self).resizeEvent(event)

    # Remove text "sync game"
    def finished_sync(self, app_name):
        if self.core.is_installed(app_name):
            self.games_tab.widgets[app_name][0].info_text = ""
            self.games_tab.widgets[app_name][0].info_label.setText("")
            self.games_tab.widgets[app_name][1].info_label.setText("")
