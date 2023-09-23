from PyQt5.QtCore import QSettings, pyqtSignal, pyqtSlot, QSize, Qt
from PyQt5.QtWidgets import (
    QLabel,
    QPushButton,
    QWidget,
    QHBoxLayout,
    QComboBox,
    QToolButton,
    QMenu,
    QAction,
)

from rare.shared import RareCore
from rare.utils.extra_widgets import SelectViewWidget, ButtonLineEdit
from rare.utils.misc import icon
from .game_widgets import LibraryFilter, LibraryOrder


class GameListHeadBar(QWidget):
    filterChanged: pyqtSignal = pyqtSignal(int)
    orderChanged: pyqtSignal = pyqtSignal(int)
    goto_import: pyqtSignal = pyqtSignal()
    goto_egl_sync: pyqtSignal = pyqtSignal()
    goto_eos_ubisoft: pyqtSignal = pyqtSignal()

    def __init__(self, parent=None):
        super(GameListHeadBar, self).__init__(parent=parent)
        self.rcore = RareCore.instance()
        self.settings = QSettings()

        self.filter = QComboBox(parent=self)
        filters = {
            LibraryFilter.ALL: self.tr("All games"),
            LibraryFilter.INSTALLED: self.tr("Installed only"),
            LibraryFilter.OFFLINE: self.tr("Offline Games"),
            # LibraryFilterTypes.HIDDEN: self.tr("Hidden"),
        }
        for data, text in filters.items():
            self.filter.addItem(text, data)
        if self.rcore.bit32_games:
            self.filter.addItem(self.tr("32 Bit Games"), LibraryFilter.WIN32)
        if self.rcore.mac_games:
            self.filter.addItem(self.tr("Mac games"), LibraryFilter.MAC)
        if self.rcore.origin_games:
            self.filter.addItem(self.tr("Exclude Origin"), LibraryFilter.INSTALLABLE)
        self.filter.addItem(self.tr("Include Unreal Engine"), LibraryFilter.INCLUDE_UE)

        try:
            self.filter.setCurrentIndex(
                self.filter.findData(
                    LibraryFilter(self.settings.value("library_filter", int(LibraryFilter.ALL), int))
                )
            )
        except (TypeError, ValueError):
            self.settings.setValue("library_filter", int(LibraryFilter.ALL))
            self.filter.setCurrentIndex(self.filter.findData(LibraryFilter.ALL))

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
        self.search_bar.setObjectName("SearchBar")
        self.search_bar.setFrame(False)
        self.search_bar.setMinimumWidth(200)

        checked = QSettings().value("icon_view", True, bool)

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

        self.view = SelectViewWidget(checked)

        self.refresh_list = QPushButton(parent=self)
        self.refresh_list.setIcon(icon("fa.refresh"))  # Reload icon
        self.refresh_list.clicked.connect(self.__refresh_clicked)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.addWidget(self.filter)
        layout.addWidget(self.order)
        layout.addStretch(0)
        layout.addWidget(integrations)
        layout.addStretch(2)
        layout.addWidget(self.search_bar)
        layout.addStretch(2)
        layout.addWidget(self.installed_icon)
        layout.addWidget(self.installed_label)
        layout.addWidget(self.available_icon)
        layout.addWidget(self.available_label)
        layout.addStretch(2)
        layout.addWidget(self.view)
        layout.addStretch(2)
        layout.addWidget(self.refresh_list)

    def set_games_count(self, inst: int, avail: int) -> None:
        self.installed_label.setText(str(inst))
        self.available_label.setText(str(avail))

    @pyqtSlot()
    def __refresh_clicked(self):
        self.rcore.fetch()

    def current_filter(self) -> int:
        return int(self.filter.currentData(Qt.UserRole))

    @pyqtSlot(int)
    def __filter_changed(self, index: int):
        data = int(self.filter.itemData(index, Qt.UserRole))
        self.filterChanged.emit(data)
        self.settings.setValue("library_filter", data)

    def current_order(self) -> int:
        return int(self.order.currentData(Qt.UserRole))

    @pyqtSlot(int)
    def __order_changed(self, index: int):
        data = int(self.order.itemData(index, Qt.UserRole))
        self.orderChanged.emit(data)
        self.settings.setValue("library_order", data)
