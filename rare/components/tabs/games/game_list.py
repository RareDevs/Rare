import os
from logging import getLogger

import psutil
from PyQt5.QtCore import Qt, pyqtSignal, QSettings, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import *

from custom_legendary.core import LegendaryCore
from rare.components.tabs.games.game_widgets.installed_icon_widget import GameWidgetInstalled
from rare.components.tabs.games.game_widgets.installed_list_widget import InstalledListWidget
from rare.components.tabs.games.game_widgets.uninstalled_icon_widget import IconWidgetUninstalled
from rare.components.tabs.games.game_widgets.uninstalled_list_widget import ListWidgetUninstalled
from rare.utils.extra_widgets import FlowLayout
from rare.utils.models import InstallOptions
from rare.utils.utils import download_image

logger = getLogger("Game list")


class GameList(QStackedWidget):
    install_game = pyqtSignal(InstallOptions)
    show_game_info = pyqtSignal(str)
    update_game = pyqtSignal()
    game_exited = pyqtSignal(str)
    game_started = pyqtSignal(str)

    running_games = []
    active_game = ("", 0)

    def __init__(self, core: LegendaryCore, parent, offline):
        super(GameList, self).__init__(parent=parent)
        self.core = core
        self.setObjectName("list_widget")
        self.offline = offline

        self.settings = QSettings()
        icon_view = self.settings.value("icon_view", True, bool)
        self.procs = [(proc.name(), proc.pid) for proc in psutil.process_iter()]
        self.init_ui(icon_view)

    def init_ui(self, icon_view=True):
        self.icon_scrollarea = QScrollArea(parent=self)
        self.icon_widget = QWidget(parent=self.icon_scrollarea)
        self.list_scrollarea = QScrollArea(parent=self)
        self.list_widget = QWidget(parent=self.list_scrollarea)

        self.icon_scrollarea.setWidgetResizable(True)
        self.icon_scrollarea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.list_scrollarea.setWidgetResizable(True)
        self.list_scrollarea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.info_text = self.tr("Installed Games: {}    Available Games: {}").format(
            len(self.core.get_installed_list()),
            len(self.core.get_game_list(update_assets=True)))

        self.icon_parent_layout = QVBoxLayout()
        self.icon_parent_layout.addWidget(QLabel(self.info_text))

        self.icon_layout = FlowLayout()
        self.list_layout = QVBoxLayout()
        self.list_layout.addWidget(QLabel(self.info_text))

        IMAGE_DIR = self.settings.value("img_dir", os.path.expanduser("~/.cache/rare/images"), str)
        self.updates = []
        self.widgets = {}

        self.installed = sorted(self.core.get_installed_list(), key=lambda x: x.title)

        # Installed Games
        for igame in self.installed:
            if os.path.exists(f"{IMAGE_DIR}/{igame.app_name}/FinalArt.png"):
                pixmap = QPixmap(f"{IMAGE_DIR}/{igame.app_name}/FinalArt.png")
            elif os.path.exists(f"{IMAGE_DIR}/{igame.app_name}/DieselGameBoxTall.png"):
                pixmap = QPixmap(f"{IMAGE_DIR}/{igame.app_name}/DieselGameBoxTall.png")
            elif os.path.exists(f"{IMAGE_DIR}/{igame.app_name}/DieselGameBoxLogo.png"):
                pixmap = QPixmap(f"{IMAGE_DIR}/{igame.app_name}/DieselGameBoxLogo.png")
            else:
                logger.warning(f"No Image found: {igame.title}")
                pixmap = None

            if pixmap.isNull():
                logger.info(igame.title + " has a corrupt image.")
                download_image(igame, force=True)
                pixmap = QPixmap(f"{IMAGE_DIR}/{igame.app_name}/DieselGameBoxTall.png")

            icon_widget = GameWidgetInstalled(igame, self.core, pixmap, self.offline)
            self.icon_layout.addWidget(icon_widget)

            list_widget = InstalledListWidget(igame, self.core, pixmap, self.offline)
            self.list_layout.addWidget(list_widget)

            icon_widget.show_info.connect(self.show_game_info.emit)
            list_widget.show_info.connect(self.show_game_info.emit)

            icon_widget.launch_signal.connect(self.launch)
            icon_widget.finish_signal.connect(self.finished)
            icon_widget.update_list.connect(lambda: self.update_list(self.settings.value("icon_view", True, bool)))
            list_widget.launch_signal.connect(self.launch)
            list_widget.finish_signal.connect(self.finished)
            list_widget.update_list.connect(lambda: self.update_list(self.settings.value("icon_view", True, bool)))

            if icon_widget.update_available:
                self.updates.append(igame)

            self.widgets[igame.app_name] = (icon_widget, list_widget)
            active, pid = self.check_for_active_game(igame)
            if active:
                # Only one game works: Workaround for Satisfactory EA and Exp.
                self.launch(igame.app_name)
                icon_widget.game_running = True
                list_widget.game_running = True
                self.active_game = (igame.app_name, pid)
                self.timer = QTimer()
                self.timer.timeout.connect(self.is_finished)
                self.timer.start(10000)

        self.uninstalled_games = []
        installed = [i.app_name for i in self.core.get_installed_list()]
        # get Uninstalled games
        games, self.dlcs = self.core.get_game_and_dlc_list()
        for game in sorted(games, key=lambda x: x.app_title):
            if not game.app_name in installed:
                self.uninstalled_games.append(game)

        # add uninstalled games
        for igame in self.uninstalled_games:
            if os.path.exists(f"{IMAGE_DIR}/{igame.app_name}/UninstalledArt.png"):
                pixmap = QPixmap(f"{IMAGE_DIR}/{igame.app_name}/UninstalledArt.png")

                if pixmap.isNull():
                    logger.info(igame.app_title + " has a corrupt image.")
                    download_image(igame, force=True)
                    pixmap = QPixmap(f"{IMAGE_DIR}/{igame.app_name}/UninstalledArt.png")
            else:
                logger.warning(f"No Image found: {igame.app_title}")
                download_image(igame, force=True)
                pixmap = QPixmap(f"{IMAGE_DIR}/{igame.app_name}/UninstalledArt.png")

            icon_widget = IconWidgetUninstalled(igame, self.core, pixmap)
            icon_widget.install_game.connect(self.install)

            list_widget = ListWidgetUninstalled(self.core, igame, pixmap)
            list_widget.install_game.connect(self.install)

            self.icon_layout.addWidget(icon_widget)
            self.list_layout.addWidget(list_widget)

            self.widgets[igame.app_name] = (icon_widget, list_widget)

        self.icon_parent_layout.addLayout(self.icon_layout)
        self.icon_parent_layout.addStretch(1)
        self.list_layout.addStretch(1)
        self.icon_widget.setLayout(self.icon_parent_layout)
        self.list_widget.setLayout(self.list_layout)

        self.icon_scrollarea.setWidget(self.icon_widget)
        self.list_scrollarea.setWidget(self.list_widget)

        self.addWidget(self.icon_scrollarea)
        self.addWidget(self.list_scrollarea)

        if not icon_view:
            self.setCurrentIndex(1)

        if self.settings.value("installed_only", False, bool):
            self.installed_only(True)

    def is_finished(self):
        if psutil.pid_exists(self.active_game[1]):
            self.timer.start(10000)
        else:
            self.finished(self.active_game[0])
            del self.timer

    def check_for_active_game(self, igame):
        executable = igame.executable.split("/")[-1].split("\\")[-1]
        if executable.endswith(".exe"):
            executable = executable[:-4]  # remove .exe

        for i, pid in self.procs:
            if executable in i:
                # Workaround for Satisfactory: Check Cmdline args
                if igame.app_name in ["CrabEA", "CrabTest"]:
                    p = psutil.Process(pid)
                    if not igame.install_path.split("/")[-1].split("\\")[-1] in " ".join(p.cmdline()):
                        return False, 0
                return True, pid
        return False, 0

    def install(self, options: InstallOptions):
        icon_widget, list_widget = self.widgets[options.app_name]
        icon_widget.mousePressEvent = lambda e: None
        icon_widget.installing = True
        list_widget.install_button.setDisabled(True)
        list_widget.installing = True
        self.install_game.emit(options)

    def finished(self, app_name):
        self.running_games.remove(app_name)
        self.active_game = ("", 0)
        self.widgets[app_name][0].info_text = ""
        self.widgets[app_name][0].info_label.setText("")
        self.widgets[app_name][1].launch_button.setDisabled(False)
        self.widgets[app_name][1].launch_button.setText(self.tr("Launch"))
        if self.widgets[app_name][0].game.supports_cloud_saves:
            if not self.settings.value(f"{app_name}/auto_sync_cloud", True, bool) \
                    and not self.settings.value("auto_sync_cloud", True, bool):
                logger.info("Auto saves disabled")
                return

            self.widgets[app_name][0].info_text = self.tr("Sync CLoud saves")
            self.widgets[app_name][0].info_label.setText(self.tr("Sync CLoud saves"))
            self.widgets[app_name][1].info_label.setText(self.tr("Sync CLoud saves"))
        self.game_exited.emit(app_name)

    def launch(self, app_name):
        self.running_games.append(app_name)
        self.game_started.emit(app_name)
        self.widgets[app_name][0].info_text = self.tr("Game running")
        self.widgets[app_name][0].info_label.setText(self.tr("Game running"))
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

        uninstalled_games = []
        installed = [i.app_name for i in self.core.get_installed_list()]
        # get Uninstalled games
        games = self.core.get_game_list(True)
        for game in sorted(games, key=lambda x: x.app_title):
            if not game.app_name in installed:
                uninstalled_games.append(game.app_name)

        # get new uninstalled/ installed games that changed
        new_installed_games = list(set(installed) - set([i.app_name for i in self.installed]))
        new_uninstalled_games = list(set(uninstalled_games) - set([i.app_name for i in self.uninstalled_games]))

        if not new_uninstalled_games and not new_installed_games:
            return

        self.removeWidget(self.icon_scrollarea)
        self.removeWidget(self.list_scrollarea)
        self.init_ui(icon_view)
        self.update()
