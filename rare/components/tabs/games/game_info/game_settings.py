import os
import platform
from logging import getLogger
from typing import Tuple

from PyQt5.QtCore import QSettings, QThreadPool
from PyQt5.QtWidgets import QWidget, QFileDialog, QMessageBox, QLabel, QVBoxLayout, QPushButton
from qtawesome import icon

from legendary.core import LegendaryCore
from legendary.models.game import InstalledGame, Game
from rare.components.tabs.settings.linux import LinuxSettings
from rare.ui.components.tabs.games.game_info.game_settings import Ui_GameSettings
from rare.utils.extra_widgets import PathEdit
from rare.utils.utils import WineResolver, get_raw_save_path


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


logger = getLogger("GameSettings")


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

        save_widget = QWidget()
        save_widget.setLayout(QVBoxLayout())
        self.cloud_save_path_edit = PathEdit("", file_type=QFileDialog.DirectoryOnly,
                                             ph_text=self.tr("Cloud save path"),
                                             edit_func=lambda text: (os.path.exists(text), text),
                                             save_func=self.save_save_path)
        save_widget.layout().addWidget(self.cloud_save_path_edit)

        self.compute_save_path_button = QPushButton(icon("fa.magic"), self.tr("Auto compute save path"))
        save_widget.layout().addWidget(self.compute_save_path_button)
        self.compute_save_path_button.clicked.connect(self.compute_save_path)

        self.cloud_gb.layout().addRow(QLabel(self.tr("Save path")), save_widget)

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

        # skip_update_check

    def compute_save_path(self):
        if self.core.is_installed(self.game.app_name) and self.game.supports_cloud_saves:
            try:
                new_path = self.core.get_save_path(self.game.app_name)
            except Exception as e:
                logger.warning(str(e))
                self.cloud_save_path_edit.setText(self.tr("Loading"))
                self.cloud_save_path_edit.setDisabled(True)
                self.compute_save_path_button.setDisabled(True)
                resolver = WineResolver(get_raw_save_path(self.game), self.game.app_name, self.core)
                app_name = self.game.app_name[:]
                resolver.signals.result_ready.connect(lambda x: self.wine_resolver_finished(x, app_name))
                QThreadPool.globalInstance().start(resolver)
                return
            self.cloud_save_path_edit.setText(new_path)

    def wine_resolver_finished(self, path, app_name):
        if app_name == self.game.app_name:
            self.cloud_save_path_edit.setDisabled(False)
            self.compute_save_path_button.setDisabled(False)
            if path and not os.path.exists(path):
                try:
                    os.makedirs(path)
                except PermissionError:
                    self.cloud_save_path_edit.setText("")
                    QMessageBox.warning(None, "Error", self.tr(
                        "Error while launching {}. No permission to create {}").format(
                        self.game.app_title, path))
                    return
            if not path:
                return
            self.cloud_save_path_edit.setText(path)
        else:
            igame = self.core.get_installed_game(app_name)
            igame.save_path = path
            self.core.lgd.set_installed_game(app_name, igame)

    def save_save_path(self, text):
        if self.game.supports_cloud_saves and self.change:
            self.igame.save_path = text
            self.core.lgd.set_installed_game(self.igame.app_name, self.igame)

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

        if option == "wine_prefix":
            if self.game.supports_cloud_saves:
                self.compute_save_path()

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
        parent = os.path.dirname(text)
        return os.path.exists(parent), text

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
            self.cloud_gb.setEnabled(False)
            self.cloud_save_path_edit.setText("")
        else:
            self.cloud_gb.setEnabled(True)
            sync_cloud = self.settings.value(f"{self.game.app_name}/auto_sync_cloud", True, bool)
            self.cloud_sync.setChecked(sync_cloud)
            if self.igame.save_path:
                self.cloud_save_path_edit.setText(self.igame.save_path)
            else:
                self.cloud_save_path_edit.setText("")

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
        self.dxvk.load_settings()
