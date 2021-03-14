import os

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QComboBox, QFileDialog, QPushButton, QMessageBox
from legendary.core import LegendaryCore
from legendary.models.game import InstalledGame, Game

from Rare.Components.Tabs.Settings.Linux import LinuxSettings
from Rare.Components.Tabs.Settings.SettingsWidget import SettingsWidget
from Rare.utils.QtExtensions import PathEdit


class GameSettings(QWidget):
    game: Game
    igame: InstalledGame
    # variable to no update when changing game
    change = False

    def __init__(self, core: LegendaryCore):
        super(GameSettings, self).__init__()
        self.core = core
        self.layout = QVBoxLayout()
        self.title = QLabel("Error")
        self.layout.addWidget(self.title)

        self.offline = QComboBox()
        self.offline.addItems(["unset", "true", "false"])
        self.offline_widget = SettingsWidget(self.tr("Launch Game offline"), self.offline)
        self.offline.currentIndexChanged.connect(self.update_offline)

        self.skip_update = QComboBox()
        self.skip_update.addItems(["unset", "true", "false"])
        self.skip_update_widget = SettingsWidget(self.tr("Skip update check before launching"), self.skip_update)
        self.layout.addWidget(self.skip_update_widget)
        self.skip_update.currentIndexChanged.connect(self.update_skip_update)

        self.layout.addWidget(self.offline_widget)

        if os.name != "nt":
            self.linux_settings = LinuxAppSettings(core)
            self.layout.addWidget(self.linux_settings)

            self.possible_proton_wrappers = []
            for i in os.listdir(os.path.expanduser("~/.steam/steam/steamapps/common")):
                if i.startswith("Proton"):
                    wrapper = '"' + os.path.join(os.path.expanduser("~/.steam/steam/steamapps/common"), i,
                                                 "proton") + '" run'
                    self.possible_proton_wrappers.append(wrapper)
            self.select_proton = QComboBox()
            self.select_proton.addItems(["Don't use Proton"] + self.possible_proton_wrappers)
            self.select_proton.currentIndexChanged.connect(self.change_proton)
            self.select_proton_widget = SettingsWidget(self.tr("Proton Wrapper"), self.select_proton)
            self.layout.addWidget(self.select_proton_widget)
            self.proton_prefix = PathEdit("x", QFileDialog.DirectoryOnly)
            self.proton_prefix_accept_button = QPushButton(self.tr("Save"))
            self.proton_prefix_accept_button.clicked.connect(self.update_prefix)
            self.proton_prefix_widget = SettingsWidget(self.tr("Proton prefix"), self.proton_prefix,
                                                       self.proton_prefix_accept_button)
            self.layout.addWidget(self.proton_prefix_widget)

        # startparams, skip_update_check

        self.layout.addStretch(1)
        self.setLayout(self.layout)

    def update_offline(self, i):
        if self.change:
            # remove section
            if i == 0:
                if self.game.app_name in self.core.lgd.config.sections():
                    if self.core.lgd.config.get(f"{self.game.app_name}", "offline", fallback="") != "":
                        self.core.lgd.config.remove_option(self.game.app_name, "offline")
                if self.core.lgd.config[self.game.app_name] == {}:
                    self.core.lgd.config.remove_section(self.game.app_name)
            elif i == 1:
                self.core.lgd.config[self.game.app_name] = {}
                self.core.lgd.config.set(self.game.app_name, "offline", "true")
            elif i == 2:
                self.core.lgd.config[self.game.app_name] = {}
                self.core.lgd.config.set(self.game.app_name, "offline", "false")
            self.core.lgd.save_config()

    def update_skip_update(self, i):
        if self.change:
            # remove section
            if i == 0:
                if self.game.app_name in self.core.lgd.config.sections():
                    if self.core.lgd.config.get(f"{self.game.app_name}", "skip_update_check", fallback="") != "":
                        self.core.lgd.config.remove_option(self.game.app_name, "skip_update_check")
                if self.core.lgd.config[self.game.app_name] == {}:
                    self.core.lgd.config.remove_section(self.game.app_name)
            elif i == 1:
                self.core.lgd.config[self.game.app_name] = {}
                self.core.lgd.config.set(self.game.app_name, "skip_update_check", "true")
            elif i == 2:
                self.core.lgd.config[self.game.app_name] = {}
                self.core.lgd.config.set(self.game.app_name, "skip_update_check", "false")
            self.core.lgd.save_config()

    def change_proton(self, i):
        if self.change:
            # Dont use Proton
            if i == 0:
                self.proton_prefix_widget.setVisible(False)
                if f"{self.game.app_name}" in self.core.lgd.config.sections():
                    if self.core.lgd.config.get(f"{self.game.app_name}", "wrapper", fallback="") != "":
                        self.core.lgd.config.remove_option(self.game.app_name, "wrapper")
                    if self.core.lgd.config.get(f"{self.game.app_name}", "no_wine", fallback="") != "":
                        self.core.lgd.config.remove_option(self.game.app_name, "no_wine")
                    if self.core.lgd.config[self.game.app_name] == {}:
                        self.core.lgd.config.remove_section(self.game.app_name)
                if f"{self.game.app_name}.env" in self.core.lgd.config.sections():
                    if self.core.lgd.config.get(f"{self.game.app_name}.env", "STEAM_COMPAT_DATA_PATH",
                                                fallback="") != "":
                        self.core.lgd.config.remove_option(f"{self.game.app_name}.env", "STEAM_COMPAT_DATA_PATH")
                    if self.core.lgd.config[self.game.app_name + ".env"] == {}:
                        self.core.lgd.config.remove_section(self.game.app_name + ".env")
            else:
                self.proton_prefix_widget.setVisible(True)
                wrapper = self.possible_proton_wrappers[i - 1]
                if not self.game.app_name in self.core.lgd.config.sections():
                    self.core.lgd.config[self.game.app_name] = {}
                if not self.game.app_name + ".env" in self.core.lgd.config.sections():
                    self.core.lgd.config[self.game.app_name + ".env"] = {}
                self.core.lgd.config.set(self.game.app_name, "wrapper", wrapper)
                self.core.lgd.config.set(self.game.app_name, "no_wine", "true")
                self.core.lgd.config.set(self.game.app_name + ".env", "STEAM_COMPAT_DATA_PATH",
                                         os.path.expanduser("~/.proton"))
                self.proton_prefix.text_edit.setText(os.path.expanduser("~/.proton"))

                # Dont use Wine
                self.linux_settings.select_wine_exec.setText("")
                self.linux_settings.save_wineexec()
                self.linux_settings.select_path.text_edit.setText("")
                self.linux_settings.save_wineprefix()

        self.core.lgd.save_config()

    def update_prefix(self):
        text = self.proton_prefix.text()
        if text == "":
            text = os.path.expanduser("~/.proton")
            self.proton_prefix.text_edit.setText(text)
        if not os.path.exists(text):
            try:
                os.makedirs(text)
            except PermissionError:
                QMessageBox.warning(self, "Warning", self.tr("No permission to create folder"))
                text = os.path.expanduser("~/.proton")
                self.proton_prefix.text_edit.setText(text)

        self.core.lgd.config.set(self.game.app_name + ".env", "STEAM_COMPAT_DATA_PATH", text)
        self.core.lgd.save_config()

    def update_game(self, app_name):
        self.change = False
        self.game = self.core.get_game(app_name)
        self.igame = self.core.get_installed_game(app_name)

        if self.igame.can_run_offline:
            offline = self.core.lgd.config.get(self.game.app_name, "offline", fallback="unset")
            if offline == "true":
                self.offline.setCurrentIndex(1)
            elif offline == "false":
                self.offline.setCurrentIndex(2)
            else:
                self.offline.setCurrentIndex(0)

            self.offline_widget.setVisible(True)
        else:
            self.offline_widget.setVisible(False)

        skip_update = self.core.lgd.config.get(self.game.app_name, "skip_update_check", fallback="unset")
        if skip_update == "true":
            self.skip_update.setCurrentIndex(1)
        elif skip_update == "false":
            self.skip_update.setCurrentIndex(2)
        else:
            self.skip_update.setCurrentIndex(0)

        self.title.setText(f"<h2>{self.game.app_title}</h2>")
        if os.name != "nt":
            self.linux_settings.update_game(app_name)
            self.linux_settings.dxvk_widget.update_settings(app_name)
            proton = self.core.lgd.config.get(f"{app_name}", "wrapper", fallback="").replace('"', "")
            if proton != "":
                self.proton_prefix_widget.setVisible(True)
                self.select_proton.setCurrentText(f'"{proton.replace(" run", "")}" run')
                proton_prefix = self.core.lgd.config.get(f"{app_name}.env", "STEAM_COMPAT_DATA_PATH",
                                                         fallback=self.tr(
                                                             "Please select path for proton prefix"))
                self.proton_prefix.text_edit.setText(proton_prefix)

            else:
                self.select_proton.setCurrentIndex(0)
                self.proton_prefix_widget.setVisible(False)
        self.change = True


class LinuxAppSettings(LinuxSettings):
    def __init__(self, core):
        super(LinuxAppSettings, self).__init__(core, "app")

    def update_game(self, app_name):
        self.name = app_name
        self.select_path.text_edit.setText(self.core.lgd.config.get(self.name, "wine_prefix", fallback=""))
        self.select_wine_exec.setText(self.core.lgd.config.get(self.name, "wine_executable", fallback=""))
        self.dxvk_widget.name = app_name
        self.dxvk_widget.more_settings_widget.name = app_name
