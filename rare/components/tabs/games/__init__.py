from logging import getLogger
from typing import Tuple, Dict

from PyQt5.QtCore import QSettings, QObjectCleanupHandler
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

import rare.shared as shared
from legendary.models.game import InstalledGame
from rare.ui.components.tabs.games.games_tab import Ui_GamesTab
from rare.utils.extra_widgets import FlowLayout
from rare.utils.utils import get_pixmap, download_image, get_uninstalled_pixmap
from .cloud_save_utils import CloudSaveUtils
from .cloud_save_utils import CloudSaveUtils
from .game_info import GameInfoTabs
from .game_info.uninstalled_info import UninstalledInfoTabs
from .game_utils import GameUtils
from .game_widgets.base_installed_widget import BaseInstalledWidget
from .game_widgets.base_uninstalled_widget import BaseUninstalledWidget
from .game_widgets.installed_icon_widget import InstalledIconWidget
from .game_widgets.installed_list_widget import InstalledListWidget
from .game_widgets.installing_game_widget import InstallingGameWidget
from .game_widgets.uninstalled_icon_widget import IconWidgetUninstalled
from .game_widgets.uninstalled_list_widget import ListWidgetUninstalled
from .head_bar import GameListHeadBar
from .import_sync import ImportSyncTabs

logger = getLogger("GamesTab")


class GamesTab(QStackedWidget, Ui_GamesTab):
    widgets: Dict[str, Tuple[InstalledIconWidget, InstalledListWidget]] = dict()
    running_games = list()
    updates = set()
    active_filter = 0

    def __init__(self, parent=None):
        super(GamesTab, self).__init__(parent=parent)
        self.setupUi(self)
        self.core = shared.core
        self.signals = shared.signals
        self.settings = QSettings()

        self.game_list = shared.api_results.game_list
        self.dlcs = shared.api_results.dlcs
        self.bit32 = shared.api_results.bit32_games
        self.mac_games = shared.api_results.mac_games
        self.no_assets = shared.api_results.no_asset_games

        self.game_utils = GameUtils(parent=self)

        self.head_bar = GameListHeadBar(self)
        self.head_bar.import_clicked.connect(self.show_import)
        self.head_bar.egl_sync_clicked.connect(self.show_egl_sync)
        self.games.layout().insertWidget(0, self.head_bar)

        self.game_info_tabs = GameInfoTabs(self.dlcs, self.game_utils, self)
        self.game_info_tabs.back_clicked.connect(lambda: self.setCurrentIndex(0))
        self.addWidget(self.game_info_tabs)

        self.game_info_tabs.info.verification_finished.connect(self.verification_finished)
        self.game_info_tabs.info.uninstalled.connect(lambda x: self.setCurrentIndex(0))

        self.import_sync_tabs = ImportSyncTabs(self)
        self.import_sync_tabs.back_clicked.connect(lambda: self.setCurrentIndex(0))
        self.addWidget(self.import_sync_tabs)

        self.uninstalled_info_tabs = UninstalledInfoTabs(self)
        self.uninstalled_info_tabs.back_clicked.connect(lambda: self.setCurrentIndex(0))
        self.addWidget(self.uninstalled_info_tabs)

        # navigation
        self.head_bar.import_game.clicked.connect(lambda: self.setCurrentIndex(2))

        self.no_asset_names = []
        if not shared.args.offline:
            for game in self.no_assets:
                self.no_asset_names.append(game.app_name)
        else:
            self.no_assets = []
        self.installed = self.core.get_installed_list()
        self.setup_game_list()

        if not self.settings.value("icon_view", True, bool):
            self.scroll_widget.layout().insertWidget(1, self.list_view)
            self.head_bar.view.list()
        else:
            self.scroll_widget.layout().insertWidget(1, self.icon_view)

        self.head_bar.search_bar.textChanged.connect(lambda x: self.filter_games("", x))
        self.head_bar.filterChanged.connect(self.filter_games)
        self.head_bar.refresh_list.clicked.connect(self.update_list)
        self.head_bar.view.toggled.connect(self.toggle_view)

        f = self.settings.value("filter", 0, int)
        if f >= len(self.head_bar.available_filters):
            f = 0
        self.active_filter = self.head_bar.available_filters[f]
        self.filter_games(self.active_filter)

        # signals
        self.signals.dl_progress.connect(self.installing_widget.set_status)
        self.signals.installation_started.connect(self.installation_started)
        self.signals.update_gamelist.connect(self.update_list)
        self.signals.installation_finished.connect(lambda x: self.installing_widget.setVisible(False))
        self.signals.game_uninstalled.connect(lambda name: self.update_list([name]))

        self.game_utils.update_list.connect(self.update_list)

        self.game_list_scroll_area.horizontalScrollBar().setDisabled(True)

    def installation_started(self, app_name: str):
        game = self.core.get_game(app_name, False)
        if game.is_dlc:
            return
        self.installing_widget.set_game(app_name)
        self.installing_widget.setVisible(True)

    def verification_finished(self, igame: InstalledGame):
        # only if igame needs verification
        i_widget, l_widget = self.widgets[igame.app_name]
        i_widget.igame = igame
        l_widget.igame = igame

        i_widget.leaveEvent(None)
        l_widget.update_text()

    def show_import(self):
        self.setCurrentIndex(2)
        self.import_sync_tabs.show_import()

    def show_egl_sync(self, idx):
        self.setCurrentIndex(2)
        self.import_sync_tabs.show_egl_sync()

    def show_game_info(self, app_name):
        self.game_info_tabs.update_game(app_name)
        self.setCurrentIndex(1)

    def show_uninstalled_info(self, game):
        self.uninstalled_info_tabs.update_game(game)
        self.setCurrentIndex(3)

    def setup_game_list(self):
        self.icon_view = QWidget()
        self.icon_view.setLayout(FlowLayout())
        self.list_view = QWidget()
        self.list_view.setLayout(QVBoxLayout())

        self.update_count_games_label()

        # add installing game widget for icon view: List view not supported
        self.installing_widget = InstallingGameWidget()
        self.icon_view.layout().addWidget(self.installing_widget)
        self.installing_widget.setVisible(False)

        # add installed games
        for igame in sorted(self.core.get_installed_list(), key=lambda x: x.title):
            icon_widget, list_widget = self.add_installed_widget(igame.app_name)
            self.icon_view.layout().addWidget(icon_widget)
            self.list_view.layout().addWidget(list_widget)

        for game in self.no_assets:
            icon_widget, list_widget = self.add_installed_widget(game.app_name)
            self.icon_view.layout().addWidget(icon_widget)
            self.list_view.layout().addWidget(list_widget)

        self.uninstalled_games = []
        for game in sorted(self.game_list, key=lambda x: x.app_title):
            if not self.core.is_installed(game.app_name):
                self.uninstalled_games.append(game)
                icon_widget, list_widget = self.add_uninstalled_widget(game)
                self.icon_view.layout().addWidget(icon_widget)
                self.list_view.layout().addWidget(list_widget)

    def update_count_games_label(self):
        self.count_games_label.setText(self.tr("Installed Games: {}    Available Games: {}").format(
            len(self.core.get_installed_list()),
            len(self.game_list)))

    def add_installed_widget(self, app_name):
        pixmap = get_pixmap(app_name)
        if pixmap.isNull():
            logger.info(app_name + " has a corrupt image.")
            download_image(self.core.get_game(app_name), force=True)
            pixmap = get_pixmap(app_name)

        icon_widget = InstalledIconWidget(app_name, pixmap, self.game_utils)

        list_widget = InstalledListWidget(app_name, pixmap, self.game_utils)

        self.widgets[app_name] = (icon_widget, list_widget)

        icon_widget.show_info.connect(self.show_game_info)
        list_widget.show_info.connect(self.show_game_info)

        if icon_widget.update_available:
            self.updates.add(app_name)

        return icon_widget, list_widget

    def add_uninstalled_widget(self, game):
        pixmap = get_uninstalled_pixmap(game.app_name)
        if pixmap.isNull():
            logger.warning(game.app_title + " has a corrupt image. Reloading...")
            download_image(game, force=True)
            pixmap = get_pixmap(game.app_name)
            img = pixmap.toImage()
            img = img.convertToFormat(QImage.Format_Grayscale8)
            pixmap = QPixmap.fromImage(img)

        icon_widget = IconWidgetUninstalled(game, self.core, pixmap)
        icon_widget.show_uninstalled_info.connect(self.show_uninstalled_info)

        list_widget = ListWidgetUninstalled(self.core, game, pixmap)
        list_widget.show_uninstalled_info.connect(self.show_uninstalled_info)

        self.widgets[game.app_name] = (icon_widget, list_widget)

        return icon_widget, list_widget

    def filter_games(self, filter_name="all", search_text: str = ""):
        if not search_text and (t := self.head_bar.search_bar.text()):
            search_text = t

        if filter_name:
            self.active_filter = filter_name
        if not filter_name and (t := self.active_filter):
            filter_name = t

        for t in self.widgets.values():
            # icon and list widget
            for w in t:
                if filter_name == "installed":
                    visible = self.core.is_installed(w.game.app_name)
                elif filter_name == "offline":
                    if self.core.is_installed(w.game.app_name):
                        visible = w.igame.can_run_offline
                    else:
                        visible = False
                elif filter_name == "32bit" and self.bit32:
                    visible = w.game.app_name in self.bit32
                elif filter_name == "mac" and self.mac_games:
                    visible = w.game.app_name in self.mac_games
                elif filter_name == "installable":
                    visible = w.game.app_name not in self.no_asset_names
                elif filter_name == "all":
                    # All visible
                    visible = True
                else:
                    visible = True
                if search_text.lower() not in w.game.app_name.lower() and search_text.lower() not in w.game.app_title.lower():
                    visible = False
                w.setVisible(visible)

    def update_list(self, app_names: list = None):
        logger.debug("Updating list for " + str(app_names))
        if app_names:
            update_list = False
            for app_name in app_names:
                if widgets := self.widgets.get(app_name):

                    # from update
                    if self.core.is_installed(widgets[0].game.app_name) and isinstance(widgets[0], BaseInstalledWidget):
                        logger.debug("Update Gamelist: Updated: " + app_name)
                        igame = self.core.get_installed_game(app_name)
                        for w in widgets:
                            w.igame = igame
                            w.update_available = self.core.get_asset(w.game.app_name, w.igame.platform,
                                                                     True).build_version != igame.version
                        widgets[0].leaveEvent(None)
                    # new installed
                    elif self.core.is_installed(app_name) and isinstance(widgets[0], BaseUninstalledWidget):
                        logger.debug("Update Gamelist: New installed " + app_name)
                        self.widgets[app_name][0].deleteLater()
                        self.widgets[app_name][1].deleteLater()
                        self.widgets.pop(app_name)

                        self.add_installed_widget(app_name)
                        update_list = True

                    # uninstalled
                    elif not self.core.is_installed(widgets[0].game.app_name) and isinstance(widgets[0],
                                                                                             BaseInstalledWidget):
                        logger.debug("Update list: Uninstalled: " + app_name)
                        self.widgets[app_name][0].deleteLater()
                        self.widgets[app_name][1].deleteLater()

                        self.widgets.pop(app_name)

                        game = self.core.get_game(app_name, False)
                        self.add_uninstalled_widget(game)
                        update_list = True

            # do not update, if only update finished
            if update_list:
                self._update_games()

        else:
            installed_names = [i.app_name for i in self.core.get_installed_list()]
            # get Uninstalled games
            uninstalled_names = []
            games = self.core.get_game_list(True)
            for game in sorted(games, key=lambda x: x.app_title):
                if not game.app_name in installed_names:
                    uninstalled_names.append(game.app_name)

            new_installed_games = list(set(installed_names) - set([i.app_name for i in self.installed]))
            new_uninstalled_games = list(set(uninstalled_names) - set([i.app_name for i in self.uninstalled_games]))

            if (not new_uninstalled_games) and (not new_installed_games):
                return

            if new_installed_games:
                for name in new_installed_games:
                    self.widgets[name][0].deleteLater()
                    self.widgets[name][1].deleteLater()
                    self.widgets.pop(name)

                    igame = self.core.get_installed_game(name)
                    self.add_installed_widget(igame.app_name)

                for name in new_uninstalled_games:
                    self.icon_view.layout().removeWidget(self.widgets[name][0])
                    self.list_view.layout().removeWidget(self.widgets[name][1])

                    self.widgets[name][0].deleteLater()
                    self.widgets[name][1].deleteLater()

                    self.widgets.pop(name)

                    game = self.core.get_game(name, False)
                    self.add_uninstalled_widget(game)

                for igame in sorted(self.core.get_installed_list(), key=lambda x: x.title):
                    i_widget, list_widget = self.widgets[igame.app_name]

                    self.icon_view.layout().addWidget(i_widget)
                    self.list_view.layout().addWidget(list_widget)
                self.installed = self.core.get_installed_list()

                for game in self.no_assets:
                    i_widget, list_widget = self.widgets[game.app_name]
                    self.icon_view.layout().addWidget(i_widget)
                    self.list_view.layout().addWidget(list_widget)

                # get Uninstalled games
                self.uninstalled_games = []
                games, self.dlcs = self.core.get_game_and_dlc_list()
                for game in sorted(games, key=lambda x: x.app_title):
                    if not self.core.is_installed(game.app_name) and game.app_name not in self.no_asset_names:
                        i_widget, list_widget = self.widgets[game.app_name]
                        self.icon_view.layout().addWidget(i_widget)
                        self.list_view.layout().addWidget(list_widget)
                        self.uninstalled_games.append(game)
        self.update_count_games_label()

    def _update_games(self):
        icon_layout = FlowLayout()
        list_layout = QVBoxLayout()

        icon_layout.addWidget(self.installing_widget)
        for igame in sorted(self.core.get_installed_list(), key=lambda x: x.title):
            i_widget, l_widget = self.widgets[igame.app_name]
            icon_layout.addWidget(i_widget)
            list_layout.addWidget(l_widget)

        for game in self.no_assets:
            i_widget, l_widget = self.widgets[game.app_name]
            icon_layout.addWidget(i_widget)
            list_layout.addWidget(l_widget)

        self.uninstalled_names = []
        installed_names = [i.app_name for i in self.core.get_installed_list()]
        # get Uninstalled games
        self.game_list, self.dlcs = self.core.get_game_and_dlc_list(update_assets=False)
        # add uninstalled games
        for game in sorted(self.game_list, key=lambda x: x.app_title):
            if game.app_name not in installed_names:
                i_widget, list_widget = self.widgets[game.app_name]
                icon_layout.addWidget(i_widget)
                list_layout.addWidget(list_widget)

        QObjectCleanupHandler().add(self.icon_view.layout())
        QObjectCleanupHandler().add(self.list_view.layout())

        self.icon_view.setLayout(icon_layout)
        self.list_view.setLayout(list_layout)

        self.icon_view.setParent(None)
        self.list_view.setParent(None)

        # insert widget in layout
        self.scroll_widget.layout().insertWidget(1,
                                                 self.icon_view if self.head_bar.view.isChecked() else self.list_view)

    def toggle_view(self):
        self.settings.setValue("icon_view", not self.head_bar.view.isChecked())

        if not self.head_bar.view.isChecked():
            self.scroll_widget.layout().replaceWidget(self.list_view, self.icon_view)
            self.list_view.setParent(None)
        else:
            self.scroll_widget.layout().replaceWidget(self.icon_view, self.list_view)
            self.icon_view.setParent(None)

        self.game_list_scroll_area.verticalScrollBar().setValue(0)
