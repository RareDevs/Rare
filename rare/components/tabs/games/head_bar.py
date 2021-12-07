from PyQt5.QtCore import QSize, QSettings, pyqtSignal
from PyQt5.QtWidgets import QLineEdit, QLabel, QPushButton, QWidget, QHBoxLayout, QComboBox
from qtawesome import icon

from rare.utils.extra_widgets import SelectViewWidget


class GameListHeadBar(QWidget):
    filterChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super(GameListHeadBar, self).__init__(parent=parent)
        self.setLayout(QHBoxLayout())
        # self.installed_only = QCheckBox(self.tr("Installed only"))
        self.settings = QSettings()
        # self.installed_only.setChecked(self.settings.value("installed_only", False, bool))
        # self.layout.addWidget(self.installed_only)

        self.filter = QComboBox()
        self.filter.addItems([self.tr("All"),
                              self.tr("Installed only"),
                              self.tr("Offline Games"),
                              self.tr("32 Bit Games"),
                              self.tr("Mac games"),
                              self.tr("Exclude Origin")])
        self.layout().addWidget(self.filter)

        self.available_filters = ["all", "installed", "offline", "32bit", "mac", "installable"]

        try:
            self.filter.setCurrentIndex(self.settings.value("filter", 0, int))
        except TypeError:
            self.settings.setValue("filter", 0)

        self.filter.currentIndexChanged.connect(self.filter_changed)
        self.layout().addStretch(1)

        self.import_game = QPushButton(icon("mdi.import"), self.tr("Import Game"))
        self.import_clicked = self.import_game.clicked
        self.layout().addWidget(self.import_game)

        self.egl_sync = QPushButton(icon("mdi.sync"), self.tr("Sync with EGL"))
        self.egl_sync_clicked = self.egl_sync.clicked
        self.layout().addWidget(self.egl_sync)
        # FIXME: Until it is ready
        # self.egl_sync.setEnabled(False)

        self.layout().addStretch(1)

        icon_label = QLabel()
        icon_label.setPixmap(icon("fa.search").pixmap(QSize(20, 20)))
        self.layout().addWidget(icon_label)
        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("search_bar")
        self.search_bar.setFrame(False)
        self.search_bar.setMinimumWidth(200)
        self.search_bar.setPlaceholderText(self.tr("Search Game"))
        self.layout().addWidget(self.search_bar)

        self.layout().addStretch(2)
        checked = QSettings().value("icon_view", True, bool)

        self.view = SelectViewWidget(checked)
        self.layout().addWidget(self.view)
        self.layout().addStretch(1)

        self.refresh_list = QPushButton()
        self.refresh_list.setIcon(icon("fa.refresh"))  # Reload icon
        self.layout().addWidget(self.refresh_list)

    def filter_changed(self, i):
        self.filterChanged.emit(self.available_filters[i])
        self.settings.setValue("filter", i)
