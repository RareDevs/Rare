from typing import Tuple, List, Union, Optional

from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import QWidget

from rare.lgndr.core import LegendaryCore
from rare.models.game import RareGame
from rare.models.signals import GlobalSignals
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

        self.signals.game.installed.connect(self.sort_list)
        self.signals.game.uninstalled.connect(self.sort_list)

    def add_game(self, rgame: RareGame):
        return self.add_widgets(rgame)

    def add_widgets(self, rgame: RareGame) -> Tuple[IconGameWidget, ListGameWidget]:
        icon_widget = IconGameWidget(rgame, self._icon_container)
        list_widget = ListGameWidget(rgame, self._list_container)
        return icon_widget, list_widget

    @staticmethod
    def __visibility(widget: Union[IconGameWidget,ListGameWidget], filter_name, search_text) -> Tuple[bool, float]:
        if filter_name == "hidden":
            visible = "hidden" in widget.rgame.metadata.tags
        elif "hidden" in widget.rgame.metadata.tags:
            visible = False
        elif filter_name == "installed":
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
                key=lambda x: (
                # Sort by grant date
                #     x.widget().rgame.is_installed,
                #     not x.widget().rgame.is_non_asset,
                #     x.widget().rgame.grant_date(),
                # ), reverse=True
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
                # Sort by grant date
                # key=lambda x: (x.rgame.is_installed, not x.rgame.is_non_asset, x.rgame.grant_date()), reverse=True
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
            games = list(self.rcore.games)
            game_app_names = set([g.app_name for g in games])
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
            self.sort_list()

    def __find_widget(self, app_name: str) -> Tuple[Union[IconGameWidget, None], Union[ListGameWidget, None]]:
        iw = self._icon_container.findChild(IconGameWidget, app_name)
        lw = self._list_container.findChild(ListGameWidget, app_name)
        return iw, lw
