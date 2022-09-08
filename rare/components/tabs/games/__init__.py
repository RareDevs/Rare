from logging import getLogger
from typing import Tuple, Dict, Union, List, Set

from PyQt5.QtCore import QSettings, Qt, pyqtSlot
from PyQt5.QtWidgets import QStackedWidget, QVBoxLayout, QWidget, QScrollArea, QFrame
from legendary.models.game import InstalledGame, Game

from rare.shared import (
    LegendaryCoreSingleton,
    GlobalSignalsSingleton,
    ArgumentsSingleton,
    ApiResultsSingleton,
    ImageManagerSingleton,
)
from rare.widgets.library_layout import LibraryLayout
from rare.widgets.sliding_stack import SlidingStackedWidget
from .cloud_save_utils import CloudSaveUtils
from .game_info import GameInfoTabs
from .game_info.uninstalled_info import UninstalledInfoTabs
from .game_utils import GameUtils
from .game_widgets.base_installed_widget import BaseInstalledWidget
from .game_widgets.base_uninstalled_widget import BaseUninstalledWidget
from .game_widgets.installed_icon_widget import InstalledIconWidget
from .game_widgets.installed_list_widget import InstalledListWidget
from .game_widgets.installing_game_widget import InstallingGameWidget
from .game_widgets.uninstalled_icon_widget import UninstalledIconWidget
from .game_widgets.uninstalled_list_widget import UninstalledListWidget
from .head_bar import GameListHeadBar
from .import_sync import ImportSyncTabs

logger = getLogger("GamesTab")


class GamesTab(QStackedWidget):
    def __init__(self, parent=None):
        super(GamesTab, self).__init__(parent=parent)
        self.core = LegendaryCoreSingleton()
        self.signals = GlobalSignalsSingleton()
        self.args = ArgumentsSingleton()
        self.api_results = ApiResultsSingleton()
        self.image_manager = ImageManagerSingleton()
        self.settings = QSettings()

        self.widgets: Dict[str, Tuple[
            Union[InstalledIconWidget, UninstalledIconWidget], Union[InstalledListWidget, UninstalledListWidget]]] = {}
        self.updates: Set = set()
        self.active_filter: int = 0
        self.uninstalled_games: List[Game] = []

        self.game_list: List[Game] = self.api_results.game_list
        self.dlcs = self.api_results.dlcs
        self.bit32 = self.api_results.bit32_games
        self.mac_games = self.api_results.mac_games
        self.no_assets = self.api_results.no_asset_games

        self.game_utils = GameUtils(parent=self)

        self.games = QWidget(parent=self)
        self.games.setLayout(QVBoxLayout())
        self.addWidget(self.games)

        self.head_bar = GameListHeadBar(parent=self.games)
        self.head_bar.import_clicked.connect(self.show_import)
        self.head_bar.egl_sync_clicked.connect(self.show_egl_sync)
        self.games.layout().addWidget(self.head_bar)

        self.game_info_tabs = GameInfoTabs(self.dlcs, self.game_utils, self)
        self.game_info_tabs.back_clicked.connect(lambda: self.setCurrentWidget(self.games))
        self.addWidget(self.game_info_tabs)

        self.game_info_tabs.info.verification_finished.connect(
            self.verification_finished
        )
        self.game_info_tabs.info.uninstalled.connect(lambda x: self.setCurrentWidget(self.games))

        self.import_sync_tabs = ImportSyncTabs(self)
        self.import_sync_tabs.back_clicked.connect(lambda: self.setCurrentWidget(self.games))
        self.addWidget(self.import_sync_tabs)

        for i in self.game_list:
            if i.app_name.startswith("UE_4"):
                pixmap = self.image_manager.get_pixmap(i.app_name)
                if pixmap.isNull():
                    continue
                self.ue_name = i.app_name
                logger.debug(f"Found Unreal AppName {self.ue_name}")
                break
        else:
            logger.warning("No Unreal engine in library found")
            self.ue_name = ""

        self.uninstalled_info_tabs = UninstalledInfoTabs(self)
        self.uninstalled_info_tabs.back_clicked.connect(lambda: self.setCurrentWidget(self.games))
        self.addWidget(self.uninstalled_info_tabs)

        self.no_asset_names = []
        if not self.args.offline:
            for game in self.no_assets:
                self.no_asset_names.append(game.app_name)
        else:
            self.no_assets = []

        self.installed = self.core.get_installed_list()

        self.view_stack = SlidingStackedWidget(self.games)
        self.view_stack.setFrameStyle(QFrame.NoFrame)
        self.icon_view_scroll = QScrollArea(self.view_stack)
        self.icon_view_scroll.setWidgetResizable(True)
        self.icon_view_scroll.setFrameShape(QFrame.StyledPanel)
        self.icon_view_scroll.horizontalScrollBar().setDisabled(True)
        self.list_view_scroll = QScrollArea(self.view_stack)
        self.list_view_scroll.setWidgetResizable(True)
        self.list_view_scroll.setFrameShape(QFrame.StyledPanel)
        self.list_view_scroll.horizontalScrollBar().setDisabled(True)
        self.icon_view = QWidget(self.icon_view_scroll)
        self.icon_view.setLayout(LibraryLayout(self.icon_view))
        self.icon_view.layout().setContentsMargins(0, 13, 0, 0)
        self.icon_view.layout().setAlignment(Qt.AlignTop)
        self.list_view = QWidget(self.list_view_scroll)
        self.list_view.setLayout(QVBoxLayout(self.list_view))
        self.list_view.layout().setContentsMargins(3, 3, 9, 3)
        self.list_view.layout().setAlignment(Qt.AlignTop)
        self.icon_view_scroll.setWidget(self.icon_view)
        self.list_view_scroll.setWidget(self.list_view)
        self.view_stack.addWidget(self.icon_view_scroll)
        self.view_stack.addWidget(self.list_view_scroll)
        self.games.layout().addWidget(self.view_stack)

        # add installing game widget for icon view: List view not supported
        self.installing_widget = InstallingGameWidget()
        self.icon_view.layout().addWidget(self.installing_widget)
        self.installing_widget.setVisible(False)

        if not self.settings.value("icon_view", True, bool):
            self.view_stack.setCurrentWidget(self.list_view_scroll)
            self.head_bar.view.list()
        else:
            self.view_stack.setCurrentWidget(self.icon_view_scroll)

        self.head_bar.search_bar.textChanged.connect(lambda x: self.filter_games("", x))
        self.head_bar.search_bar.textChanged.connect(
            lambda x: self.icon_view_scroll.verticalScrollBar().setSliderPosition(
                self.icon_view_scroll.verticalScrollBar().minimum()
            )
        )
        self.head_bar.search_bar.textChanged.connect(
            lambda x: self.list_view_scroll.verticalScrollBar().setSliderPosition(
                self.list_view_scroll.verticalScrollBar().minimum()
            )
        )
        self.head_bar.filterChanged.connect(self.filter_games)
        self.head_bar.refresh_list.clicked.connect(self.update_list)
        self.head_bar.view.toggled.connect(self.toggle_view)

        f = self.settings.value("filter", 0, int)
        if f >= len(self.head_bar.available_filters):
            f = 0
        self.active_filter = self.head_bar.available_filters[f]

        # signals
        self.signals.dl_progress.connect(self.installing_widget.set_status)
        self.signals.installation_started.connect(self.installation_started)
        self.signals.update_gamelist.connect(self.update_list)
        self.signals.installation_finished.connect(
            self.installation_finished
        )
        self.signals.game_uninstalled.connect(lambda name: self.update_list([name]))

        self.game_utils.update_list.connect(self.update_list)

        self.setup_game_list()

    def installation_finished(self, app_name: str):
        self.installing_widget.setVisible(False)
        self.installing_widget.set_game("")
        self.filter_games("")

    def installation_started(self, app_name: str):
        self.installing_widget.set_game(app_name)

        i_widget, l_widget = self.widgets.get(app_name, (None, None))
        if not i_widget or not l_widget:
            return
        i_widget.setVisible(False)
        l_widget.setVisible(False)

    def verification_finished(self, igame: InstalledGame):
        # only if igame needs verification
        i_widget, l_widget = self.widgets[igame.app_name]
        i_widget.igame = igame
        l_widget.igame = igame

        i_widget.leaveEvent(None)
        l_widget.update_text()

    def show_import(self):
        self.setCurrentWidget(self.import_sync_tabs)
        self.import_sync_tabs.show_import()

    def show_egl_sync(self, idx):
        self.setCurrentWidget(self.import_sync_tabs)
        self.import_sync_tabs.show_egl_sync()

    def show_game_info(self, app_name):
        self.game_info_tabs.update_game(app_name)
        self.setCurrentWidget(self.game_info_tabs)

    def show_uninstalled_info(self, game):
        self.uninstalled_info_tabs.update_game(game)
        self.setCurrentWidget(self.uninstalled_info_tabs)

    @pyqtSlot()
    def update_count_games_label(self):
        self.head_bar.set_games_count(len(self.core.get_installed_list()), len(self.game_list))

    def setup_game_list(self):
        self.update_count_games_label()

        # add installed games
        for igame in sorted(self.core.get_installed_list(), key=lambda x: x.title):
            icon_widget, list_widget = self.add_installed_widget(igame.app_name)
            self.icon_view.layout().addWidget(icon_widget)
            self.list_view.layout().addWidget(list_widget)

        for game in self.no_assets:
            if not game.metadata.get("customAttributes", {}).get("ThirdPartyManagedApp", {}).get("value") == "Origin":
                icon_widget, list_widget = self.add_uninstalled_widget(game)
            else:
                icon_widget, list_widget = self.add_installed_widget(game.app_name)
            if not icon_widget or not list_widget:
                logger.warning(f"Ignoring {game.app_name} in game list")
                continue
            self.icon_view.layout().addWidget(icon_widget)
            self.list_view.layout().addWidget(list_widget)

        for game in sorted(self.game_list, key=lambda x: x.app_title):
            if not self.core.is_installed(game.app_name):
                self.uninstalled_games.append(game)
                icon_widget, list_widget = self.add_uninstalled_widget(game)
                self.icon_view.layout().addWidget(icon_widget)
                self.list_view.layout().addWidget(list_widget)
        self.filter_games(self.active_filter)

    def add_installed_widget(self, app_name):
        pixmap = self.image_manager.get_pixmap(app_name)
        try:
            if pixmap.isNull():
                logger.info(f"{app_name} has a corrupt image.")
                if app_name in self.no_asset_names and self.core.get_asset(app_name).namespace != "ue":
                    self.image_manager.download_image_blocking(self.core.get_game(app_name), force=True)
                    pixmap = self.image_manager.get_pixmap(app_name)
                elif self.ue_name:
                    pixmap = self.image_manager.get_pixmap(self.ue_name)

            icon_widget = InstalledIconWidget(app_name, pixmap, self.game_utils)
            list_widget = InstalledListWidget(app_name, pixmap, self.game_utils)
        except Exception as e:
            logger.error(f"{app_name} is broken. Don't add it to game list: {e}")
            return None, None

        self.widgets[app_name] = (icon_widget, list_widget)

        icon_widget.show_info.connect(self.show_game_info)
        list_widget.show_info.connect(self.show_game_info)

        if icon_widget.update_available:
            self.updates.add(app_name)
        return icon_widget, list_widget

    def add_uninstalled_widget(self, game):
        pixmap = self.image_manager.get_pixmap(game.app_name, color=False)
        try:
            if pixmap.isNull():
                if self.core.get_asset(game.app_name).namespace != "ue":
                    logger.warning(f"{game.app_title} has a corrupt image. Reloading...")
                    self.image_manager.download_image_blocking(game, force=True)
                    pixmap = self.image_manager.get_pixmap(game.app_name, color=False)
                elif self.ue_name:
                    pixmap = self.image_manager.get_pixmap(self.ue_name, color=False)

            icon_widget = UninstalledIconWidget(game, self.core, pixmap)
            list_widget = UninstalledListWidget(self.core, game, pixmap)
        except Exception as e:
            logger.error(f"{game.app_name} is broken. Don't add it to game list: {e}")
            return None, None

        icon_widget.show_uninstalled_info.connect(self.show_uninstalled_info)
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

        def get_visibility(widget) -> Tuple[bool, float]:
            app_name = widget.game.app_name

            if not isinstance(widget,
                              InstallingGameWidget) and self.installing_widget.game and self.installing_widget.game.app_name == app_name:
                visible = False
            elif filter_name == "installed":
                visible = self.core.is_installed(app_name)
            elif filter_name == "offline":
                if self.core.is_installed(app_name) and not isinstance(widget, InstallingGameWidget):
                    visible = widget.igame.can_run_offline
                else:
                    visible = False
            elif filter_name == "32bit" and self.bit32:
                visible = app_name in self.bit32
            elif filter_name == "mac" and self.mac_games:
                visible = app_name in self.mac_games
            elif filter_name == "installable":
                visible = app_name not in self.no_asset_names
            elif filter_name == "include_ue":
                visible = True
            elif filter_name == "all":
                # All visible except ue
                try:
                    visible = self.core.get_asset(app_name, update=False).namespace != "ue"
                except ValueError:
                    visible = True
            else:
                visible = True

            if (
                    search_text.lower() not in widget.game.app_name.lower()
                    and search_text.lower() not in widget.game.app_title.lower()
            ):
                opacity = 0.25
            else:
                opacity = 1.0
            return visible, opacity

        for t in self.widgets.values():
            visible, opacity = get_visibility(t[0])
            for w in t:
                w.setVisible(visible)
                w.image.setOpacity(opacity)

        self.sort_list(search_text)

        if self.installing_widget.game:
            self.installing_widget.setVisible(get_visibility(self.installing_widget)[0])

    @pyqtSlot()
    def sort_list(self, sort_by: str = ""):
        # lk: this is the existing sorting implemenation
        # lk: it sorts by installed then by title
        installing_widget = self.icon_view.layout().remove(type(self.installing_widget).__name__)
        if sort_by:
            self.icon_view.layout().sort(lambda x: (sort_by.lower() not in x.widget().game.app_title.lower(),))
        else:
            self.icon_view.layout().sort(
                lambda x: (
                    not x.widget().is_installed,
                    x.widget().is_non_asset,
                    x.widget().app_title,
                )
            )
        self.icon_view.layout().insert(0, installing_widget)
        list_widgets = self.list_view.findChildren(InstalledListWidget) + self.list_view.findChildren(
            UninstalledListWidget)
        if sort_by:
            list_widgets.sort(key=lambda x: (sort_by not in x.game.app_title.lower(),))
        else:
            list_widgets.sort(
                key=lambda x: (not x.is_installed, x.is_non_asset, x.app_title)
            )
        for idx, wl in enumerate(list_widgets):
            self.list_view.layout().insertWidget(idx, wl)

    def __remove_from_layout(self, app_name):
        self.icon_view.layout().removeWidget(self.widgets[app_name][0])
        self.list_view.layout().removeWidget(self.widgets[app_name][1])
        self.widgets[app_name][0].deleteLater()
        self.widgets[app_name][1].deleteLater()
        self.widgets.pop(app_name)

    def __update_installed(self, app_name):
        self.__remove_from_layout(app_name)
        icon_widget, list_widget = self.add_installed_widget(app_name)
        self.icon_view.layout().addWidget(icon_widget)
        self.list_view.layout().addWidget(list_widget)

    def __update_uninstalled(self, app_name):
        self.__remove_from_layout(app_name)
        game = self.core.get_game(app_name, False)
        try:
            icon_widget, list_widget = self.add_uninstalled_widget(game)
            self.icon_view.layout().addWidget(icon_widget)
            self.list_view.layout().addWidget(list_widget)
        except Exception:
            pass

    def update_list(self, app_names: list = None):
        logger.debug(f"Updating list for {app_names}")
        if app_names:
            update_list = False
            for app_name in app_names:
                if widgets := self.widgets.get(app_name):

                    # from update
                    if self.core.is_installed(widgets[0].game.app_name) and isinstance(
                            widgets[0], BaseInstalledWidget
                    ):
                        logger.debug(f"Update Gamelist: Updated: {app_name}")
                        igame = self.core.get_installed_game(app_name)
                        for w in widgets:
                            w.igame = igame
                            w.update_available = (
                                    self.core.get_asset(
                                        w.game.app_name, w.igame.platform, False
                                    ).build_version
                                    != igame.version
                            )
                        widgets[0].leaveEvent(None)
                    # new installed
                    elif self.core.is_installed(app_name) and isinstance(
                            widgets[0], BaseUninstalledWidget
                    ):
                        logger.debug(f"Update Gamelist: New installed {app_name}")
                        self.__update_installed(app_name)
                        update_list = True

                    # uninstalled
                    elif not self.core.is_installed(
                            widgets[0].game.app_name
                    ) and isinstance(widgets[0], BaseInstalledWidget):
                        logger.debug(f"Update list: Uninstalled: {app_name}")
                        self.__update_uninstalled(app_name)
                        update_list = True

            # do not update, if only update finished
            if update_list:
                self.sort_list()

        else:
            installed_names = [i.app_name for i in self.core.get_installed_list()]
            # get Uninstalled games
            uninstalled_names = []
            games = self.core.get_game_list(True)
            for game in sorted(games, key=lambda x: x.app_title):
                if not game.app_name in installed_names:
                    uninstalled_names.append(game.app_name)

            new_installed_games = list(
                set(installed_names) - set([i.app_name for i in self.installed])
            )
            new_uninstalled_games = list(
                set(uninstalled_names)
                - set([i.app_name for i in self.uninstalled_games])
            )

            if (not new_uninstalled_games) and (not new_installed_games):
                return

            if new_installed_games:
                for name in new_installed_games:
                    self.__update_installed(name)

                for name in new_uninstalled_games:
                    self.__update_uninstalled(name)

                self.sort_list()
        self.update_count_games_label()

    def toggle_view(self):
        self.settings.setValue("icon_view", not self.head_bar.view.isChecked())

        if not self.head_bar.view.isChecked():
            self.view_stack.slideInWidget(self.icon_view_scroll)
        else:
            self.view_stack.slideInWidget(self.list_view_scroll)
