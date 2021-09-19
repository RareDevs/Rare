from PyQt5.QtCore import QSettings, QSize, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QStackedLayout, \
    QLabel, QComboBox
from qtawesome import icon

from legendary.models.game import Game
from rare.components.tabs.games.game_info import InfoTabs
from rare.components.tabs.games.game_info.uninstalled_info import UninstalledInfo, UninstalledTabInfo
from rare.components.tabs.games.game_list import GameList
from rare.components.tabs.games.import_widget import ImportWidget
from rare.utils.extra_widgets import SelectViewWidget


class GameTab(QWidget):
    def __init__(self, core, parent, offline):
        super(GameTab, self).__init__(parent=parent)
        self.setLayout(QStackedLayout())
        self.default_widget = Games(core, self, offline)
        # Signal to show info
        self.default_widget.game_list.show_game_info.connect(self.show_info)
        self.default_widget.head_bar.import_game.clicked.connect(lambda: self.layout().setCurrentIndex(2))
        self.layout().addWidget(self.default_widget)

        self.game_info = InfoTabs(core, self)
        self.game_info.info.update_list.connect(self.update_list)
        self.layout().addWidget(self.game_info)

        self.default_widget.head_bar.refresh_list.clicked.connect(self.update_list)

        self.import_widget = ImportWidget(core, self)
        self.layout().addWidget(self.import_widget)
        self.import_widget.back_button.clicked.connect(lambda: self.layout().setCurrentIndex(0))
        self.import_widget.update_list.connect(self.update_list)

        self.uninstalled_info_widget = UninstalledTabInfo(core, self)
        self.layout().addWidget(self.uninstalled_info_widget)
        # self.uninstalled_info_widget.back.clicked.connect(lambda: self.layout().setCurrentIndex(0))

    def update_list(self, app_name=None):
        self.default_widget.game_list.update_list(app_name)
        self.layout().setCurrentIndex(0)

    def show_uninstalled(self, game: Game):
        self.uninstalled_info_widget.update_game(game)
        self.uninstalled_info_widget.setCurrentIndex(1)
        self.layout().setCurrentIndex(3)

    def show_info(self, game: Game):
        self.game_info.update_game(game, self.default_widget.game_list.dlcs)
        self.game_info.setCurrentIndex(1)
        self.layout().setCurrentIndex(1)


class Games(QWidget):
    def __init__(self, core, parent, offline):
        super(Games, self).__init__(parent=parent)
        self.setLayout(QVBoxLayout())

        self.head_bar = GameListHeadBar(self)
        self.head_bar.setObjectName("head_bar")

        self.game_list = GameList(core, self, offline)

        self.head_bar.search_bar.textChanged.connect(
            lambda: self.game_list.search(self.head_bar.search_bar.text()))

        self.head_bar.filter_changed_signal.connect(self.game_list.filter)
        self.head_bar.filter_changed(self.head_bar.filter.currentIndex())
        self.layout().addWidget(self.head_bar)
        self.layout().addWidget(self.game_list)
        # self.layout().addStretch(1)
        self.head_bar.view.toggled.connect(self.toggle_view)

    def toggle_view(self):
        self.game_list.setCurrentIndex(1 if self.head_bar.view.isChecked() else 0)
        settings = QSettings()
        settings.setValue("icon_view", not self.head_bar.view.isChecked())


class GameListHeadBar(QWidget):
    filter_changed_signal = pyqtSignal(str)

    def __init__(self, parent):
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
                              self.tr("Exclude Origin")])
        self.layout().addWidget(self.filter)

        try:
            self.filter.setCurrentIndex(self.settings.value("filter", 0, int))
        except TypeError:
            self.settings.setValue("filter", 0)

        self.filter.currentIndexChanged.connect(self.filter_changed)
        self.layout().addStretch(1)

        self.import_game = QPushButton(icon("mdi.import"), self.tr("Import Game"))
        self.layout().addWidget(self.import_game)

        self.layout().addStretch(1)

        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("search_bar")
        self.search_bar.setFrame(False)
        icon_label = QLabel()
        icon_label.setPixmap(icon("fa.search").pixmap(QSize(20, 20)))
        self.layout().addWidget(icon_label)
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
        self.filter_changed_signal.emit(["", "installed", "offline", "32bit", "installable"][i])
        self.settings.setValue("filter", i)
