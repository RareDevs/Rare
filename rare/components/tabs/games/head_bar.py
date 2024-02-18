from PyQt5.QtCore import QSettings, pyqtSignal, pyqtSlot, QSize, Qt
from PyQt5.QtWidgets import (
    QLabel,
    QPushButton,
    QWidget,
    QHBoxLayout,
    QComboBox,
    QToolButton,
    QMenu,
    QAction, QSpacerItem, QSizePolicy,
)

from rare.models.options import options, LibraryFilter, LibraryOrder
from rare.shared import RareCore
from rare.utils.extra_widgets import ButtonLineEdit
from rare.utils.misc import icon


class GameListHeadBar(QWidget):
    filterChanged = pyqtSignal(object)
    orderChanged = pyqtSignal(object)
    viewChanged = pyqtSignal(object)
    goto_import = pyqtSignal()
    goto_egl_sync = pyqtSignal()
    goto_eos_ubisoft = pyqtSignal()

    def __init__(self, parent=None):
        super(GameListHeadBar, self).__init__(parent=parent)
        self.rcore = RareCore.instance()
        self.settings = QSettings(self)

        self.filter = QComboBox(self)
        filters = {
            LibraryFilter.ALL: self.tr("All games"),
            LibraryFilter.INSTALLED: self.tr("Installed"),
            LibraryFilter.OFFLINE: self.tr("Offline"),
            # int(LibraryFilter.HIDDEN): self.tr("Hidden"),
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
            _filter = self.settings.value(*options.library_filter)
            if (index := self.filter.findData(_filter, Qt.UserRole)) < 0:
                raise ValueError
            else:
                self.filter.setCurrentIndex(index)
        except (TypeError, ValueError):
            self.settings.setValue(options.library_filter.key, options.library_filter.default)
            _filter = LibraryFilter(options.library_filter.default)
            self.filter.setCurrentIndex(self.filter.findData(_filter, Qt.UserRole))
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
            if (index := self.order.findData(_order, Qt.UserRole)) < 0:
                raise ValueError
            else:
                self.order.setCurrentIndex(index)
        except (TypeError, ValueError):
            self.settings.setValue(options.library_order.key, options.library_order.default)
            _order = LibraryOrder(options.library_order.default)
            self.order.setCurrentIndex(self.order.findData(_order, Qt.UserRole))
        self.order.currentIndexChanged.connect(self.__order_changed)

        integrations_menu = QMenu(parent=self)
        import_action = QAction(
            icon("mdi.import", "fa.arrow-down"), self.tr("Import Game"), integrations_menu
        )

        import_action.triggered.connect(self.goto_import)
        egl_sync_action = QAction(icon("mdi.sync", "fa.refresh"), self.tr("Sync with EGL"), integrations_menu)
        egl_sync_action.triggered.connect(self.goto_egl_sync)

        eos_ubisoft_action = QAction(
            icon("mdi.rocket", "fa.rocket"), self.tr("Epic Overlay and Ubisoft"), integrations_menu
        )
        eos_ubisoft_action.triggered.connect(self.goto_eos_ubisoft)

        integrations_menu.addAction(import_action)
        integrations_menu.addAction(egl_sync_action)
        integrations_menu.addAction(eos_ubisoft_action)

        integrations = QToolButton(parent=self)
        integrations.setText(self.tr("Integrations"))
        integrations.setMenu(integrations_menu)
        integrations.setPopupMode(QToolButton.InstantPopup)

        self.search_bar = ButtonLineEdit("fa.search", placeholder_text=self.tr("Search Game"))
        self.search_bar.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self.search_bar.setObjectName("SearchBar")
        self.search_bar.setFrame(False)
        self.search_bar.setMinimumWidth(250)

        installed_tooltip = self.tr("Installed games")
        self.installed_icon = QLabel(parent=self)
        self.installed_icon.setPixmap(icon("ph.floppy-disk-back-fill").pixmap(QSize(16, 16)))
        self.installed_icon.setToolTip(installed_tooltip)
        self.installed_label = QLabel(parent=self)
        font = self.installed_label.font()
        font.setBold(True)
        self.installed_label.setFont(font)
        self.installed_label.setToolTip(installed_tooltip)
        available_tooltip = self.tr("Available games")
        self.available_icon = QLabel(parent=self)
        self.available_icon.setPixmap(icon("ph.floppy-disk-back-light").pixmap(QSize(16, 16)))
        self.available_icon.setToolTip(available_tooltip)
        self.available_label = QLabel(parent=self)
        self.available_label.setToolTip(available_tooltip)

        self.refresh_list = QPushButton(parent=self)
        self.refresh_list.setIcon(icon("fa.refresh"))  # Reload icon
        self.refresh_list.clicked.connect(self.__refresh_clicked)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.addWidget(self.filter)
        layout.addWidget(self.order)
        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))
        layout.addWidget(self.search_bar)
        layout.addWidget(self.installed_icon)
        layout.addWidget(self.installed_label)
        layout.addWidget(self.available_icon)
        layout.addWidget(self.available_label)
        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))
        layout.addWidget(integrations)
        layout.addWidget(self.refresh_list)

    def set_games_count(self, inst: int, avail: int) -> None:
        self.installed_label.setText(str(inst))
        self.available_label.setText(str(avail))

    @pyqtSlot()
    def __refresh_clicked(self):
        self.rcore.fetch()

    def current_filter(self) -> LibraryFilter:
        return self.filter.currentData(Qt.UserRole)

    @pyqtSlot(int)
    def __filter_changed(self, index: int):
        data = self.filter.itemData(index, Qt.UserRole)
        self.filterChanged.emit(data)
        self.settings.setValue(options.library_filter.key, int(data))

    def current_order(self) -> LibraryOrder:
        return self.order.currentData(Qt.UserRole)

    @pyqtSlot(int)
    def __order_changed(self, index: int):
        data = self.order.itemData(index, Qt.UserRole)
        self.orderChanged.emit(data)
        self.settings.setValue(options.library_order.key, int(data))
