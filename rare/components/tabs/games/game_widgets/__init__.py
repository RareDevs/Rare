from typing import Tuple, List, Union

from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import QWidget

from rare.lgndr.core import LegendaryCore
from rare.models.game import RareGame
from rare.models.signals import GlobalSignals
from rare.models.library import LibraryFilter, LibraryOrder
from rare.shared import RareCore
from .icon_game_widget import IconGameWidget
from .list_game_widget import ListGameWidget


class LibraryWidgetController(QObject):
    def __init__(self, icon_container: QWidget, list_container: QWidget, parent: QWidget = None):
        super(LibraryWidgetController, self).__init__(parent=parent)
        self._icon_container: QWidget = icon_container
        self._list_container: QWidget = list_container
        self.rcore = RareCore.instance()
        self.core: LegendaryCore = self.rcore.core()
        self.signals: GlobalSignals = self.rcore.signals()

        self.signals.game.installed.connect(self.order_game_views)
        self.signals.game.uninstalled.connect(self.order_game_views)

    def add_game(self, rgame: RareGame):
        return self.add_widgets(rgame)

    def add_widgets(self, rgame: RareGame) -> Tuple[IconGameWidget, ListGameWidget]:
        icon_widget = IconGameWidget(rgame, self._icon_container)
        list_widget = ListGameWidget(rgame, self._list_container)
        return icon_widget, list_widget

    @staticmethod
    def __visibility(
        widget: Union[IconGameWidget, ListGameWidget], library_filter, search_text
    ) -> Tuple[bool, float]:
        if library_filter == LibraryFilter.HIDDEN:
            visible = "hidden" in widget.rgame.metadata.tags
        elif "hidden" in widget.rgame.metadata.tags:
            visible = False
        elif library_filter == LibraryFilter.INSTALLED:
            visible = widget.rgame.is_installed and not widget.rgame.is_unreal
        elif library_filter == LibraryFilter.OFFLINE:
            visible = widget.rgame.can_run_offline and not widget.rgame.is_unreal
        elif library_filter == LibraryFilter.WIN32:
            visible = widget.rgame.is_win32 and not widget.rgame.is_unreal
        elif library_filter == LibraryFilter.MAC:
            visible = widget.rgame.is_mac and not widget.rgame.is_unreal
        elif library_filter == LibraryFilter.INSTALLABLE:
            visible = not widget.rgame.is_non_asset and not widget.rgame.is_unreal
        elif library_filter == LibraryFilter.INCLUDE_UE:
            visible = True
        elif library_filter == LibraryFilter.ALL:
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

    def filter_game_views(self, library_filter=LibraryFilter.ALL, search_text: str = ""):
        icon_widgets = self._icon_container.findChildren(IconGameWidget)
        list_widgets = self._list_container.findChildren(ListGameWidget)
        for iw in icon_widgets:
            visibility, opacity = self.__visibility(iw, library_filter, search_text)
            iw.setOpacity(opacity)
            iw.setVisible(visibility)
        for lw in list_widgets:
            visibility, opacity = self.__visibility(lw, library_filter, search_text)
            lw.setOpacity(opacity)
            lw.setVisible(visibility)
        self.order_game_views(search_text=search_text)

    @pyqtSlot()
    def order_game_views(self, order_by: LibraryOrder = LibraryOrder.TITLE, search_text: str = ""):
        list_widgets = self._list_container.findChildren(ListGameWidget)
        if search_text:
            self._icon_container.layout().sort(
                lambda x: (search_text not in x.widget().rgame.app_title.lower(),)
            )
            list_widgets.sort(key=lambda x: (search_text not in x.rgame.app_title.lower(),))
        else:
            if (newest := order_by == LibraryOrder.NEWEST) or order_by == LibraryOrder.OLDEST:
                # Sort by grant date
                self._icon_container.layout().sort(
                    key=lambda x: (x.widget().rgame.is_installed, not x.widget().rgame.is_non_asset, x.widget().rgame.grant_date()),
                    reverse=newest,
                )
                list_widgets.sort(
                    key=lambda x: (x.rgame.is_installed, not x.rgame.is_non_asset, x.rgame.grant_date()),
                    reverse=newest,
                )
            elif order_by == LibraryOrder.RECENT:
                # Sort by recently played
                self._icon_container.layout().sort(
                    key=lambda x: (not x.widget().rgame.is_installed, x.widget().rgame.is_non_asset, x.widget().rgame.metadata.last_played),
                    reverse=True,
                )
                list_widgets.sort(
                    key=lambda x: (not x.rgame.is_installed, x.rgame.is_non_asset, x.rgame.metadata.last_played),
                    reverse=True,
                )
            else:
                # Sort by title
                self._icon_container.layout().sort(
                    key=lambda x: (not x.widget().rgame.is_installed, x.widget().rgame.is_non_asset, x.widget().rgame.app_title)
                )
                list_widgets.sort(
                    key=lambda x: (not x.rgame.is_installed, x.rgame.is_non_asset, x.rgame.app_title)
                )

        for idx, wl in enumerate(list_widgets):
            self._list_container.layout().insertWidget(idx, wl)

    @pyqtSlot()
    @pyqtSlot(list)
    def update_game_views(self, app_names: List[str] = None):
        if app_names:
            return
        # lk: base it on icon widgets, the two lists should be identical
        icon_widgets = self._icon_container.findChildren(IconGameWidget)
        list_widgets = self._list_container.findChildren(ListGameWidget)
        icon_app_names = {iw.rgame.app_name for iw in icon_widgets}
        list_app_names = {lw.rgame.app_name for lw in list_widgets}
        games = list(self.rcore.games)
        game_app_names = {g.app_name for g in games}
        new_icon_app_names = game_app_names.difference(icon_app_names)
        new_list_app_names = game_app_names.difference(list_app_names)
        for app_name in new_icon_app_names:
            game = self.rcore.get_game(app_name)
            iw = IconGameWidget(game)
            self._icon_container.layout().addWidget(iw)
        for app_name in new_list_app_names:
            game = self.rcore.get_game(app_name)
            lw = ListGameWidget(game)
            self._list_container.layout().addWidget(lw)
        self.order_game_views()

    def __find_widget(self, app_name: str) -> Tuple[Union[IconGameWidget, None], Union[ListGameWidget, None]]:
        iw = self._icon_container.findChild(IconGameWidget, app_name)
        lw = self._list_container.findChild(ListGameWidget, app_name)
        return iw, lw
