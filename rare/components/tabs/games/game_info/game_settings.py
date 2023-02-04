import platform
from logging import getLogger

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel
from legendary.models.game import Game, InstalledGame

from rare.components.tabs.settings import DefaultGameSettings
from rare.components.tabs.settings.widgets.pre_launch import PreLaunchSettings
from rare.models.game import RareGame
from rare.utils import config_helper
from rare.widgets.side_tab import SideTabContents

logger = getLogger("GameSettings")


class GameSettings(DefaultGameSettings, SideTabContents):
    game: Game
    igame: InstalledGame

    def __init__(self, parent=None):
        super(GameSettings, self).__init__(False, parent=parent)
        self.pre_launch_settings = PreLaunchSettings()
        self.launch_settings_group.layout().addRow(
            QLabel(self.tr("Pre-launch command")), self.pre_launch_settings
        )

        self.offline.currentIndexChanged.connect(lambda x: self.update_combobox(x, "offline"))
        self.skip_update.currentIndexChanged.connect(lambda x: self.update_combobox(x, "skip_update_check"))

        self.override_exe_edit.textChanged.connect(lambda text: self.save_line_edit("override_exe", text))
        self.launch_params.textChanged.connect(lambda x: self.save_line_edit("start_params", x))

        self.game_settings_layout.setAlignment(Qt.AlignTop)

    def save_line_edit(self, option, value):
        if value:

            config_helper.add_option(self.game.app_name, option, value)
        else:
            config_helper.remove_option(self.game.app_name, option)
        config_helper.save_config()

    def update_combobox(self, i, option):
        if self.change:
            # remove section
            if i:
                if i == 1:
                    config_helper.add_option(self.game.app_name, option, "true")
                if i == 2:
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

        self.set_title.emit(self.game.app_title)
        if platform.system() != "Windows":
            if self.igame and self.igame.platform == "Mac":
                self.linux_settings_widget.setVisible(False)
            else:
                self.linux_settings_widget.setVisible(True)

        self.launch_params.setText(self.core.lgd.config.get(self.game.app_name, "start_params", fallback=""))
        self.override_exe_edit.setText(
            self.core.lgd.config.get(self.game.app_name, "override_exe", fallback="")
        )

        self.pre_launch_settings.load_settings(app_name)

        self.change = True
