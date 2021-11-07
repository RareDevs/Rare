import os
import platform
from typing import Tuple

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QWidget, QFileDialog, QMessageBox

from legendary.core import LegendaryCore
from legendary.models.game import InstalledGame, Game
from rare.components.tabs.settings.linux import LinuxSettings
from rare.ui.components.tabs.games.game_info.game_settings import Ui_GameSettings
from rare.utils.extra_widgets import PathEdit


def find_proton_wrappers():
    possible_proton_wrappers = []
    compatibilitytools_dirs = [
        os.path.expanduser("~/.steam/steam/steamapps/common"),
        "/usr/share/steam/compatibilitytools.d",
        os.path.expanduser("~/.steam/compatibilitytools.d"),
        os.path.expanduser("~/.steam/root/compatibilitytools.d")
    ]
    for c in compatibilitytools_dirs:
        if os.path.exists(c):
            for i in os.listdir(c):
                proton = os.path.join(c, i, "proton")
                compatibilitytool = os.path.join(c, i, "compatibilitytool.vdf")
                toolmanifest = os.path.join(c, i, "toolmanifest.vdf")
                if os.path.exists(proton) and (os.path.exists(compatibilitytool) or os.path.exists(toolmanifest)):
                    wrapper = '"' + proton + '" run'
                    possible_proton_wrappers.append(wrapper)
    if not possible_proton_wrappers:
        print("Unable to find any Proton version")
    return possible_proton_wrappers


class GameSettings(QWidget, Ui_GameSettings):
    game: Game
    igame: InstalledGame

    # variable to no update when changing game
    change = False

    def __init__(self, core: LegendaryCore, parent):
        super(GameSettings, self).__init__(parent=parent)
        self.setupUi(self)

        self.core = core
        self.settings = QSettings()
        self.offline.currentIndexChanged.connect(
            lambda x: self.update_combobox(x, "offline")
        )
        self.skip_update.currentIndexChanged.connect(
            lambda x: self.update_combobox(x, "skip_update_check")
        )
        self.cloud_sync.stateChanged.connect(
            lambda: self.settings.setValue(f"{self.game.app_name}/auto_sync_cloud", self.cloud_sync.isChecked())
        )
        self.launch_params.textChanged.connect(lambda: self.launch_params_button.setEnabled(True))
        self.launch_params_button.clicked.connect(
            lambda: self.save_line_edit("start_params", self.launch_params.text())
        )
        self.launch_params_button.setEnabled(False)
        self.wrapper.textChanged.connect(lambda: self.wrapper_button.setEnabled(True))
        self.wrapper_button.clicked.connect(
            lambda: self.save_line_edit("wrapper", self.wrapper.text())
        )
        self.wrapper_button.setEnabled(False)

        if platform.system() != "Windows":
            self.possible_proton_wrappers = find_proton_wrappers()

            self.proton_wrapper.addItems(self.possible_proton_wrappers)
            self.proton_wrapper.currentIndexChanged.connect(self.change_proton)

            self.proton_prefix = PathEdit(
                file_type=QFileDialog.DirectoryOnly,
                edit_func=self.proton_prefix_edit,
                save_func=self.proton_prefix_save
            )
            self.proton_prefix_layout.addWidget(self.proton_prefix)

            self.linux_settings = LinuxAppSettings()
            self.linux_layout.addWidget(self.linux_settings)
        else:
            self.proton_groupbox.setVisible(False)

        # startparams, skip_update_check

    def save_line_edit(self, option, value):
        if value:
            if self.game.app_name not in self.core.lgd.config.sections():
                self.core.lgd.config.add_section(self.game.app_name)
            self.core.lgd.config.set(self.game.app_name, option, value)
        else:
            if self.core.lgd.config.has_section(self.game.app_name) and self.core.lgd.config.get(
                    f"{self.game.app_name}", option, fallback=None) is not None:
                self.core.lgd.config.remove_option(self.game.app_name, option)
                if not self.core.lgd.config[self.game.app_name]:
                    self.core.lgd.config.remove_section(self.game.app_name)
        self.core.lgd.save_config()
        self.sender().setEnabled(False)

    def update_combobox(self, i, option):
        if self.change:
            # remove section
            if i:
                if self.game.app_name not in self.core.lgd.config.sections():
                    self.core.lgd.config.add_section(self.game.app_name)
                if i == 1:
                    self.core.lgd.config.set(self.game.app_name, option, "true")
                if i == 2:
                    self.core.lgd.config.set(self.game.app_name, option, "false")
            else:
                if self.game.app_name in self.core.lgd.config.sections():
                    if self.core.lgd.config.get(f"{self.game.app_name}", option, fallback=False):
                        self.core.lgd.config.remove_option(self.game.app_name, option)
                if not self.core.lgd.config[self.game.app_name]:
                    self.core.lgd.config.remove_section(self.game.app_name)
            self.core.lgd.save_config()

    def change_proton(self, i):
        if self.change:
            # Dont use Proton
            if i == 0:
                if f"{self.game.app_name}" in self.core.lgd.config.sections():
                    if self.core.lgd.config.get(f"{self.game.app_name}", "wrapper", fallback=False):
                        self.core.lgd.config.remove_option(self.game.app_name, "wrapper")
                    if self.core.lgd.config.get(f"{self.game.app_name}", "no_wine", fallback=False):
                        self.core.lgd.config.remove_option(self.game.app_name, "no_wine")
                    if not self.core.lgd.config[self.game.app_name]:
                        self.core.lgd.config.remove_section(self.game.app_name)
                if f"{self.game.app_name}.env" in self.core.lgd.config.sections():
                    if self.core.lgd.config.get(f"{self.game.app_name}.env", "STEAM_COMPAT_DATA_PATH", fallback=False):
                        self.core.lgd.config.remove_option(f"{self.game.app_name}.env", "STEAM_COMPAT_DATA_PATH")
                    if not self.core.lgd.config[self.game.app_name + ".env"]:
                        self.core.lgd.config.remove_section(self.game.app_name + ".env")
                self.proton_prefix.setEnabled(False)
                # lk: TODO: This has to be fixed properly.
                # lk: It happens because of the widget update. Mask it for now behind disabling the save button
                self.wrapper.setText(self.core.lgd.config.get(f"{self.game.app_name}", "wrapper", fallback=""))
                self.wrapper_button.setDisabled(True)
                self.wrapper_widget.setEnabled(True)
                self.linux_settings.wine_groupbox.setEnabled(True)
            else:
                self.proton_prefix.setEnabled(True)
                self.wrapper_widget.setEnabled(False)
                self.linux_settings.wine_groupbox.setEnabled(False)
                wrapper = self.possible_proton_wrappers[i - 1]
                if self.game.app_name not in self.core.lgd.config.sections():
                    self.core.lgd.config[self.game.app_name] = {}
                if self.game.app_name + ".env" not in self.core.lgd.config.sections():
                    self.core.lgd.config[self.game.app_name + ".env"] = {}
                self.core.lgd.config.set(self.game.app_name, "wrapper", wrapper)
                self.core.lgd.config.set(self.game.app_name, "no_wine", "true")
                self.core.lgd.config.set(self.game.app_name + ".env", "STEAM_COMPAT_DATA_PATH",
                                         os.path.expanduser("~/.proton"))
                self.proton_prefix.setText(os.path.expanduser("~/.proton"))

                # Dont use Wine
                self.linux_settings.wine_exec.setText("")
                self.linux_settings.save_setting(self.linux_settings.wine_exec.text(), "wine_exec")
                self.linux_settings.wine_prefix.setText("")
                self.linux_settings.save_setting(self.linux_settings.wine_prefix.text(), "wine_prefix")

        self.core.lgd.save_config()

    def proton_prefix_edit(self, text: str) -> Tuple[bool, str]:
        if not text:
            text = os.path.expanduser("~/.proton")
            return True, text
        if not os.path.exists(text):
            try:
                os.makedirs(text)
            except PermissionError:
                QMessageBox.warning(self, "Warning", f"{self.tr('No permission to create folder')} {text}")
                text = os.path.expanduser("~/.proton")
            finally:
                return True, text
        return True, text

    def proton_prefix_save(self, text: str):
        self.core.lgd.config.set(self.game.app_name + ".env", "STEAM_COMPAT_DATA_PATH", text)
        self.core.lgd.save_config()

    def update_game(self, game: Game):
        self.change = False
        self.game = game
        self.igame = self.core.get_installed_game(game.app_name)
        app_name = game.app_name
        if self.igame:
            if self.igame.can_run_offline:
                offline = self.core.lgd.config.get(self.game.app_name, "offline", fallback="unset")
                if offline == "true":
                    self.offline.setCurrentIndex(1)
                elif offline == "false":
                    self.offline.setCurrentIndex(2)
                else:
                    self.offline.setCurrentIndex(0)

                self.offline.setEnabled(True)
            else:
                self.offline.setEnabled(False)
        else:
            self.offline.setEnabled(False)

        skip_update = self.core.lgd.config.get(self.game.app_name, "skip_update_check", fallback="unset")
        if skip_update == "true":
            self.skip_update.setCurrentIndex(1)
        elif skip_update == "false":
            self.skip_update.setCurrentIndex(2)
        else:
            self.skip_update.setCurrentIndex(0)

        wrapper = self.core.lgd.config.get(self.game.app_name, "wrapper", fallback="")
        self.wrapper.setText(wrapper)

        self.game_title.setText(f"<h2>{self.game.app_title}</h2>")
        if platform.system() != "Windows":
            self.linux_settings.update_game(app_name)
            self.linux_settings.dxvk.update_settings(app_name)
            proton = self.core.lgd.config.get(f"{app_name}", "wrapper", fallback="").replace('"', "")
            if proton != "":
                self.proton_prefix.setEnabled(True)
                self.proton_wrapper.setCurrentText(f'"{proton.replace(" run", "")}" run')
                proton_prefix = self.core.lgd.config.get(f"{app_name}.env", "STEAM_COMPAT_DATA_PATH",
                                                         fallback=self.tr(
                                                             "Please select path for proton prefix"))
                self.proton_prefix.setText(proton_prefix)
                self.wrapper_widget.setEnabled(False)
            else:
                self.proton_wrapper.setCurrentIndex(0)
                self.proton_prefix.setEnabled(False)
                self.wrapper_widget.setEnabled(True)

        if not self.game.supports_cloud_saves:
            self.cloud_sync.setEnabled(False)
        else:
            self.cloud_sync.setEnabled(True)
            sync_cloud = self.settings.value(f"{self.game.app_name}/auto_sync_cloud", True, bool)
            self.cloud_sync.setChecked(sync_cloud)

        self.launch_params.setText(self.core.lgd.config.get(self.game.app_name, "start_params", fallback=""))
        self.change = True


class LinuxAppSettings(LinuxSettings):
    def __init__(self):
        super(LinuxAppSettings, self).__init__("app")

    def update_game(self, app_name):
        self.name = app_name
        self.wine_prefix.setText(self.core.lgd.config.get(self.name, "wine_prefix", fallback=""))
        self.wine_exec.setText(self.core.lgd.config.get(self.name, "wine_executable", fallback=""))
        self.dxvk.name = app_name
        self.dxvk.more_settings_widget.name = app_name
