import os
import platform
from logging import getLogger

from PyQt5.QtCore import Qt, QThreadPool
from PyQt5.QtWidgets import QSizePolicy, QPushButton, QLabel, QFileDialog, QMessageBox
from legendary.models.game import Game, InstalledGame

from rare.components.tabs.settings import DefaultGameSettings
from rare.components.tabs.settings.widgets.pre_launch import PreLaunchSettings
from rare.utils import config_helper
from rare.utils.extra_widgets import PathEdit
from rare.utils.misc import icon, WineResolver, get_raw_save_path

logger = getLogger("GameSettings")


class GameSettings(DefaultGameSettings):
    game: Game
    igame: InstalledGame

    def __init__(self, parent=None):
        super(GameSettings, self).__init__(False, parent)
        self.pre_launch_settings = PreLaunchSettings()
        self.launch_settings_group.layout().addRow(
            QLabel(self.tr("Pre launch command")), self.pre_launch_settings
        )

        self.cloud_save_path_edit = PathEdit(
            "",
            file_type=QFileDialog.DirectoryOnly,
            placeholder=self.tr("Cloud save path"),
            edit_func=lambda text: (True, text, None)
            if os.path.exists(text)
            else (False, text, PathEdit.reasons.dir_not_exist),
            save_func=self.save_save_path,
        )
        self.cloud_layout.addRow(QLabel(self.tr("Save path")), self.cloud_save_path_edit)

        self.compute_save_path_button = QPushButton(icon("fa.magic"), self.tr("Auto compute save path"))
        self.compute_save_path_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.compute_save_path_button.clicked.connect(self.compute_save_path)
        self.cloud_layout.addRow(None, self.compute_save_path_button)

        self.offline.currentIndexChanged.connect(lambda x: self.update_combobox(x, "offline"))
        self.skip_update.currentIndexChanged.connect(lambda x: self.update_combobox(x, "skip_update_check"))
        self.cloud_sync.stateChanged.connect(
            lambda: self.settings.setValue(
                f"{self.game.app_name}/auto_sync_cloud", self.cloud_sync.isChecked()
            )
        )
        self.override_exe_edit.textChanged.connect(lambda text: self.save_line_edit("override_exe", text))
        self.launch_params.textChanged.connect(lambda x: self.save_line_edit("start_params", x))

        self.game_settings_layout.setAlignment(Qt.AlignTop)

    def compute_save_path(self):
        if self.core.is_installed(self.game.app_name) and self.game.supports_cloud_saves:
            try:
                new_path = self.core.get_save_path(self.game.app_name)
            except Exception as e:
                logger.warning(str(e))
                resolver = WineResolver(get_raw_save_path(self.game), self.game.app_name)
                if not resolver.wine_env.get("WINEPREFIX"):
                    self.cloud_save_path_edit.setText("")
                    QMessageBox.warning(self, "Warning", "No wine prefix selected. Please set it in settings")
                    return
                self.cloud_save_path_edit.setText(self.tr("Loading"))
                self.cloud_save_path_edit.setDisabled(True)
                self.compute_save_path_button.setDisabled(True)

                app_name = self.game.app_name[:]
                resolver.signals.result_ready.connect(lambda x: self.wine_resolver_finished(x, app_name))
                QThreadPool.globalInstance().start(resolver)
                return
            else:
                self.cloud_save_path_edit.setText(new_path)

    def wine_resolver_finished(self, path, app_name):
        logger.info(f"Wine resolver finished for {app_name}. Computed save path: {path}")
        if app_name == self.game.app_name:
            self.cloud_save_path_edit.setDisabled(False)
            self.compute_save_path_button.setDisabled(False)
            if path and not os.path.exists(path):
                try:
                    os.makedirs(path)
                except PermissionError:
                    self.cloud_save_path_edit.setText("")
                    QMessageBox.warning(
                        None,
                        "Error",
                        self.tr("Error while launching {}. No permission to create {}").format(
                            self.game.app_title, path
                        ),
                    )
                    return
            if not path:
                self.cloud_save_path_edit.setText("")
                return
            self.cloud_save_path_edit.setText(path)
        elif path:
            igame = self.core.get_installed_game(app_name)
            igame.save_path = path
            self.core.lgd.set_installed_game(app_name, igame)

    def save_save_path(self, text):
        if self.game.supports_cloud_saves and self.change:
            self.igame.save_path = text
            self.core.lgd.set_installed_game(self.igame.app_name, self.igame)

    def save_line_edit(self, option, value):
        if value:

            config_helper.add_option(self.game.app_name, option, value)
        else:
            config_helper.remove_option(self.game.app_name, option)
        config_helper.save_config()

        if option == "wine_prefix":
            if self.game.supports_cloud_saves:
                self.compute_save_path()

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

    def load_settings(self, app_name):
        self.change = False
        super(GameSettings, self).load_settings(app_name)
        self.game = self.core.get_game(app_name)
        self.igame = self.core.get_installed_game(self.game.app_name)
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

        self.title.setTitle(self.game.app_title)
        if platform.system() != "Windows":
            if self.igame and self.igame.platform == "Mac":
                self.linux_settings_widget.setVisible(False)
            else:
                self.linux_settings_widget.setVisible(True)

        if not self.game.supports_cloud_saves:
            self.cloud_group.setEnabled(False)
            self.cloud_save_path_edit.setText("")
        else:
            self.cloud_group.setEnabled(True)
            sync_cloud = self.settings.value(f"{self.game.app_name}/auto_sync_cloud", True, bool)
            self.cloud_sync.setChecked(sync_cloud)
            if self.igame.save_path:
                self.cloud_save_path_edit.setText(self.igame.save_path)
            else:
                self.cloud_save_path_edit.setText("")

        self.launch_params.setText(self.core.lgd.config.get(self.game.app_name, "start_params", fallback=""))
        self.override_exe_edit.setText(
            self.core.lgd.config.get(self.game.app_name, "override_exe", fallback="")
        )

        self.pre_launch_settings.load_settings(app_name)

        self.change = True
