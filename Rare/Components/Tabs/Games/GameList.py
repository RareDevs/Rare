import os
from logging import getLogger

from PyQt5.QtCore import Qt, pyqtSignal, QSettings
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import *

from Rare.Components.Tabs.Games.GameWidgets.UninstalledListWidget import ListWidgetUninstalled
from Rare.Components.Tabs.Games.GameWidgets.UninstalledIconWidget import IconWidgetUninstalled
from Rare.Components.Tabs.Games.GameWidgets.InstalledIconWidget import GameWidgetInstalled
from Rare.Components.Tabs.Games.GameWidgets.InstalledListWidget import InstalledListWidget
from Rare.utils.Models import InstallOptions
from Rare.utils.QtExtensions import FlowLayout
from Rare.utils.utils import download_image
from custom_legendary.core import LegendaryCore

logger = getLogger("Game list")


class GameList(QStackedWidget):
    install_game = pyqtSignal(InstallOptions)
    show_game_info = pyqtSignal(str)
    update_game = pyqtSignal()

    def __init__(self, core: LegendaryCore):
        super(GameList, self).__init__()
        self.core = core
        self.setObjectName("list_widget")

        self.settings = QSettings()
        icon_view = self.settings.value("icon_view", True, bool)
        self.init_ui(icon_view)

    def init_ui(self, icon_view=True):
        self.icon_scrollarea = QScrollArea()
        self.icon_widget = QWidget()
        self.list_scrollarea = QScrollArea()
        self.list_widget = QWidget()

        self.icon_scrollarea.setWidgetResizable(True)
        self.icon_scrollarea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.list_scrollarea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.icon_layout = FlowLayout()
        self.list_layout = QVBoxLayout()

        IMAGE_DIR = self.settings.value("img_dir", os.path.expanduser("~/.cache/rare"), str)
        self.updates = []
        self.widgets = {}

        # Installed Games
        for game in sorted(self.core.get_installed_list(), key=lambda x: x.title):
            if os.path.exists(f"{IMAGE_DIR}/{game.app_name}/FinalArt.png"):
                pixmap = QPixmap(f"{IMAGE_DIR}/{game.app_name}/FinalArt.png")
            elif os.path.exists(f"{IMAGE_DIR}/{game.app_name}/DieselGameBoxTall.png"):
                pixmap = QPixmap(f"{IMAGE_DIR}/{game.app_name}/DieselGameBoxTall.png")
            elif os.path.exists(f"{IMAGE_DIR}/{game.app_name}/DieselGameBoxLogo.png"):
                pixmap = QPixmap(f"{IMAGE_DIR}/{game.app_name}/DieselGameBoxLogo.png")
            else:
                logger.warning(f"No Image found: {game.title}")
                pixmap = None

            if pixmap.isNull():
                logger.info(game.title + " has a corrupt image.")
                download_image(game, force=True)
                pixmap = QPixmap(f"{IMAGE_DIR}/{game.app_name}/DieselGameBoxTall.png")

            icon_widget = GameWidgetInstalled(game, self.core, pixmap)
            list_widget = InstalledListWidget(game, self.core, pixmap)

            icon_widget.show_info.connect(self.show_game_info.emit)
            list_widget.show_info.connect(self.show_game_info.emit)

            icon_widget.launch_signal.connect(self.launch)
            icon_widget.finish_signal.connect(self.finished)
            list_widget.launch_signal.connect(self.launch)
            list_widget.launch_signal.connect(self.finished)

            self.icon_layout.addWidget(icon_widget)
            self.list_layout.addWidget(list_widget)

            if icon_widget.update_available:
                self.updates.append(game)

            self.widgets[game.app_name] = (icon_widget, list_widget)

        uninstalled_games = []
        installed = [i.app_name for i in self.core.get_installed_list()]
        # get Uninstalled games
        for game in sorted(self.core.get_game_list(), key=lambda x: x.app_title):
            if not game.app_name in installed:
                uninstalled_games.append(game)

        for game in uninstalled_games:
            if os.path.exists(f"{IMAGE_DIR}/{game.app_name}/UninstalledArt.png"):
                pixmap = QPixmap(f"{IMAGE_DIR}/{game.app_name}/UninstalledArt.png")

                if pixmap.isNull():
                    logger.info(game.app_title + " has a corrupt image.")
                    download_image(game, force=True)
                    pixmap = QPixmap(f"{IMAGE_DIR}/{game.app_name}/UninstalledArt.png")

            else:
                logger.warning(f"No Image found: {self.game.app_title}")
                download_image(game, force=True)
                pixmap = QPixmap(f"{IMAGE_DIR}/{game.app_name}/UninstalledArt.png")

            icon_widget = IconWidgetUninstalled(game, self.core, pixmap)
            icon_widget.install_game.connect(self.install_game.emit)

            list_widget = ListWidgetUninstalled(self.core, game, pixmap)
            list_widget.install_game.connect(self.install_game.emit)

            self.icon_layout.addWidget(icon_widget)
            self.list_layout.addWidget(list_widget)

            self.widgets[game.app_name] = (icon_widget, list_widget)

        self.list_layout.addStretch(1)
        self.icon_widget.setLayout(self.icon_layout)
        self.list_widget.setLayout(self.list_layout)

        self.icon_scrollarea.setWidget(self.icon_widget)
        self.list_scrollarea.setWidget(self.list_widget)

        self.addWidget(self.icon_scrollarea)
        self.addWidget(self.list_scrollarea)

        if not icon_view:
            self.setCurrentIndex(1)

        if self.settings.value("installed_only", False, bool):
            self.installed_only(True)

    def finished(self, app_name):
        self.widgets[app_name][0].info_text = ""
        self.widgets[app_name][0].info_label.setText("")
        self.widgets[app_name][1].launch_button.setDisabled(False)
        self.widgets[app_name][1].launch_button.setText(self.tr("Launch"))

    def launch(self, app_name):
        self.widgets[app_name][0].info_text = self.tr("Game running")
        self.widgets[app_name][1].launch_button.setDisabled(True)
        self.widgets[app_name][1].launch_button.setText(self.tr("Game running"))

    def filter(self, text: str):
        for t in self.widgets.values():
            for w in t:
                if text.lower() in w.game.app_title.lower() + w.game.app_name.lower():
                    w.setVisible(True)
                else:
                    w.setVisible(False)

    def installed_only(self, i_o: bool):
        for t in self.widgets.values():
            for w in t:
                w.setVisible(not (not self.core.is_installed(w.game.app_name) and i_o))
        self.settings.setValue("installed_only", i_o)

    def update_list(self, icon_view=True):
        self.settings.setValue("icon_view", icon_view)
        self.removeWidget(self.icon_scrollarea)
        self.removeWidget(self.list_scrollarea)
        self.init_ui(icon_view)
        self.update()

    def import_game(self):
        pass
