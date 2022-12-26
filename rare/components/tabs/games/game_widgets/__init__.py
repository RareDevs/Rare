from typing import Tuple, List, Union, Optional

from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import QWidget

from rare.lgndr.core import LegendaryCore
from rare.models.game import RareGame
from rare.models.signals import GlobalSignals
from rare.shared import LegendaryCoreSingleton, GlobalSignalsSingleton, ApiResultsSingleton
from rare.shared.game_utils import GameUtils
from .icon_game_widget import IconGameWidget
from .list_game_widget import ListGameWidget


class LibraryWidgetController(QObject):
    def __init__(self, icon_container: QWidget, list_container: QWidget, parent: QWidget = None):
        super(LibraryWidgetController, self).__init__(parent=parent)
        self._icon_container: QWidget = icon_container
        self._list_container: QWidget = list_container
        self.core: LegendaryCore = LegendaryCoreSingleton()
        self.signals: GlobalSignals = GlobalSignalsSingleton()
        self.api_results = ApiResultsSingleton()

        self.signals.progress.started.connect(self.start_progress)
        self.signals.progress.value.connect(self.update_progress)
        self.signals.progress.finished.connect(self.finish_progress)

        self.signals.game.installed.connect(self.on_install)
        self.signals.game.uninstalled.connect(self.on_uninstall)
        self.signals.game.verified.connect(self.on_verified)

    def add_game(self, rgame: RareGame, game_utils: GameUtils, parent):
        return self.add_widgets(rgame, game_utils, parent)

    def add_widgets(self, rgame: RareGame, game_utils: GameUtils, parent) -> Tuple[IconGameWidget, ListGameWidget]:
        icon_widget = IconGameWidget(rgame, game_utils, parent)
        list_widget = ListGameWidget(rgame, game_utils, parent)
        return icon_widget, list_widget

    def __find_widget(self, app_name: str) -> Tuple[Union[IconGameWidget, None], Union[ListGameWidget, None]]:
        iw = self._icon_container.findChild(IconGameWidget, app_name)
        lw = self._list_container.findChild(ListGameWidget, app_name)
        return iw, lw

    @staticmethod
    def __visibility(widget, filter_name, search_text) -> Tuple[bool, float]:
        if filter_name == "installed":
            visible = widget.rgame.is_installed
        elif filter_name == "offline":
            visible = widget.rgame.can_run_offline
        elif filter_name == "32bit":
            visible = widget.rgame.is_win32
        elif filter_name == "mac":
            visible = widget.rgame.is_mac
        elif filter_name == "installable":
            visible = not widget.rgame.is_non_asset
        elif filter_name == "include_ue":
            visible = True
        elif filter_name == "all":
            visible = not widget.rgame.is_unreal
        else:
            visible = True

        if (
            search_text not in widget.rgame.app_name.lower()
            and search_text not in widget.rgame.app_title.lower()
        ):
            opacity = 0.25
        else:
            opacity = 1.0

        return visible, opacity

    def filter_list(self, filter_name="all", search_text: str = ""):
        icon_widgets = self._icon_container.findChildren(IconGameWidget)
        list_widgets = self._list_container.findChildren(ListGameWidget)
        for iw in icon_widgets:
            visibility, opacity = self.__visibility(iw, filter_name, search_text)
            iw.setOpacity(opacity)
            iw.setVisible(visibility)
        for lw in list_widgets:
            visibility, opacity = self.__visibility(lw, filter_name, search_text)
            lw.setOpacity(opacity)
            lw.setVisible(visibility)
        self.sort_list(search_text)

    @pyqtSlot()
    def sort_list(self, sort_by: str = ""):
        # lk: this is the existing sorting implemenation
        # lk: it sorts by installed then by title
        if sort_by:
            self._icon_container.layout().sort(lambda x: (sort_by not in x.widget().rgame.app_title.lower(),))
        else:
            self._icon_container.layout().sort(
                lambda x: (
                    not x.widget().rgame.is_installed,
                    x.widget().rgame.is_non_asset,
                    x.widget().rgame.app_title,
                )
            )
        list_widgets = self._list_container.findChildren(ListGameWidget)
        if sort_by:
            list_widgets.sort(key=lambda x: (sort_by not in x.rgame.app_title.lower(),))
        else:
            list_widgets.sort(
                key=lambda x: (not x.rgame.is_installed, x.rgame.is_non_asset, x.rgame.app_title)
            )
        for idx, wl in enumerate(list_widgets):
            self._list_container.layout().insertWidget(idx, wl)

    @pyqtSlot()
    @pyqtSlot(list)
    def update_list(self, app_names: List[str] = None):
        if not app_names:
            # lk: base it on icon widgets, the two lists should be identical
            icon_widgets = self._icon_container.findChildren(IconGameWidget)
            list_widgets = self._list_container.findChildren(ListGameWidget)
            icon_app_names = set([iw.rgame.app_name for iw in icon_widgets])
            list_app_names = set([lw.rgame.app_name for lw in list_widgets])
            games = self.api_results.game_list + self.api_results.no_asset_games
            game_app_names = set([g.app_name for g in games])
            new_icon_app_names = game_app_names.difference(icon_app_names)
            new_list_app_names = game_app_names.difference(list_app_names)
            for app_name in new_icon_app_names:
                game = self.rare_core.get_game(app_name)
                iw = IconGameWidget(game)
                self._icon_container.layout().addWidget(iw)
            for app_name in new_list_app_names:
                game = self.rare_core.get_game(app_name)
                lw = ListGameWidget(game)
                self._list_container.layout().addWidget(lw)
            self.sort_list()

    @pyqtSlot(list)
    def on_install(self, app_names: List[str]):
        for app_name in app_names:
            iw, lw = self.__find_widget(app_name)
            if iw is not None:
                iw.rgame.set_installed(True)
            if lw is not None:
                lw.rgame.set_installed(True)
        self.sort_list()

    @pyqtSlot(str)
    def on_uninstall(self, app_name: str):
        iw, lw = self.__find_widget(app_name)
        if iw is not None:
            iw.rgame.set_installed(False)
        if lw is not None:
            lw.rgame.set_installed(False)
        self.sort_list()

    @pyqtSlot(str)
    def on_verified(self, app_name: str):
        iw, lw = self.__find_widget(app_name)
        if iw is not None:
            iw.rgame.needs_verification = False
        if lw is not None:
            lw.rgame.needs_verification = False

    # lk: this should go in downloads and happen once
    def __find_game_for_dlc(self, app_name: str) -> Optional[str]:
        game = self.core.get_game(app_name, False)
        # lk: how can an app_name not refer to a game?
        if not game:
            return None
        if game.is_dlc:
            game_list = self.core.get_game_list(update_assets=False)
            game = list(
                filter(
                    lambda x: x.asset_infos["Windows"].catalog_item_id == game.metadata["mainGameItem"]["id"],
                    game_list,
                )
            )
            return game[0].app_name
        return app_name

    @pyqtSlot(str)
    def start_progress(self, app_name: str):
        iw, lw = self.__find_widget(app_name)
        if iw is not None:
            iw.rgame.start_progress()
        if lw is not None:
            lw.rgame.start_progress()

    @pyqtSlot(str, int)
    def update_progress(self, app_name: str, progress: int):
        iw, lw = self.__find_widget(app_name)
        if iw is not None:
            iw.rgame.update_progress(progress)
        if lw is not None:
            lw.rgame.update_progress(progress)

    @pyqtSlot(str, bool)
    def finish_progress(self, app_name: str, stopped: bool):
        iw, lw = self.__find_widget(app_name)
        if iw is not None:
            iw.rgame.finish_progress(not stopped, 0, "")
        if lw is not None:
            lw.rgame.finish_progress(not stopped, 0, "")
