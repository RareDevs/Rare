import webbrowser

from PyQt5.QtCore import QSize, pyqtSignal
from PyQt5.QtWidgets import QMenu, QTabWidget, QWidget, QWidgetAction, QShortcut
from qtawesome import icon

from custom_legendary.core import LegendaryCore
from rare.components.dialogs.install_dialog import InstallDialog
from rare.components.dialogs.uninstall_dialog import UninstallDialog
from rare.components.tab_utils import TabBar, TabButtonWidget
from rare.components.tabs.account import MiniWidget
from rare.components.tabs.cloud_saves import SyncSaves
from rare.components.tabs.downloads import DownloadTab
from rare.components.tabs.games import GameTab
from rare.components.tabs.settings import SettingsTab
from rare.utils import legendary_utils
from rare.utils.models import InstallQueueItemModel, InstallOptionsModel


class TabWidget(QTabWidget):
    quit_app = pyqtSignal(int)
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

        self.mini_widget = MiniWidget(core)
        self.mini_widget.quit_app.connect(self.quit_app.emit)
        account_action = QWidgetAction(self)
        account_action.setDefaultWidget(self.mini_widget)
        account_button = TabButtonWidget(core, 'mdi.account-circle', 'Account')
        account_button.setMenu(QMenu())
        account_button.menu().addAction(account_action)
        self.tabBar().setTabButton(disabled_tab + 1, self.tabBar().RightSide, account_button)

        self.addTab(self.settings, icon("fa.gear"),
                    "(!)" if self.settings.about.update_available else "")

        # Signals
        # open download tab
        self.games_tab.default_widget.game_list.update_game.connect(lambda: self.setCurrentIndex(1))

        # uninstall
        self.games_tab.game_info.info.uninstall_game.connect(self.uninstall_game)

        # imported
        self.games_tab.import_widget.update_list.connect(self.game_imported)

        if not offline:
            # Download finished
            self.downloadTab.finished.connect(self.dl_finished)
            # show uninstalled info
            self.games_tab.default_widget.game_list.show_uninstalled_info.connect(self.games_tab.show_uninstalled)
            # install dlc
            self.games_tab.game_info.dlc_tab.install_dlc.connect(
                lambda app_name, update: self.install_game(
                    InstallOptionsModel(app_name=app_name),
                    update=update))

            # install game
            self.games_tab.uninstalled_info_widget.info.install_game.connect(
                lambda app_name: self.install_game(
                    InstallOptionsModel(app_name=app_name)))
            # repair game
            self.games_tab.game_info.info.verify_game.connect(
                lambda app_name: self.install_game(
                    InstallOptionsModel(app_name=app_name,
                                        base_path=core.get_installed_game(app_name).install_path,
                                        repair=True),
                    silent=True)
            )

            # Finished sync
            self.cloud_saves.finished.connect(self.finished_sync)
        # Game finished
        self.games_tab.default_widget.game_list.game_exited.connect(self.game_finished)

        # Open game list on click on Games tab button
        self.tabBarClicked.connect(lambda x: self.games_tab.layout.setCurrentIndex(0) if x == 0 else None)
        self.setIconSize(QSize(25, 25))

        # shortcuts
        QShortcut("Alt+1", self).activated.connect(lambda: self.setCurrentIndex(0))
        QShortcut("Alt+2", self).activated.connect(lambda: self.setCurrentIndex(1))
        QShortcut("Alt+3", self).activated.connect(lambda: self.setCurrentIndex(2))
        QShortcut("Alt+4", self).activated.connect(lambda: self.setCurrentIndex(5))

        self.downloadTab.dl_status.connect(
            self.games_tab.default_widget.game_list.installing_widget.image_widget.set_status)

    # TODO; maybe pass InstallOptionsModel only, not split arguments
    def install_game(self, options: InstallOptionsModel, update=False, silent=False):
        install_dialog = InstallDialog(self.core,
                                       InstallQueueItemModel(options=options),
                                       update=update, silent=silent, parent=self)
        install_dialog.result_ready.connect(self.on_install_dialog_closed)
        install_dialog.execute()

    def on_install_dialog_closed(self, download_item: InstallQueueItemModel):
        if download_item:
            self.setCurrentIndex(1)
            self.start_download(download_item)

    def start_download(self, download_item: InstallQueueItemModel):
        downloads = len(self.downloadTab.dl_queue) + len(self.downloadTab.update_widgets.keys()) + 1
        self.setTabText(1, "Downloads" + ((" (" + str(downloads) + ")") if downloads != 0 else ""))
        self.setCurrentIndex(1)
        self.downloadTab.install_game(download_item)
        self.games_tab.default_widget.game_list.start_download(download_item.options.app_name)

    def game_imported(self, app_name: str):
        igame = self.core.get_installed_game(app_name)
        if self.core.get_asset(app_name, True).build_version != igame.version:
            self.downloadTab.add_update(igame)
            downloads = len(self.downloadTab.dl_queue) + len(self.downloadTab.update_widgets.keys())
            self.setTabText(1, "Downloads" + ((" (" + str(downloads) + ")") if downloads != 0 else ""))
        self.games_tab.default_widget.game_list.update_list(app_name)
        self.games_tab.layout.setCurrentIndex(0)

    # Sync game and delete dc rpc
    def game_finished(self, app_name):
        self.delete_presence.emit()
        if self.core.get_game(app_name).supports_cloud_saves:
            self.cloud_saves.sync_game(app_name, True)

    def uninstall_game(self, app_name):
        game = self.core.get_game(app_name)
        infos = UninstallDialog(game).get_information()
        if infos == 0:
            return
        legendary_utils.uninstall(game.app_name, self.core, infos)
        if app_name in self.downloadTab.update_widgets.keys():
            self.downloadTab.update_layout.removeWidget(self.downloadTab.update_widgets[app_name])
            self.downloadTab.update_widgets.pop(app_name)
            downloads = len(self.downloadTab.dl_queue) + len(self.downloadTab.update_widgets.keys())
            self.setTabText(1, "Downloads" + ((" (" + str(downloads) + ")") if downloads != 0 else ""))
            self.downloadTab.update_text.setVisible(len(self.downloadTab.update_widgets) == 0)

    # Update gamelist and set text of Downlaods to "Downloads"

    def dl_finished(self, update_list):
        if update_list[0]:
            self.games_tab.default_widget.game_list.update_list(update_list[1])
            self.cloud_saves.reload(update_list[1])
        self.games_tab.default_widget.game_list.installing_widget.setVisible(False)
        downloads = len(self.downloadTab.dl_queue) + len(self.downloadTab.update_widgets.keys())
        self.setTabText(1, "Downloads" + ((" (" + str(downloads) + ")") if downloads != 0 else ""))

    def resizeEvent(self, event):
        self.tabBar().setMinimumWidth(self.width())
        super(TabWidget, self).resizeEvent(event)

    # Remove text "sync game"
    def finished_sync(self, app_name):
        self.games_tab.default_widget.game_list.widgets[app_name][0].info_text = ""
        self.games_tab.default_widget.game_list.widgets[app_name][0].info_label.setText("")
        self.games_tab.default_widget.game_list.widgets[app_name][1].info_label.setText("")
