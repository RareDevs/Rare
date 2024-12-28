import os.path
import platform as pf
from logging import getLogger
from typing import Tuple

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QFileDialog, QComboBox, QLineEdit
from legendary.models.game import Game, InstalledGame

from rare.components.tabs.settings.widgets.env_vars import EnvVars
from rare.components.tabs.settings.widgets.game import GameSettingsBase
from rare.components.tabs.settings.widgets.launch import LaunchSettingsBase
from rare.components.tabs.settings.widgets.overlay import DxvkSettings
from rare.components.tabs.settings.widgets.wrappers import WrapperSettings
from rare.models.game import RareGame
from rare.utils import config_helper as config
from rare.widgets.indicator_edit import PathEdit, IndicatorReasonsCommon

if pf.system() != "Windows":
    from rare.components.tabs.settings.widgets.wine import WineSettings
    if pf.system() in {"Linux", "FreeBSD"}:
        from rare.components.tabs.settings.widgets.proton import ProtonSettings
        from rare.components.tabs.settings.widgets.overlay import MangoHudSettings

logger = getLogger("GameSettings")


class GameWrapperSettings(WrapperSettings):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def load_settings(self, app_name: str):
        self.app_name = app_name


class GameLaunchSettings(LaunchSettingsBase):

    def __init__(self, parent=None):
        super(GameLaunchSettings, self).__init__(GameWrapperSettings, parent=parent)

        self.game: Game = None
        self.igame: InstalledGame = None

        self.skip_update_combo = QComboBox(self)
        self.skip_update_combo.addItem(self.tr("Default"), None)
        self.skip_update_combo.addItem(self.tr("No"), "false")
        self.skip_update_combo.addItem(self.tr("Yes"), "true")
        self.skip_update_combo.currentIndexChanged.connect(self.__skip_update_changed)

        self.offline_combo = QComboBox(self)
        self.offline_combo.addItem(self.tr("Default"), None)
        self.offline_combo.addItem(self.tr("No"), "false")
        self.offline_combo.addItem(self.tr("Yes"), "true")
        self.offline_combo.currentIndexChanged.connect(self.__offline_changed)

        self.override_exe_name_filters: Tuple[str, ...] = (
            "*.exe", "*.app", "*.bat", "*.ps1", "*.sh"
        )

        self.override_exe_edit = PathEdit(
            file_mode=QFileDialog.FileMode.ExistingFile,
            name_filters=self.override_exe_name_filters,
            placeholder=self.tr("Relative path to the replacement executable"),
            edit_func=self.__override_exe_edit_callback,
            save_func=self.__override_exe_save_callback,
            parent=self
        )

        self.launch_params_edit = QLineEdit(self)
        self.launch_params_edit.setPlaceholderText(self.tr("Game specific command line arguments"))
        self.launch_params_edit.textChanged.connect(self.__launch_params_changed)

        self.main_layout.insertRow(0, self.tr("Skip update check"), self.skip_update_combo)
        self.main_layout.insertRow(1, self.tr("Offline mode"), self.offline_combo)
        self.main_layout.insertRow(2, self.tr("Launch parameters"), self.launch_params_edit)
        self.main_layout.insertRow(3, self.tr("Override executable"), self.override_exe_edit)

    def showEvent(self, a0: QShowEvent):
        if a0.spontaneous():
            return super().showEvent(a0)

        skip_update = config.get_option(self.app_name, "skip_update_check", fallback=None)
        self.skip_update_combo.setCurrentIndex(self.offline_combo.findData(skip_update, Qt.ItemDataRole.UserRole))

        offline = config.get_option(self.app_name, "offline", fallback=None)
        self.offline_combo.setCurrentIndex(self.offline_combo.findData(offline, Qt.ItemDataRole.UserRole))

        if self.igame:
            self.offline_combo.setEnabled(self.igame.can_run_offline)
            self.override_exe_edit.setRootPath(self.igame.install_path)
        else:
            self.offline_combo.setEnabled(False)
            self.override_exe_edit.setRootPath(os.path.expanduser("~/"))

        launch_params = config.get_option(self.app_name, "start_params", "")
        self.launch_params_edit.setText(launch_params)

        override_exe = config.get_option(self.app_name, "override_exe", fallback="")
        self.override_exe_edit.setText(override_exe)

        return super().showEvent(a0)

    @Slot(int)
    def __skip_update_changed(self, index):
        data = self.skip_update_combo.itemData(index, Qt.ItemDataRole.UserRole)
        config.save_option(self.app_name, "skip_update_check", data)

    def __override_exe_edit_callback(self, path: str) -> Tuple[bool, str, int]:
        if not path or self.igame is None:
            return True, path, IndicatorReasonsCommon.VALID
        if not os.path.isabs(path):
            path = os.path.join(self.igame.install_path, path)
        # lk: Compare paths through python's commonpath because in windows we
        # cannot compare as strings
        # antonia disapproves of this
        if os.path.commonpath([self.igame.install_path, path]) != self.igame.install_path:
            return False, self.igame.install_path, IndicatorReasonsCommon.WRONG_PATH
        if not os.path.exists(path):
            return False, path, IndicatorReasonsCommon.WRONG_PATH

        if not path.endswith(tuple(map(lambda s: s.replace("*", ""), self.override_exe_name_filters))):
            return False, path, IndicatorReasonsCommon.WRONG_PATH
        path = os.path.relpath(path, self.igame.install_path)
        return True, path, IndicatorReasonsCommon.VALID

    def __override_exe_save_callback(self, path: str):
        config.save_option(self.app_name, "override_exe", path)

    @Slot(int)
    def __offline_changed(self, index):
        data = self.skip_update_combo.itemData(index, Qt.ItemDataRole.UserRole)
        config.save_option(self.app_name, "offline", data)

    def __launch_params_changed(self, value) -> None:
        config.save_option(self.app_name, "start_params", value)

    def load_settings(self, rgame: RareGame):
        self.game = rgame.game
        self.igame = rgame.igame
        self.app_name = rgame.app_name
        self.wrappers_widget.load_settings(rgame.app_name)


if pf.system() != "Windows":
    class GameWineSettings(WineSettings):
        def load_settings(self, app_name):
            self.app_name = app_name

    if pf.system() in {"Linux", "FreeBSD"}:
        class GameProtonSettings(ProtonSettings):
            def load_settings(self, app_name: str):
                self.app_name = app_name

        class GameMangoHudSettings(MangoHudSettings):
            def load_settings(self, app_name: str):
                self.app_name = app_name


class GameDxvkSettings(DxvkSettings):
    def load_settings(self, app_name: str):
        self.app_name = app_name


class GameEnvVars(EnvVars):
    def load_settings(self, app_name):
        self.app_name = app_name


class GameSettings(GameSettingsBase):
    def __init__(self, parent=None):
        if pf.system() != "Windows":
            if pf.system() in {"Linux", "FreeBSD"}:
                super(GameSettings, self).__init__(
                    GameLaunchSettings, GameDxvkSettings, GameEnvVars,
                    GameWineSettings, GameProtonSettings, GameMangoHudSettings,
                    parent=parent
                )
            else:
                super(GameSettings, self).__init__(
                    GameLaunchSettings, GameDxvkSettings, GameEnvVars,
                    GameWineSettings,
                    parent=parent
                )
        else:
            super(GameSettings, self).__init__(
                GameLaunchSettings, GameDxvkSettings, GameEnvVars,
                parent=parent
            )

    def load_settings(self, rgame: RareGame):
        self.set_title.emit(rgame.app_title)
        self.app_name = rgame.app_name
        self.launch.load_settings(rgame)
        if pf.system() != "Windows":
            self.wine.load_settings(rgame.app_name)
            if pf.system() in {"Linux", "FreeBSD"}:
                self.proton_tool.load_settings(rgame.app_name)
                self.mangohud.load_settings(rgame.app_name)
        self.dxvk.load_settings(rgame.app_name)
        self.env_vars.load_settings(rgame.app_name)
