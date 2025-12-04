from logging import getLogger

from PySide6.QtCore import QSize, Qt, Signal, Slot
from PySide6.QtWidgets import (
    QComboBox,
    QCompleter,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QWidget,
    QWidgetAction,
)

from rare.models.settings import LibraryFilter, LibraryOrder, RareAppSettings, app_settings
from rare.shared import RareCore
from rare.utils.misc import qta_icon
from rare.widgets.button_edit import ButtonLineEdit

from .account import AccountWidget


class LibraryHeadBar(QWidget):
    # int: exit code
    exit_app: Signal = Signal(int)
    # object: LibraryFilter
    filterChanged = Signal(object)
    # object: LibraryOrder
    orderChanged = Signal(object)
    # object: LibraryView
    viewChanged = Signal(object)

    def __init__(self, settings: RareAppSettings, rcore: RareCore, parent=None):
        super(LibraryHeadBar, self).__init__(parent=parent)
        self.settings = settings
        self.rcore = rcore
        self.core = rcore.core()
        self.signals = rcore.signals()
        self.logger = getLogger(type(self).__name__)

        self.filter = QComboBox(self)
        filters = {
            LibraryFilter.ALL: self.tr("All games"),
            LibraryFilter.INSTALLED: self.tr("Installed"),
            LibraryFilter.OFFLINE: self.tr("Offline"),
            LibraryFilter.HIDDEN: self.tr("Hidden"),
            LibraryFilter.FAVORITES: self.tr("Favorites"),
        }
        for data, text in filters.items():
            self.filter.addItem(text, data)

        if self.rcore.bit32_games:
            self.filter.addItem(self.tr("Only 32bit"), LibraryFilter.WIN32)
        if self.rcore.mac_games:
            self.filter.addItem(self.tr("Only macOS"), LibraryFilter.MAC)
        if self.rcore.non_asset_games:
            self.filter.addItem(self.tr("Exclude non-asset"), LibraryFilter.INSTALLABLE)
        self.filter.addItem(self.tr("Include Unreal"), LibraryFilter.INCLUDE_UE)
        self.filter.addItem(self.tr("Android"), LibraryFilter.ANDROID)

        try:
            _filter = LibraryFilter(self.settings.get_value(app_settings.library_filter))
            if (index := self.filter.findData(_filter, Qt.ItemDataRole.UserRole)) < 0:
                raise ValueError(f"Filter '{_filter}' is not available")
            else:
                self.filter.setCurrentIndex(index)
        except (TypeError, ValueError) as e:
            self.logger.error("Error while loading library: %s", e)
            self.settings.set_value(app_settings.library_filter, app_settings.library_filter.default)
            _filter = LibraryFilter(app_settings.library_filter.default)
            self.filter.setCurrentIndex(self.filter.findData(_filter, Qt.ItemDataRole.UserRole))
        self.filter.currentIndexChanged.connect(self.__filter_changed)

        self.order = QComboBox(parent=self)
        sortings = {
            LibraryOrder.TITLE: self.tr("Title"),
            LibraryOrder.RECENT: self.tr("Recently played"),
            LibraryOrder.NEWEST: self.tr("Newest"),
            LibraryOrder.OLDEST: self.tr("Oldest"),
        }
        for data, text in sortings.items():
            self.order.addItem(text, data)

        try:
            _order = LibraryOrder(self.settings.get_value(app_settings.library_order))
            if (index := self.order.findData(_order, Qt.ItemDataRole.UserRole)) < 0:
                raise ValueError(f"Order '{_order}' is not available")
            else:
                self.order.setCurrentIndex(index)
        except (TypeError, ValueError) as e:
            self.logger.error("Error while loading library: %s", e)
            self.settings.set_value(app_settings.library_order, app_settings.library_order.default)
            _order = LibraryOrder(app_settings.library_order.default)
            self.order.setCurrentIndex(self.order.findData(_order, Qt.ItemDataRole.UserRole))
        self.order.currentIndexChanged.connect(self.__order_changed)

        self.search_bar = ButtonLineEdit("fa5s.search", placeholder_text=self.tr("Search (use :: to filter by tag)"))
        self.search_bar.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.search_bar.setObjectName("SearchBar")
        self.search_bar.setMinimumWidth(250)

        installed_tooltip = self.tr("Installed games")
        self.installed_icon = QLabel(parent=self)
        self.installed_icon.setPixmap(qta_icon("ph.floppy-disk-back-fill").pixmap(QSize(16, 16)))
        self.installed_icon.setToolTip(installed_tooltip)
        self.installed_label = QLabel(parent=self)
        font = self.installed_label.font()
        font.setBold(True)
        self.installed_label.setFont(font)
        self.installed_label.setToolTip(installed_tooltip)
        available_tooltip = self.tr("Available games")
        self.available_icon = QLabel(parent=self)
        self.available_icon.setPixmap(qta_icon("ph.floppy-disk-back-light").pixmap(QSize(16, 16)))
        self.available_icon.setToolTip(available_tooltip)
        self.available_label = QLabel(parent=self)
        self.available_label.setToolTip(available_tooltip)

        # Account Button
        self.account_widget = AccountWidget(self.signals, self.core, self)
        self.account_widget.exit_app.connect(self.exit_app)
        account_action = QWidgetAction(self)
        account_action.setDefaultWidget(self.account_widget)
        account_button = QPushButton(self.core.lgd.userdata.get("displayName"), self)
        account_button.setIcon(qta_icon("mdi.account-circle", "fa5s.user"))
        account_button.setToolTip(self.tr("Menu"))
        account_menu = QMenu(account_button)
        account_menu.addAction(account_action)
        account_button.setMenu(account_menu)

        self.refresh_list = QPushButton(parent=self)
        self.refresh_list.setIcon(qta_icon("fa.refresh", "fa5s.sync"))  # Reload icon
        self.refresh_list.clicked.connect(self.__refresh_clicked)

        left_layout = QHBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.filter)
        left_layout.addWidget(self.order)
        left_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))

        right_layout = QHBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(self.installed_icon)
        right_layout.addWidget(self.installed_label)
        right_layout.addWidget(self.available_icon)
        right_layout.addWidget(self.available_label)
        right_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))
        right_layout.addWidget(account_button)
        right_layout.addWidget(self.refresh_list)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(left_layout)
        layout.addWidget(self.search_bar)
        layout.addLayout(right_layout)

        self.signals.application.update_game_tags.connect(self.__game_tags_updated)
        self.__game_tags_updated()

    def __game_tags_updated(self):
        if self.search_bar.completer():
            self.search_bar.completer().deleteLater()
        wordlist = tuple(map(lambda x: "::" + x, self.rcore.game_tags))
        completer = QCompleter(wordlist, self.search_bar)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.search_bar.setCompleter(completer)

    def set_games_count(self, inst: int, avail: int) -> None:
        self.installed_label.setText(str(inst))
        self.available_label.setText(str(avail))

    @Slot()
    def __refresh_clicked(self):
        self.rcore.fetch()

    def current_filter(self) -> LibraryFilter:
        return self.filter.currentData(Qt.ItemDataRole.UserRole)

    @Slot(int)
    def __filter_changed(self, index: int):
        data = self.filter.itemData(index, Qt.ItemDataRole.UserRole)
        self.filterChanged.emit(data)
        self.settings.set_value(app_settings.library_filter, data)

    def current_order(self) -> LibraryOrder:
        return self.order.currentData(Qt.ItemDataRole.UserRole)

    @Slot(int)
    def __order_changed(self, index: int):
        data = self.order.itemData(index, Qt.ItemDataRole.UserRole)
        self.orderChanged.emit(data)
        self.settings.set_value(app_settings.library_order, data)


class SelectViewWidget(QWidget):
    toggled = Signal(bool)

    def __init__(self, icon_view: bool, parent=None):
        super(SelectViewWidget, self).__init__(parent=parent)
        self.icon_button = QPushButton(self)
        self.icon_button.setObjectName(f"{type(self).__name__}Button")
        self.list_button = QPushButton(self)
        self.list_button.setObjectName(f"{type(self).__name__}Button")

        if icon_view:
            self.icon_button.setIcon(qta_icon("mdi.view-grid-outline", "ei.th-large", color="orange"))
            self.list_button.setIcon(qta_icon("fa5s.list", "ei.th-list", color="#eee"))
        else:
            self.icon_button.setIcon(qta_icon("mdi.view-grid-outline", "ei.th-large", color="#eee"))
            self.list_button.setIcon(qta_icon("fa5s.list", "ei.th-list", color="orange"))

        self.icon_button.clicked.connect(self.icon)
        self.list_button.clicked.connect(self.list)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.icon_button)
        layout.addWidget(self.list_button)

        self.setLayout(layout)

    def icon(self):
        self.icon_button.setIcon(qta_icon("mdi.view-grid-outline", "ei.th-large", color="orange"))
        self.list_button.setIcon(qta_icon("fa5s.list", "ei.th-list", color="#eee"))
        self.toggled.emit(True)

    def list(self):
        self.icon_button.setIcon(qta_icon("mdi.view-grid-outline", "ei.th-large", color="#eee"))
        self.list_button.setIcon(qta_icon("fa5s.list", "ei.th-list", color="orange"))
        self.toggled.emit(False)
