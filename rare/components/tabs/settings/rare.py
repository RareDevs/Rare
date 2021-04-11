import os
import shutil
from logging import getLogger

from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtWidgets import QVBoxLayout, QFileDialog, QComboBox, QPushButton, QCheckBox, QGroupBox, QScrollArea

from rare.components.tabs.settings.settings_widget import SettingsWidget
from rare.utils.extra_widgets import PathEdit
from rare.utils.utils import get_lang, get_possible_langs

logger = getLogger("RareSettings")

languages = [
    ("en", "English"),
    ("de", "Deutsch"),
    ("fr", "Français")
]


class RareSettings(QScrollArea):
    def __init__(self):
        super(RareSettings, self).__init__()
        self.widget = QGroupBox(self.tr("Rare settings"))
        self.widget.setObjectName("group")
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setWidgetResizable(True)
        self.layout = QVBoxLayout()
        self.settings = QSettings()
        img_dir = self.settings.value("img_dir", os.path.expanduser("~/.cache/rare/images/"), type=str)
        language = self.settings.value("language", get_lang(), type=str)
        # select Image dir
        self.select_path = PathEdit(img_dir, type_of_file=QFileDialog.DirectoryOnly)
        self.select_path.text_edit.textChanged.connect(lambda t: self.save_path_button.setDisabled(False))
        self.save_path_button = QPushButton(self.tr("Save"))
        self.save_path_button.clicked.connect(self.save_path)
        self.img_dir = SettingsWidget(self.tr("Image Directory"), self.select_path, self.save_path_button)
        self.layout.addWidget(self.img_dir)

        # Select lang
        self.select_lang = QComboBox()
        self.select_lang.addItems([i[1] for i in languages])
        if language in get_possible_langs():
            index = [lang[0] for lang in languages].index(language)
            self.select_lang.setCurrentIndex(index)
        else:
            self.select_lang.setCurrentIndex(0)
        self.lang_widget = SettingsWidget(self.tr("Language"), self.select_lang)
        self.select_lang.currentIndexChanged.connect(self.update_lang)
        self.layout.addWidget(self.lang_widget)

        self.exit_to_sys_tray = QCheckBox(self.tr("Hide to System Tray Icon"))
        self.exit_to_sys_tray.setChecked(self.settings.value("sys_tray", True, bool))
        self.exit_to_sys_tray.stateChanged.connect(lambda: self.settings.setValue("sys_tray", self.exit_to_sys_tray.isChecked()))
        self.sys_tray_widget = SettingsWidget(self.tr("Exit to System Tray Icon"), self.exit_to_sys_tray)
        self.layout.addWidget(self.sys_tray_widget)

        self.game_start_accept = QCheckBox(self.tr("Confirm launch of game"))
        self.game_start_accept.stateChanged.connect(lambda x: self.settings.setValue("confirm_start", self.game_start_accept.isChecked()))
        self.game_start_accept_widget = SettingsWidget(self.tr("Confirm launch of game"), self.game_start_accept)
        self.layout.addWidget(self.game_start_accept_widget)

        self.cloud_sync = QCheckBox(self.tr("Sync with cloud"))
        self.cloud_sync.setChecked(self.settings.value("auto_sync_cloud", True, bool))
        self.cloud_sync_widget = SettingsWidget(self.tr("Auto sync with cloud"), self.cloud_sync)
        self.layout.addWidget(self.cloud_sync_widget)
        self.cloud_sync.stateChanged.connect(
            lambda: self.settings.setValue(f"auto_sync_cloud", self.cloud_sync.isChecked()))

        self.save_size = QCheckBox(self.tr("Save size"))
        self.save_size.setChecked(self.settings.value("save_size", False, bool))
        self.save_size_widget = SettingsWidget(self.tr("Save size of window after restart"), self.save_size)
        self.layout.addWidget(self.save_size_widget)
        self.save_size.stateChanged.connect(self.save_window_size)

        self.layout.addStretch()
        self.widget.setLayout(self.layout)
        self.setWidget(self.widget)

    def save_window_size(self):
        self.settings.setValue("save_size", self.save_size.isChecked())
        self.settings.remove("window_size")

    def save_path(self):
        self.save_path_button.setDisabled(True)
        self.update_path()

    def update_lang(self, i: int):
        self.settings.setValue("language", languages[i][0])
        self.lang_widget.info_text.setText(self.tr("Restart Application to activate changes"))

    def update_path(self):
        old_path = self.settings.value("img_dir", type=str)
        new_path = self.select_path.text()

        if old_path != new_path:
            if not os.path.exists(new_path):
                os.makedirs(new_path)
            elif len(os.listdir(new_path)) > 0:
                logger.warning("New directory is not empty")
                return
            logger.info("Move Images")
            for i in os.listdir(old_path):
                shutil.move(os.path.join(old_path, i), os.path.join(new_path, i))
            os.rmdir(old_path)
            self.settings.setValue("img_dir", new_path)
