import logging

from PySide6.QtCore import QSettings, Signal, Slot, QSize, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QHBoxLayout,
    QWidget,
    QPushButton,
    QLabel,
    QComboBox,
    QMenu,
    QSpacerItem,
    QSizePolicy,
)

from rare.models.options import options, LibraryFilter, LibraryOrder
from rare.shared import RareCore
from rare.utils.misc import qta_icon
from rare.widgets.button_edit import ButtonLineEdit


class LibraryHeadBar(QWidget):
    filterChanged = Signal(object)
    orderChanged = Signal(object)
    viewChanged = Signal(object)
    goto_import = Signal()
    goto_egl_sync = Signal()
    goto_eos_ubisoft = Signal()

    def __init__(self, parent=None):
        super(LibraryHeadBar, self).__init__(parent=parent)
        self.logger = logging.getLogger(type(self).__name__)
        self.rcore = RareCore.instance()
        self.settings = QSettings(self)

        self.filter = QComboBox(self)
        filters = {
            LibraryFilter.ALL: self.tr("All games"),
            LibraryFilter.INSTALLED: self.tr("Installed"),
            LibraryFilter.OFFLINE: self.tr("Offline"),
            # LibraryFilter.HIDDEN: self.tr("Hidden"),
        }
        for data, text in filters.items():
            self.filter.addItem(text, data)

        if self.rcore.bit32_games:
            self.filter.addItem(self.tr("32bit games"), LibraryFilter.WIN32)
        if self.rcore.mac_games:
            self.filter.addItem(self.tr("macOS games"), LibraryFilter.MAC)
        if self.rcore.origin_games:
            self.filter.addItem(self.tr("Exclude Origin"), LibraryFilter.INSTALLABLE)
        self.filter.addItem(self.tr("Include Unreal"),     LibraryFilter.INCLUDE_UE)

        try:
            _filter = LibraryFilter(self.settings.value(*options.library_filter))
            if (index := self.filter.findData(_filter, Qt.ItemDataRole.UserRole)) < 0:
                raise ValueError(f"Filter '{_filter}' is not available")
            else:
                self.filter.setCurrentIndex(index)
        except (TypeError, ValueError) as e:
            self.logger.error("Error while loading library: %s", e)
            self.settings.setValue(options.library_filter.key, options.library_filter.default)
            _filter = LibraryFilter(options.library_filter.default)
            self.filter.setCurrentIndex(self.filter.findData(_filter, Qt.ItemDataRole.UserRole))
        self.filter.currentIndexChanged.connect(self.__filter_changed)

        self.order = QComboBox(parent=self)
        sortings = {
            LibraryOrder.TITLE:  self.tr("Title"),
            LibraryOrder.RECENT: self.tr("Recently played"),
            LibraryOrder.NEWEST: self.tr("Newest"),
            LibraryOrder.OLDEST: self.tr("Oldest"),
        }
        for data, text in sortings.items():
            self.order.addItem(text, data)

        try:
            _order = LibraryOrder(self.settings.value(*options.library_order))
            if (index := self.order.findData(_order, Qt.ItemDataRole.UserRole)) < 0:
                raise ValueError(f"Order '{_order}' is not available")
            else:
                self.order.setCurrentIndex(index)
        except (TypeError, ValueError) as e:
            self.logger.error("Error while loading library: %s", e)
            self.settings.setValue(options.library_order.key, options.library_order.default)
            _order = LibraryOrder(options.library_order.default)
            self.order.setCurrentIndex(self.order.findData(_order, Qt.ItemDataRole.UserRole))
        self.order.currentIndexChanged.connect(self.__order_changed)

        integrations_menu = QMenu(parent=self)
        import_action = QAction(
            qta_icon("mdi.import", "fa.arrow-down"), self.tr("Import Game"), integrations_menu
        )

        import_action.triggered.connect(self.goto_import)
        egl_sync_action = QAction(qta_icon("mdi.sync", "fa.refresh"), self.tr("Sync with EGL"), integrations_menu)
        egl_sync_action.triggered.connect(self.goto_egl_sync)

        eos_ubisoft_action = QAction(
            qta_icon("mdi.rocket", "fa.rocket"), self.tr("Epic Overlay and Ubisoft"), integrations_menu
        )
        eos_ubisoft_action.triggered.connect(self.goto_eos_ubisoft)

        integrations_menu.addAction(import_action)
        integrations_menu.addAction(egl_sync_action)
        integrations_menu.addAction(eos_ubisoft_action)

        integrations = QPushButton(parent=self)
        integrations.setText(self.tr("Integrations"))
        integrations.setIcon(qta_icon("mdi.tools"))
        integrations.setMenu(integrations_menu)

        self.search_bar = ButtonLineEdit("fa.search", placeholder_text=self.tr("Search"))
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

        self.refresh_list = QPushButton(parent=self)
        self.refresh_list.setIcon(qta_icon("fa.refresh"))  # Reload icon
        self.refresh_list.clicked.connect(self.__refresh_clicked)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.filter)
        layout.addWidget(self.order)
        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))
        layout.addWidget(self.search_bar)
        layout.addWidget(self.installed_icon)
        layout.addWidget(self.installed_label)
        layout.addWidget(self.available_icon)
        layout.addWidget(self.available_label)
        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))
        layout.addWidget(integrations)
        layout.addWidget(self.refresh_list)

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
        self.settings.setValue(options.library_filter.key, int(data))

    def current_order(self) -> LibraryOrder:
        return self.order.currentData(Qt.ItemDataRole.UserRole)

    @Slot(int)
    def __order_changed(self, index: int):
        data = self.order.itemData(index, Qt.ItemDataRole.UserRole)
        self.orderChanged.emit(data)
        self.settings.setValue(options.library_order.key, int(data))


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


