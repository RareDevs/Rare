from PyQt5.QtCore import QSettings, pyqtSignal
from PyQt5.QtWidgets import (
    QLabel,
    QPushButton,
    QWidget,
    QHBoxLayout,
    QComboBox,
)
from qtawesome import IconWidget

from rare.shared import ApiResultsSingleton
from rare.utils.extra_widgets import SelectViewWidget, ButtonLineEdit
from rare.utils.misc import icon


class GameListHeadBar(QWidget):
    filterChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super(GameListHeadBar, self).__init__(parent=parent)
        self.api_results = ApiResultsSingleton()
        self.settings = QSettings()

        self.filter = QComboBox()
        self.filter.addItems(
            [
                self.tr("All games"),
                self.tr("Installed only"),
                self.tr("Offline Games"),
            ]
        )

        self.available_filters = [
            "all",
            "installed",
            "offline",
        ]
        if self.api_results.bit32_games:
            self.filter.addItem(self.tr("32 Bit Games"))
            self.available_filters.append("32bit")

        if self.api_results.mac_games:
            self.filter.addItem(self.tr("Mac games"))
            self.available_filters.append("mac")

        if self.api_results.no_asset_games:
            self.filter.addItem(self.tr("Exclude Origin"))
            self.available_filters.append("installable")

        self.filter.addItem(self.tr("Include Unreal Engine"))
        self.available_filters.append("include_ue")

        try:
            self.filter.setCurrentIndex(self.settings.value("filter", 0, int))
        except TypeError:
            self.settings.setValue("filter", 0)
            self.filter.setCurrentIndex(0)

        self.filter.currentIndexChanged.connect(self.filter_changed)

        self.import_game = QPushButton(icon("mdi.import", "fa.arrow-down"), self.tr("Import Game"))
        self.import_clicked = self.import_game.clicked

        self.egl_sync = QPushButton(icon("mdi.sync", "fa.refresh"), self.tr("Sync with EGL"))
        self.egl_sync_clicked = self.egl_sync.clicked
        # FIXME: Until it is ready
        # self.egl_sync.setEnabled(False)

        self.search_bar = ButtonLineEdit("fa.search", placeholder_text=self.tr("Search Game"))
        self.search_bar.setObjectName("search_bar")
        self.search_bar.setFrame(False)
        self.search_bar.setMinimumWidth(200)

        checked = QSettings().value("icon_view", True, bool)

        installed_tooltip = self.tr("Installed games")
        self.installed_icon = IconWidget(parent=self)
        self.installed_icon.setIcon(icon("ph.floppy-disk-back-fill"))
        self.installed_icon.setToolTip(installed_tooltip)
        self.installed_label = QLabel(parent=self)
        font = self.installed_label.font()
        font.setBold(True)
        self.installed_label.setFont(font)
        self.installed_label.setToolTip(installed_tooltip)
        available_tooltip = self.tr("Available games")
        self.available_icon = IconWidget(parent=self)
        self.available_icon.setIcon(icon("ph.floppy-disk-back-light"))
        self.available_icon.setToolTip(available_tooltip)
        self.available_label = QLabel(parent=self)
        self.available_label.setToolTip(available_tooltip)

        self.view = SelectViewWidget(checked)

        self.refresh_list = QPushButton()
        self.refresh_list.setIcon(icon("fa.refresh"))  # Reload icon

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 5, 0, 5)
        layout.addWidget(self.filter)
        layout.addStretch(1)
        layout.addWidget(self.import_game)
        layout.addWidget(self.egl_sync)
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
        self.setLayout(layout)

    def set_games_count(self, inst: int, avail: int) -> None:
        self.installed_label.setText(str(inst))
        self.available_label.setText(str(avail))

    def filter_changed(self, i):
        self.filterChanged.emit(self.available_filters[i])
        self.settings.setValue("filter", i)
