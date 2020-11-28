import os
import signal
from logging import getLogger

from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QLineEdit, QPushButton, QFormLayout, QGroupBox, \
    QComboBox, QHBoxLayout, QTableWidget, QTableWidgetItem
from legendary.core import LegendaryCore

from Rare.GameWidget import GameWidget, UninstalledGameWidget
from Rare.utils import legendaryConfig, RareConfig
from Rare.utils.legendaryUtils import logout, get_updates, get_name, update

logger = getLogger("TabWidgets")


class BrowserTab(QWebEngineView):
    def __init__(self, parent):
        super(BrowserTab, self).__init__(parent=parent)
        self.profile = QWebEngineProfile("storage", self)
        self.webpage = QWebEnginePage(self.profile, self)
        self.setPage(self.webpage)
        self.load(QUrl("https://www.epicgames.com/store/"))
        self.show()

    def createWindow(self, QWebEnginePage_WebWindowType):
        return self


class Settings(QScrollArea):
    def __init__(self, parent):
        super(Settings, self).__init__(parent=parent)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # Settings
        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel("<h1>Rare Settings</h1>"))
        self.logged_in_as = QLabel(f"Logged in as {get_name()}")
        self.get_legendary_config()
        self.gen_form_legendary()
        self.gen_form_rare()

        if RareConfig.get_config()["Rare"].get("theme") == "dark":
            self.parent().parent().setStyleSheet(open("../Styles/style.qss").read())
            self.style_combo_box.setCurrentIndex(1)

        self.logout_button = QPushButton("Logout")
        self.logout_button.clicked.connect(self.logout)
        self.layout.addWidget(self.logged_in_as)
        self.layout.addWidget(self.rare_form_group_box)
        self.update_rare_button = QPushButton("Update Rare Settings")
        self.update_rare_button.clicked.connect(self.update_rare_settings)
        self.layout.addWidget(self.update_rare_button)

        self.layout.addWidget(self.form_group_box)
        self.update_legendary_button = QPushButton("Update Legendary Settings")
        self.update_legendary_button.clicked.connect(self.update_legendary_settings)
        self.layout.addWidget(self.update_legendary_button)
        self.layout.addStretch(1)
        self.layout.addWidget(self.logout_button)

        self.info_label = QLabel("<h2>Credits</h2>")
        self.infotext = QLabel("Developers : Dummerle, CommandMC\nLegendary Dev: Derrod\nLicence: GPL v.3")

        self.layout.addWidget(self.info_label)
        self.layout.addWidget(self.infotext)

        self.setLayout(self.layout)

    def update_rare_settings(self):
        logger.info("Update Rare settings")
        config = {"Rare": {}}
        if self.style_combo_box.currentIndex() == 1:
            self.parent().parent().parent().setStyleSheet(open("../Styles/style.qss").read())
            config["Rare"]["theme"] = "dark"
        else:
            self.parent().parent().parent().setStyleSheet("")
            config["Rare"]["theme"] = "light"

        RareConfig.set_config(config)

    def update_legendary_settings(self):
        print("Legendary update")
        self.config["Legendary"]["wine_executable"] = self.lgd_conf_wine_exec.text()
        self.config["Legendary"]["wine_prefix"] = self.lgd_conf_wine_prefix.text()
        self.config["Legendary"]["locale"] = self.lgd_conf_locale.text()
        # self.config["default.env"] = self.lgd_conf_env_vars.toPlainText()
        self.config["default.env"] = {}
        for row in range(self.table.rowCount()):
            self.config["default.env"][self.table.item(row, 0).text()] = self.table.item(row, 1).text()
        print(self.config["default.env"])
        legendaryConfig.set_config(self.config)

    def logout(self):
        logout()
        exit(0)

    def gen_form_legendary(self):
        # Default Config
        if not self.config.get("Legendary"):
            self.config["Legendary"] = {}
        if not self.config["Legendary"].get("wine_executable"):
            self.config["Legendary"]["wine_executable"] = "wine"
        if not self.config["Legendary"].get("wine_prefix"):
            self.config["Legendary"]["wine_prefix"] = f"{os.path.expanduser('~')}/.wine"
        if not self.config["Legendary"].get("locale"):
            self.config["Legendary"]["locale"] = "en-US"

        env_vars = self.config["default.env"]
        self.table = QTableWidget(len(env_vars), 2)

        self.table.setHorizontalHeaderLabels(["Variable", "Value"])
        for i, label in enumerate(env_vars):
            self.table.setItem(i, 0, QTableWidgetItem(label))
            self.table.setItem(i, 1, QTableWidgetItem(env_vars[label]))

        self.form_group_box = QGroupBox("Legendary Defaults")
        self.form = QFormLayout()

        self.lgd_conf_wine_prefix = QLineEdit(self.config["Legendary"]["wine_prefix"])
        self.lgd_conf_wine_exec = QLineEdit(self.config["Legendary"]["wine_executable"])
        self.lgd_conf_locale = QLineEdit(self.config["Legendary"]["locale"])

        self.add_button = QPushButton("Add Environment Variable")
        self.delete_env_var = QPushButton("Delete selected Variable")
        self.delete_env_var.clicked.connect(self.delete_var)
        self.add_button.clicked.connect(self.add_variable)
        self.form.addRow(QLabel("Default Wineprefix"), self.lgd_conf_wine_prefix)
        self.form.addRow(QLabel("Wine executable"), self.lgd_conf_wine_exec)
        self.form.addRow(QLabel("Environment Variables"), self.table)
        self.form.addRow(QLabel("Add Variable"), self.add_button)
        self.form.addRow(QLabel("Delete Variable"), self.delete_env_var)
        self.form.addRow(QLabel("Locale"), self.lgd_conf_locale)

        self.form_group_box.setLayout(self.form)

    def add_variable(self):
        print("add row")
        self.table.insertRow(self.table.rowCount())
        self.table.setItem(self.table.rowCount(), 0, QTableWidgetItem(""))
        self.table.setItem(self.table.rowCount(), 1, QTableWidgetItem(""))

    def delete_var(self):
        self.table.removeRow(self.table.currentRow())

    def gen_form_rare(self):
        self.rare_form_group_box = QGroupBox("Rare Settings")
        self.rare_form = QFormLayout()
        self.style_combo_box = QComboBox()
        self.style_combo_box.addItems(["Light", "Dark"])
        self.rare_form.addRow(QLabel("Style"), self.style_combo_box)

        self.rare_form_group_box.setLayout(self.rare_form)

    def get_legendary_config(self):
        self.config = legendaryConfig.get_config()


class GameListInstalled(QScrollArea):
    def __init__(self, parent, core: LegendaryCore):
        super(GameListInstalled, self).__init__(parent=parent)
        self.widget = QWidget()
        self.core = core
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.layout = QVBoxLayout()
        self.widgets = {}
        for i in sorted(core.get_installed_list(), key=lambda game: game.title):
            widget = GameWidget(i, core)
            widget.signal.connect(self.remove_game)
            self.widgets[i.app_name] = widget
            self.layout.addWidget(widget)
        self.widget.setLayout(self.layout)
        self.setWidget(self.widget)

    def remove_game(self, app_name: str):
        logger.info(f"Uninstall {app_name}")
        self.widgets[app_name].setVisible(False)
        self.layout.removeWidget(self.widgets[app_name])
        self.widgets[app_name].deleteLater()
        self.widgets.pop(app_name)


class GameListUninstalled(QScrollArea):
    def __init__(self, parent, core: LegendaryCore):
        super(GameListUninstalled, self).__init__(parent=parent)
        self.widget = QWidget()
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.layout = QVBoxLayout()

        self.filter = QLineEdit()
        self.filter.textChanged.connect(self.filter_games)
        self.filter.setPlaceholderText("Filter Games")
        self.layout.addWidget(self.filter)

        self.widgets_uninstalled = []
        games = []
        installed = [i.app_name for i in core.get_installed_list()]
        for game in core.get_game_list():
            if not game.app_name in installed:
                games.append(game)
        games = sorted(games, key=lambda x: x.app_title)
        for game in games:
            game_widget = UninstalledGameWidget(game)
            self.layout.addWidget(game_widget)
            self.widgets_uninstalled.append(game_widget)

        self.layout.addStretch(1)
        self.widget.setLayout(self.layout)
        self.setWidget(self.widget)

    def filter_games(self):
        for i in self.widgets_uninstalled:
            if self.filter.text().lower() in i.game.app_title.lower() + i.game.app_name.lower():
                i.setVisible(True)
            else:
                i.setVisible(False)


class UpdateList(QWidget):
    class UpdateWidget(QWidget):
        def __init__(self, game):
            super().__init__()
            self.updating = False
            self.game = game
            self.layout = QHBoxLayout()
            self.label = QLabel("Update available for " + self.game.title)
            self.button = QPushButton("Update")
            self.button.clicked.connect(self.update_game)

            self.layout.addWidget(self.label)
            self.layout.addWidget(self.button)

            self.setLayout(self.layout)

        def update_game(self):
            if not self.updating:
                logger.info("Update " + self.game.title)
                self.proc = update(self.game.app_name)
                self.button.setText("Cancel")
                self.updating = True
            else:
                logger.info("Terminate process")
                self.proc.send_signal(signal.SIGINT)
                self.button.setText("Update")
                self.updating = False

    def __init__(self, parent):
        super(UpdateList, self).__init__(parent=parent)
        self.layout = QVBoxLayout()
        updates = get_updates()
        if updates:
            for game in get_updates():
                self.layout.addWidget(self.UpdateWidget(game))
        else:
            self.layout.addWidget(QLabel("No updates available"))
        self.layout.addStretch(1)
        self.setLayout(self.layout)

        # TODO Remove when finished
