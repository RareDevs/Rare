from abc import abstractmethod
from typing import Tuple, List, Union, Type, TypeVar

from PySide6.QtCore import QObject, Slot, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea

from rare.lgndr.core import LegendaryCore
from rare.models.game import RareGame
from rare.models.signals import GlobalSignals
from rare.models.library import LibraryFilter, LibraryOrder, LibraryView
from rare.shared import RareCore
from rare.widgets.library_layout import LibraryLayout
from .icon_game_widget import IconGameWidget
from .list_game_widget import ListGameWidget

ViewWidget = TypeVar("ViewWidget", IconGameWidget, ListGameWidget)


class ViewContainer(QWidget):
    def __init__(self, rcore: RareCore, parent=None):
        super().__init__(parent=parent)
        self.rcore: RareCore = rcore

    def _add_widget(self, widget_type: Type[ViewWidget], rgame: RareGame) -> ViewWidget:
        widget = widget_type(rgame, self)
        self.layout().addWidget(widget)
        return widget

    @staticmethod
    def __visibility(widget: ViewWidget, library_filter, search_text) -> Tuple[bool, float]:
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

    def _filter_view(self, widget_type: Type[ViewWidget], filter_by: LibraryFilter = LibraryFilter.ALL, search_text: str = ""):
        widgets = self.findChildren(widget_type)
        for iw in widgets:
            visibility, opacity = self.__visibility(iw, filter_by, search_text)
            iw.setOpacity(opacity)
            iw.setVisible(visibility)

    def _update_view(self, widget_type: Type[ViewWidget]):
        widgets = self.findChildren(widget_type)
        app_names = {iw.rgame.app_name for iw in widgets}
        games = list(self.rcore.games)
        game_app_names = {g.app_name for g in games}
        new_app_names = game_app_names.difference(app_names)
        for app_name in new_app_names:
            game = self.rcore.get_game(app_name)
            w = widget_type(game, self)
            self.layout().addWidget(w)

    def _find_widget(self, widget_type: Type[ViewWidget], app_name: str) -> ViewWidget:
        w = self.findChild(widget_type, app_name)
        return w

    @abstractmethod
    def order_view(self):
        pass


class IconViewContainer(ViewContainer):
    def __init__(self, rcore: RareCore, parent=None):
        super().__init__(rcore, parent=parent)
        view_layout = LibraryLayout(self)
        view_layout.setSpacing(9)
        view_layout.setContentsMargins(0, 13, 0, 13)
        view_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(view_layout)

    def add_widget(self, rgame: RareGame) -> IconGameWidget:
        return self._add_widget(IconGameWidget, rgame)

    def filter_view(self, filter_by: LibraryFilter = LibraryFilter.ALL, search_text: str = ""):
        self._filter_view(IconGameWidget, filter_by, search_text)

    def update_view(self):
        self._update_view(IconGameWidget)

    def find_widget(self, app_name: str) -> ViewWidget:
        return self._find_widget(IconGameWidget, app_name)

    def order_view(self, order_by: LibraryOrder = LibraryOrder.TITLE, search_text: str = ""):
        if search_text:
            self.layout().sort(
                lambda x: (search_text not in x.widget().rgame.app_title.lower(),)
            )
        else:
            if (newest := order_by == LibraryOrder.NEWEST) or order_by == LibraryOrder.OLDEST:
                # Sort by grant date
                self.layout().sort(
                    key=lambda x: (x.widget().rgame.is_installed, not x.widget().rgame.is_non_asset, x.widget().rgame.grant_date()),
                    reverse=newest,
                )
            elif order_by == LibraryOrder.RECENT:
                # Sort by recently played
                self.layout().sort(
                    key=lambda x: (x.widget().rgame.is_installed, not x.widget().rgame.is_non_asset, x.widget().rgame.metadata.last_played),
                    reverse=True,
                )
            else:
                # Sort by title
                self.layout().sort(
                    key=lambda x: (not x.widget().rgame.is_installed, x.widget().rgame.is_non_asset, x.widget().rgame.app_title)
                )


class ListViewContainer(ViewContainer):
    def __init__(self, rcore, parent=None):
        super().__init__(rcore, parent=parent)
        view_layout = QVBoxLayout(self)
        view_layout.setContentsMargins(3, 3, 9, 3)
        view_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(view_layout)

    def add_widget(self, rgame: RareGame) -> ListGameWidget:
        return self._add_widget(ListGameWidget, rgame)

    def filter_view(self, filter_by: LibraryFilter = LibraryFilter.ALL, search_text: str = ""):
        self._filter_view(ListGameWidget, filter_by, search_text)

    def update_view(self):
        self._update_view(ListGameWidget)

    def find_widget(self, app_name: str) -> ViewWidget:
        return self._find_widget(ListGameWidget, app_name)

    def order_view(self, order_by: LibraryOrder = LibraryOrder.TITLE, search_text: str = ""):
        list_widgets = self.findChildren(ListGameWidget)
        if search_text:
            list_widgets.sort(key=lambda x: (search_text not in x.rgame.app_title.lower(),))
        else:
            if (newest := order_by == LibraryOrder.NEWEST) or order_by == LibraryOrder.OLDEST:
                list_widgets.sort(
                    key=lambda x: (x.rgame.is_installed, not x.rgame.is_non_asset, x.rgame.grant_date()),
                    reverse=newest,
                )
            elif order_by == LibraryOrder.RECENT:
                list_widgets.sort(
                    key=lambda x: (x.rgame.is_installed, not x.rgame.is_non_asset, x.rgame.metadata.last_played),
                    reverse=True,
                )
            else:
                list_widgets.sort(
                    key=lambda x: (not x.rgame.is_installed, x.rgame.is_non_asset, x.rgame.app_title)
                )
        for idx, wl in enumerate(list_widgets):
            self.layout().insertWidget(idx, wl)


class LibraryWidgetController(QObject):
    def __init__(self, view: LibraryView, parent: QScrollArea = None):
        super(LibraryWidgetController, self).__init__(parent=parent)
        self.rcore = RareCore.instance()
        self.core: LegendaryCore = self.rcore.core()
        self.signals: GlobalSignals = self.rcore.signals()

        if view == LibraryView.COVER:
            self._container: IconViewContainer = IconViewContainer(self.rcore, parent)
        else:
            self._container: ListViewContainer = ListViewContainer(self.rcore, parent)
        parent.setWidget(self._container)

        self.signals.game.installed.connect(self.order_game_views)
        self.signals.game.uninstalled.connect(self.order_game_views)

    def add_game(self, rgame: RareGame):
        return self.add_widgets(rgame)

    def add_widgets(self, rgame: RareGame) -> ViewWidget:
        return self._container.add_widget(rgame)

    def filter_game_views(self, filter_by: LibraryFilter = LibraryFilter.ALL, search_text: str = ""):
        self._container.filter_view(filter_by, search_text)
        self.order_game_views(search_text=search_text)

    @Slot()
    def order_game_views(self, order_by: LibraryOrder = LibraryOrder.TITLE, search_text: str = ""):
        self._container.order_view(order_by, search_text)

    @Slot()
    @Slot(list)
    def update_game_views(self, app_names: List[str] = None):
        if app_names:
            return
        self._container.update_view()
        self.order_game_views()

    def __find_widget(self, app_name: str) -> Union[ViewWidget, None]:
        return self._container.find_widget(app_name)
