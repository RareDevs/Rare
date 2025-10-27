from abc import abstractmethod
from typing import Tuple, Type, TypeVar, Union

from PySide6.QtCore import QObject, Qt, Slot
from PySide6.QtWidgets import QScrollArea, QVBoxLayout, QWidget

from rare.models.enumerations import LibraryFilter, LibraryOrder, LibraryView
from rare.models.game import RareGame
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

    __is_visible = {
        LibraryFilter.HIDDEN: lambda x: "hidden" in x.metadata.tags,
        LibraryFilter.FAVORITES: lambda x: "favorite" in x.metadata.tags,
        LibraryFilter.INSTALLED: lambda x: x.is_installed and not x.is_unreal and "hidden" not in x.metadata.tags,
        LibraryFilter.OFFLINE: lambda x: x.can_run_offline and not x.is_unreal and "hidden" not in x.metadata.tags,
        LibraryFilter.WIN32: lambda x: x.is_win32 and not x.is_unreal and "hidden" not in x.metadata.tags,
        LibraryFilter.MAC: lambda x: x.is_mac and not x.is_unreal and "hidden" not in x.metadata.tags,
        LibraryFilter.INSTALLABLE: lambda x: not x.is_non_asset and not x.is_unreal and "hidden" not in x.metadata.tags,
        LibraryFilter.INCLUDE_UE: lambda x: not x.is_android_only and "hidden" not in x.metadata.tags,
        LibraryFilter.ANDROID: lambda x: x.is_android_only,
        LibraryFilter.ALL: lambda x: not x.is_unreal and not x.is_android_only and "hidden" not in x.metadata.tags,
    }

    def __visibility(self, widget: ViewWidget, library_filter, search_text) -> Tuple[bool, float]:
        name_search = True
        tag_search = False
        if search_text.startswith("::"):
            search_text = search_text.removeprefix("::")
            tag_search = True
            name_search = False
            visible = True
        else:
            visible = self.__is_visible[library_filter](widget.rgame)

        opacity = 1.0
        if search_text and (
            (
                name_search
                and search_text not in widget.rgame.app_name.lower()
                and search_text not in widget.rgame.app_title.lower()
            )
            or (tag_search and search_text not in widget.rgame.metadata.tags)
        ):
            opacity = 0.25

        return visible, opacity

    def _filter_view(
        self,
        widget_type: Type[ViewWidget],
        filter_by: LibraryFilter = LibraryFilter.ALL,
        search_text: str = "",
    ):
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
    def filter_view(self, filter_by, search_text):
        pass

    @abstractmethod
    def order_view(self, order_by, search_text):
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

    def update_view(self):
        self._update_view(IconGameWidget)

    def find_widget(self, app_name: str) -> ViewWidget:
        return self._find_widget(IconGameWidget, app_name)

    def filter_view(self, filter_by: LibraryFilter, search_text: str = ""):
        self._filter_view(IconGameWidget, filter_by, search_text)

    def order_view(self, order_by: LibraryOrder, search_text: str = ""):
        if search_text:
            if search_text.startswith("::"):
                self.layout().sort(lambda x: search_text.removeprefix("::") not in x.widget().rgame.metadata.tags)
            else:
                self.layout().sort(
                    lambda x: search_text not in x.widget().rgame.app_title.lower()
                    and search_text not in x.widget().rgame.app_name.lower()
                )
        else:
            if (newest := order_by == LibraryOrder.NEWEST) or order_by == LibraryOrder.OLDEST:
                # Sort by grant date
                self.layout().sort(
                    key=lambda x: (
                        x.widget().rgame.is_installed,
                        not x.widget().rgame.is_non_asset,
                        x.widget().rgame.grant_date(),
                    ),
                    reverse=newest,
                )
            elif order_by == LibraryOrder.RECENT:
                # Sort by recently played
                self.layout().sort(
                    key=lambda x: (
                        x.widget().rgame.is_installed,
                        not x.widget().rgame.is_non_asset,
                        x.widget().rgame.metadata.last_played,
                    ),
                    reverse=True,
                )
            else:
                # Sort by title
                self.layout().sort(
                    key=lambda x: (
                        not x.widget().rgame.is_installed,
                        x.widget().rgame.is_non_asset,
                        x.widget().rgame.app_title,
                    )
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

    def update_view(self):
        self._update_view(ListGameWidget)

    def find_widget(self, app_name: str) -> ViewWidget:
        return self._find_widget(ListGameWidget, app_name)

    def filter_view(self, filter_by: LibraryFilter, search_text: str = ""):
        self._filter_view(ListGameWidget, filter_by, search_text)

    def order_view(self, order_by: LibraryOrder, search_text: str = ""):
        list_widgets = self.findChildren(ListGameWidget)
        if search_text:
            if search_text.startswith("::"):
                list_widgets.sort(key=lambda x: search_text.removeprefix("::") not in x.rgame.metadata.tags)
            else:
                list_widgets.sort(
                    key=lambda x: search_text not in x.rgame.app_title.lower() and search_text not in x.rgame.app_name.lower()
                )
        else:
            if (newest := order_by == LibraryOrder.NEWEST) or order_by == LibraryOrder.OLDEST:
                list_widgets.sort(
                    key=lambda x: (
                        x.rgame.is_installed,
                        not x.rgame.is_non_asset,
                        x.rgame.grant_date(),
                    ),
                    reverse=newest,
                )
            elif order_by == LibraryOrder.RECENT:
                list_widgets.sort(
                    key=lambda x: (
                        x.rgame.is_installed,
                        not x.rgame.is_non_asset,
                        x.rgame.metadata.last_played,
                    ),
                    reverse=True,
                )
            else:
                list_widgets.sort(
                    key=lambda x: (
                        not x.rgame.is_installed,
                        x.rgame.is_non_asset,
                        x.rgame.app_title,
                    )
                )
        for idx, wl in enumerate(list_widgets):
            self.layout().insertWidget(idx, wl)


class LibraryWidgetController(QObject):
    def __init__(self, rcore: RareCore, view: LibraryView, parent: QScrollArea = None):
        super(LibraryWidgetController, self).__init__(parent=parent)
        self.rcore = rcore
        self.core = rcore.core()
        self.signals = rcore.signals()

        if view == LibraryView.COVER:
            self._container: IconViewContainer = IconViewContainer(self.rcore, parent)
        else:
            self._container: ListViewContainer = ListViewContainer(self.rcore, parent)
        parent.setWidget(self._container)

        self._current_filter: LibraryFilter = LibraryFilter.ALL
        self._current_order: LibraryOrder = LibraryOrder.TITLE

        self.rcore.completed.connect(self.refresh_game_view)
        self.signals.game.installed.connect(self.update_game_view)
        self.signals.game.uninstalled.connect(self.update_game_view)

    def add_game(self, rgame: RareGame):
        return self.add_widget(rgame)

    def add_widget(self, rgame: RareGame) -> ViewWidget:
        return self._container.add_widget(rgame)

    def filter_game_view(self, filter_by: LibraryFilter = None, search_text: str = ""):
        self._current_filter = filter_by if filter_by is not None else self._current_filter
        self._container.filter_view(self._current_filter, search_text)
        self.order_game_view(self._current_order, search_text=search_text)

    @Slot()
    def order_game_view(self, order_by: LibraryOrder = None, search_text: str = ""):
        self._current_order = order_by if order_by is not None else self._current_order
        self._container.order_view(self._current_order, search_text)

    @Slot()
    def update_game_view(self):
        self.order_game_view(self._current_order)

    @Slot()
    def refresh_game_view(self):
        self._container.update_view()
        self.order_game_view(self._current_order)

    def __find_widget(self, app_name: str) -> Union[ViewWidget, None]:
        return self._container.find_widget(app_name)
