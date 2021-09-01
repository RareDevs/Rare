from logging import getLogger

import psutil
from PyQt5.QtCore import Qt, pyqtSignal, QSettings, QTimer
from PyQt5.QtWidgets import QScrollArea, QWidget, QLabel, QVBoxLayout, QStackedWidget

from custom_legendary.core import LegendaryCore
from rare.components.tabs.games.game_widgets.base_installed_widget import BaseInstalledWidget
from rare.components.tabs.games.game_widgets.installed_icon_widget import GameWidgetInstalled
from rare.components.tabs.games.game_widgets.installed_list_widget import InstalledListWidget
from rare.components.tabs.games.game_widgets.installing_game_widget import InstallingGameWidget
from rare.components.tabs.games.game_widgets.uninstalled_icon_widget import IconWidgetUninstalled
from rare.components.tabs.games.game_widgets.uninstalled_list_widget import ListWidgetUninstalled
from rare.utils.extra_widgets import FlowLayout
from rare.utils.models import InstallOptionsModel
from rare.utils.utils import download_image, get_uninstalled_pixmap, get_pixmap

logger = getLogger("Game list")


class GameList(QStackedWidget):
    install_game = pyqtSignal(InstallOptionsModel)
    show_game_info = pyqtSignal(str)
    update_game = pyqtSignal()
    game_exited = pyqtSignal(str)
    game_started = pyqtSignal(str)
    show_uninstalled_info = pyqtSignal(str)

    running_games = []
    active_game = ("", 0)

    def __init__(self, core: LegendaryCore, parent, offline):
        super(GameList, self).__init__(parent=parent)
        self.core = core
        self.setObjectName("list_widget")
        self.offline = offline
        self.installing_widget = InstallingGameWidget(self.core.get_game("CrabEA"))
        self.settings = QSettings()
        icon_view = self.settings.value("icon_view", True, bool)
        self.procs = []
        for proc in psutil.process_iter():
            try:
                self.procs.append((proc.name(), proc.pid))
            except psutil.ZombieProcess:
                continue
            except psutil.NoSuchProcess:
                continue
            except Exception:
                continue
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

        self.updates = []
        self.widgets = {}
        if not self.offline:
            self.bit32 = [i.app_name for i in self.core.get_game_and_dlc_list(True, "Win32")[0]]
            self.mac_games = [i.app_name for i in self.core.get_game_and_dlc_list(True, "Mac")[0]]
            self.no_assets = [i.app_name for i in self.core.get_non_asset_library_items()[0]]
        else:
            self.bit32 = []
            self.mac_games = []
        self.installed = sorted(self.core.get_installed_list(), key=lambda x: x.title)

        self.installing_widget = InstallingGameWidget(self.core.get_game("CrabEA"))
        self.icon_layout.addWidget(self.installing_widget)
        self.installing_widget.setVisible(False)

        # Installed Games
        for igame in self.installed:
            icon_widget, list_widget = self.add_installed_widget(igame)
            self.icon_layout.addWidget(icon_widget)
            self.list_layout.addWidget(list_widget)
        if not self.offline:
            self.uninstalled_games = []
            installed = [i.app_name for i in self.core.get_installed_list()]
            # get Uninstalled games
            games, self.dlcs = self.core.get_game_and_dlc_list(update_assets=not self.offline)
            for game in games:
                if not game.app_name in installed:
                    self.uninstalled_games.append(game)

            # add uninstalled games
            self.uninstalled_games += self.core.get_non_asset_library_items()[0]
            for game in sorted(self.uninstalled_games, key=lambda x: x.app_title):
                icon_widget, list_widget = self.add_uninstalled_widget(game)

                self.icon_layout.addWidget(icon_widget)
                self.list_layout.addWidget(list_widget)
        else:
            self.dlcs = []

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

        if filter_games := self.settings.value("filter", "", str):
            self.filter(filter_games)

    def start_download(self, app_name):
        self.installing_widget.set_game(self.core.get_game(app_name))
        self.installing_widget.setVisible(True)

    def add_uninstalled_widget(self, game):
        pixmap = get_uninstalled_pixmap(game.app_name)
        if pixmap.isNull():
            logger.info(game.app_title + " has a corrupt image. Reloading...")
            download_image(game, force=True)
            pixmap = get_uninstalled_pixmap(game.app_name)

        icon_widget = IconWidgetUninstalled(game, self.core, pixmap)
        icon_widget.show_uninstalled_info.connect(self.show_install_info)

        list_widget = ListWidgetUninstalled(self.core, game, pixmap)
        list_widget.show_uninstalled_info.connect(self.show_install_info)

        self.widgets[game.app_name] = (icon_widget, list_widget)

        return icon_widget, list_widget

    def add_installed_widget(self, igame):
        pixmap = get_pixmap(igame.app_name)

        if pixmap.isNull():
            logger.info(igame.title + " has a corrupt image.")
            download_image(self.core.get_game(igame.app_name), force=True)
            pixmap = get_pixmap(igame.app_name)

        icon_widget = GameWidgetInstalled(igame, self.core, pixmap, self.offline)
        # self.icon_layout.addWidget(icon_widget)

        list_widget = InstalledListWidget(igame, self.core, pixmap, self.offline)
        # self.list_layout.addWidget(list_widget)

        self.widgets[igame.app_name] = (icon_widget, list_widget)

        icon_widget.show_info.connect(self.show_game_info.emit)
        list_widget.show_info.connect(self.show_game_info.emit)

        icon_widget.launch_signal.connect(self.launch)
        icon_widget.finish_signal.connect(self.finished)
        icon_widget.update_list.connect(self.update_list)
        list_widget.launch_signal.connect(self.launch)
        list_widget.finish_signal.connect(self.finished)
        list_widget.update_list.connect(self.update_list)

        if icon_widget.update_available:
            self.updates.append(igame)

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

        return icon_widget, list_widget

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

    def show_install_info(self, app_name):
        self.show_uninstalled_info.emit(app_name)

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

    def search(self, text: str):
        for t in self.widgets.values():
            for w in t:
                if text.lower() in w.game.app_title.lower() + w.game.app_name.lower():
                    w.setVisible(True)
                else:
                    w.setVisible(False)

    def filter(self, filter="installed"):
        for t in self.widgets.values():
            for w in t:
                if filter == "installed":
                    w.setVisible(self.core.is_installed(w.game.app_name))
                elif filter == "offline":
                    if self.core.is_installed(w.game.app_name):
                        w.setVisible(w.igame.can_run_offline)
                    else:
                        w.setVisible(False)
                elif filter == "32bit" and self.bit32:
                    w.setVisible(w.game.app_name in self.bit32)
                elif filter == "mac":
                    w.setVisible(w.game.app_name in self.mac_games)
                elif filter == "installable":
                    w.setVisible(w.game.app_name not in self.no_assets)
                else:
                    # All visible
                    w.setVisible(True)
        self.settings.setValue("filter", filter)

    def update_list(self, app_name=None):
        # self.settings.setValue("icon_view", icon_view)
        if app_name:
            if widgets := self.widgets.get(app_name):

                # from update
                if self.core.is_installed(widgets[0].game.app_name) and isinstance(widgets[0], BaseInstalledWidget):
                    igame = self.core.get_installed_game(app_name)
                    for w in widgets:
                        w.igame = igame
                        w.update_available = self.core.get_asset(w.game.app_name, True).build_version != igame.version
                    widgets[0].info_label.setText("")
                    widgets[0].info_text = ""
                # new installed
                elif self.core.is_installed(widgets[0].game.app_name) and not isinstance(widgets[0],
                                                                                         BaseInstalledWidget):
                    self.widgets.pop(widgets[0].game.app_name)

                    # QWidget().setLayout(self.icon_layout)

                    igame = self.core.get_installed_game(app_name)
                    self.add_installed_widget(igame)

                    self._update_games()

                # uninstalled
                elif not self.core.is_installed(widgets[0].game.app_name) and isinstance(widgets[0],
                                                                                         BaseInstalledWidget):
                    self.list_layout.removeWidget(widgets[1])
                    self.icon_layout.removeWidget(widgets[0])

                    self.widgets.pop(app_name)

                    game = self.core.get_game(app_name, True)
                    self.add_uninstalled_widget(game)

                    self._update_games()

        else:
            installed_names = [i.app_name for i in self.core.get_installed_list()]
            # get Uninstalled games
            uninstalled_names = []
            games = self.core.get_game_list(True)
            for game in sorted(games, key=lambda x: x.app_title):
                if not game.app_name in installed_names:
                    uninstalled_names.append(game.app_name)

            new_installed_games = list(set(installed_names) - set([i.app_name for i in self.installed]))
            new_uninstalled_games = list(set(uninstalled_names) - set([i.app_name for i in self.uninstalled_games]))

            if (not new_uninstalled_games) and (not new_installed_games):
                return

            if new_installed_games:
                for name in new_installed_games:
                    self.icon_layout.removeWidget(self.widgets[app_name][0])
                    self.list_layout.removeWidget(self.widgets[app_name][1])

                    self.widgets.pop(name)

                    igame = self.core.get_installed_game(name)
                    self.add_installed_widget(igame)

                for name in new_uninstalled_games:
                    self.icon_layout.removeWidget(self.widgets[app_name][0])
                    self.list_layout.removeWidget(self.widgets[app_name][1])

                    self.widgets.pop(name)

                    game = self.core.get_game(name, True)
                    self.add_uninstalled_widget(game)

                for igame in sorted(self.core.get_installed_list(), key=lambda x: x.title):
                    i_widget, list_widget = self.widgets[igame.app_name]

                    self.icon_layout.addWidget(i_widget)
                    self.list_layout.addWidget(list_widget)

                # get Uninstalled games
                games, self.dlcs = self.core.get_game_and_dlc_list()
                for game in sorted(games, key=lambda x: x.app_title):
                    if not game.app_name in installed_names:
                        self.uninstalled_names.append(game)
                for name in uninstalled_names:
                    i_widget, list_widget = self.widgets[name]
                    self.icon_layout.addWidget(i_widget)
                    self.list_layout.addWidget(list_widget)
        self.installing_widget.setVisible(False)

    def _update_games(self):
        # new layouts to remove from old layout
        icon_layout = FlowLayout()
        # QWidget().setLayout(self.list_layout)
        list_layout = QVBoxLayout()

        icon_layout.addWidget(self.installing_widget)
        for igame in sorted(self.core.get_installed_list(), key=lambda x: x.title):
            i_widget, l_widget = self.widgets[igame.app_name]
            icon_layout.addWidget(i_widget)
            list_layout.addWidget(l_widget)

        self.uninstalled_names = []
        installed_names = [i.app_name for i in self.core.get_installed_list()]
        # get Uninstalled games
        games, self.dlcs = self.core.get_game_and_dlc_list()
        for game in sorted(games, key=lambda x: x.app_title):
            if not game.app_name in installed_names:
                self.uninstalled_names.append(game)
        for game in self.uninstalled_names:
            i_widget, list_widget = self.widgets[game.app_name]
            icon_layout.addWidget(i_widget)
            list_layout.addWidget(list_widget)

        QWidget().setLayout(self.icon_layout)
        QWidget().setLayout(self.list_layout)

        self.icon_widget = QWidget()
        self.list_widget = QWidget()

        self.icon_widget.setLayout(icon_layout)
        self.list_widget.setLayout(list_layout)

        self.list_scrollarea.setWidget(QWidget())
        self.icon_scrollarea.setWidget(QWidget())

        self.icon_scrollarea.setWidget(self.icon_widget)
        self.list_scrollarea.setWidget(self.list_widget)

        self.icon_layout = icon_layout
        self.list_layout = list_layout

        self.icon_widget.setLayout(self.icon_layout)
        self.list_widget.setLayout(self.list_layout)

        self.update()
