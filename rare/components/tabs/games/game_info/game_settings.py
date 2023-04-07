import os.path
import platform
from logging import getLogger
from typing import Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QFileDialog
from legendary.models.game import Game, InstalledGame

from rare.components.tabs.settings import DefaultGameSettings
from rare.components.tabs.settings.widgets.pre_launch import PreLaunchSettings
from rare.models.game import RareGame
from rare.utils import config_helper
from rare.widgets.side_tab import SideTabContents
from rare.widgets.indicator_edit import PathEdit, IndicatorReasonsCommon

logger = getLogger("GameSettings")


class GameSettings(DefaultGameSettings, SideTabContents):
    def __init__(self, parent=None):
        super(GameSettings, self).__init__(False, parent=parent)
        self.pre_launch_settings = PreLaunchSettings()
        self.ui.launch_settings_group.layout().addRow(
            QLabel(self.tr("Pre-launch command")), self.pre_launch_settings
        )

        self.ui.skip_update.currentIndexChanged.connect(
            lambda x: self.update_combobox("skip_update_check", x)
        )
        self.ui.offline.currentIndexChanged.connect(
            lambda x: self.update_combobox("offline", x)
        )
        self.ui.launch_params.textChanged.connect(
            lambda x: self.line_edit_save_callback("start_params", x)
        )

        self.override_exe_edit = PathEdit(
            file_mode=QFileDialog.ExistingFile,
            name_filters=["*.exe", "*.app"],
            placeholder=self.tr("Relative path to launch executable"),
            edit_func=self.override_exe_edit_callback,
            save_func=self.override_exe_save_callback,
            parent=self
        )
        self.ui.launch_settings_layout.insertRow(
            int(self.ui.launch_settings_layout.indexOf(self.ui.launch_params)/2) + 1,
            QLabel(self.tr("Override executable"), self),
            self.override_exe_edit
        )

        self.ui.game_settings_layout.setAlignment(Qt.AlignTop)

        self.game: Game = None
        self.igame: InstalledGame = None

    def override_exe_edit_callback(self, path: str) -> Tuple[bool, str, int]:
        if not path or self.igame is None:
            return True, path, IndicatorReasonsCommon.VALID
        if not os.path.isabs(path):
            path = os.path.join(self.igame.install_path, path)
        if self.igame.install_path not in path:
            return False, self.igame.install_path, IndicatorReasonsCommon.WRONG_PATH
        if not os.path.exists(path):
            return False, path, IndicatorReasonsCommon.WRONG_PATH

        if not path.endswith(".exe") and not path.endswith(".app"):
            return False, path, IndicatorReasonsCommon.WRONG_PATH
        path = os.path.relpath(path, self.igame.install_path)
        return True, path, IndicatorReasonsCommon.VALID

    def override_exe_save_callback(self, path: str):
        self.line_edit_save_callback("override_exe", path)

    def line_edit_save_callback(self, option, value) -> None:
        if value:
            config_helper.add_option(self.game.app_name, option, value)
        else:
            config_helper.remove_option(self.game.app_name, option)
        config_helper.save_config()

    def update_combobox(self, option, index):
        if self.change:
            # remove section
            if index:
                if index == 1:
                    config_helper.add_option(self.game.app_name, option, "true")
                if index == 2:
                    config_helper.add_option(self.game.app_name, option, "false")
            else:
                config_helper.remove_option(self.game.app_name, option)
            config_helper.save_config()

    def load_settings(self, rgame: RareGame):
        self.change = False
        # FIXME: Use RareGame for the rest of the code
        app_name = rgame.app_name
        super(GameSettings, self).load_settings(app_name)
        self.game = rgame.game
        self.igame = rgame.igame
        if self.igame:
            if self.igame.can_run_offline:
                offline = self.core.lgd.config.get(self.game.app_name, "offline", fallback="unset")
                if offline == "true":
                    self.ui.offline.setCurrentIndex(1)
                elif offline == "false":
                    self.ui.offline.setCurrentIndex(2)
                else:
                    self.ui.offline.setCurrentIndex(0)

                self.ui.offline.setEnabled(True)
            else:
                self.ui.offline.setEnabled(False)
            self.override_exe_edit.set_root(self.igame.install_path)
        else:
            self.ui.offline.setEnabled(False)
            self.override_exe_edit.set_root("")

        skip_update = self.core.lgd.config.get(self.game.app_name, "skip_update_check", fallback="unset")
        if skip_update == "true":
            self.ui.skip_update.setCurrentIndex(1)
        elif skip_update == "false":
            self.ui.skip_update.setCurrentIndex(2)
        else:
            self.ui.skip_update.setCurrentIndex(0)

        self.set_title.emit(self.game.app_title)
        if platform.system() != "Windows":
            if self.igame and self.igame.platform == "Mac":
                self.ui.linux_settings_widget.setVisible(False)
            else:
                self.ui.linux_settings_widget.setVisible(True)

        self.ui.launch_params.setText(self.core.lgd.config.get(self.game.app_name, "start_params", fallback=""))
        self.override_exe_edit.setText(
            self.core.lgd.config.get(self.game.app_name, "override_exe", fallback="")
        )
        self.pre_launch_settings.load_settings(app_name)

        self.change = True
