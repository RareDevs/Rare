import webbrowser

from PyQt5.QtCore import QSize, pyqtSignal
from PyQt5.QtWidgets import QMenu, QTabWidget, QWidget, QWidgetAction
from qtawesome import icon

from custom_legendary.core import LegendaryCore
from rare.components.tab_utils import TabBar, TabButtonWidget
from rare.components.tabs.account import MiniWidget
from rare.components.tabs.cloud_saves import SyncSaves
from rare.components.tabs.downloads.__init__ import DownloadTab
from rare.components.tabs.games import GameTab
from rare.components.tabs.settings import SettingsTab
from rare.utils.models import InstallOptions


class TabWidget(QTabWidget):
    delete_presence = pyqtSignal()

    def __init__(self, core: LegendaryCore, parent, offline):
        super(TabWidget, self).__init__(parent=parent)
        disabled_tab = 3 if not offline else 1
        self.core = core
        self.setTabBar(TabBar(disabled_tab))

        # Generate Tabs
        self.games_tab = GameTab(core, self, offline)
        self.addTab(self.games_tab, self.tr("Games"))

        if not offline:
            updates = self.games_tab.default_widget.game_list.updates
            self.downloadTab = DownloadTab(core, updates, self)
            self.addTab(self.downloadTab, "Downloads" + (" (" + str(len(updates)) + ")" if len(updates) != 0 else ""))

            self.cloud_saves = SyncSaves(core, self)
            self.addTab(self.cloud_saves, "Cloud Saves")

        self.settings = SettingsTab(core, self)

        # Space Tab
        self.addTab(QWidget(), "")
        self.setTabEnabled(disabled_tab, False)
        # Buttons
        store_button = TabButtonWidget(core, 'fa.shopping-cart', 'Epic Games Store')
        store_button.pressed.connect(lambda: webbrowser.open("https://www.epicgames.com/store"))
        self.tabBar().setTabButton(disabled_tab, self.tabBar().RightSide, store_button)

        self.account = QWidget()
        self.addTab(self.account, "")
        self.setTabEnabled(disabled_tab + 1, False)

        account_action = QWidgetAction(self)
        account_action.setDefaultWidget(MiniWidget(core))
        account_button = TabButtonWidget(core, 'mdi.account-circle', 'Account')
        account_button.setMenu(QMenu())
        account_button.menu().addAction(account_action)
        self.tabBar().setTabButton(disabled_tab + 1, self.tabBar().RightSide, account_button)

        self.addTab(self.settings, icon("fa.gear", color='white'),
                    "(!)" if self.settings.about.update_available else "")

        # Signals
        # open download tab
        self.games_tab.default_widget.game_list.update_game.connect(lambda: self.setCurrentIndex(1))

        if not offline:
            # Download finished
            self.downloadTab.finished.connect(self.dl_finished)
            # start download
            self.games_tab.default_widget.game_list.install_game.connect(self.start_download)
            # install dlc
            self.games_tab.game_info.dlc_tab.install_dlc.connect(self.start_download)

            # repair game
            self.games_tab.game_info.info.verify_game.connect(lambda app_name: self.downloadTab.install_game(
                InstallOptions(app_name, core.get_installed_game(app_name).install_path, repair=True)))

            # Finished sync
            self.cloud_saves.finished.connect(self.finished_sync)
        # Game finished
        self.games_tab.default_widget.game_list.game_exited.connect(self.game_finished)

        # Open game list on click on Games tab button
        self.tabBarClicked.connect(lambda x: self.games_tab.layout.setCurrentIndex(0) if x == 0 else None)
        self.setIconSize(QSize(25, 25))

    # Sync game and delete dc rpc
    def game_finished(self, app_name):
        self.delete_presence.emit()
        if self.core.get_game(app_name).supports_cloud_saves:
            self.cloud_saves.sync_game(app_name, True)

    # Update gamelist and set text of Downlaods to "Downloads"
    def dl_finished(self, update_list):
        if update_list:
            self.games_tab.default_widget.game_list.update_list()
        downloads = len(self.downloadTab.dl_queue) + len(self.downloadTab.update_widgets.keys())
        self.setTabText(1, "Downloads" + ((" (" + str(downloads) + ")") if downloads != 0 else ""))

    def start_download(self, options):
        downloads = len(self.downloadTab.dl_queue) + len(self.downloadTab.update_widgets.keys()) + 1
        self.setTabText(1, "Downloads" + ((" (" + str(downloads) + ")") if downloads != 0 else ""))
        self.downloadTab.install_game(options)

    def resizeEvent(self, event):
        self.tabBar().setMinimumWidth(self.width())
        super(TabWidget, self).resizeEvent(event)

    # Remove text "sync game"
    def finished_sync(self, app_name):
        self.games_tab.default_widget.game_list.widgets[app_name][0].info_text = ""
        self.games_tab.default_widget.game_list.widgets[app_name][0].info_label.setText("")
        self.games_tab.default_widget.game_list.widgets[app_name][1].info_label.setText("")
