import os
import platform
import subprocess
import sys
from logging import getLogger

from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtWidgets import QWidget, QMessageBox

from rare import cache_dir, shared
from rare.components.tabs.settings.rpc import RPCSettings
from rare.ui.components.tabs.settings.rare import Ui_RareSettings
from rare.utils import utils
from rare.utils.utils import get_translations, get_color_schemes, set_color_pallete, get_style_sheets, set_style_sheet

logger = getLogger("RareSettings")

languages = [
    ("en", "English"),
    ("de", "Deutsch"),
    ("fr", "Français")
]


class RareSettings(QWidget, Ui_RareSettings):
    def __init__(self):
        super(RareSettings, self).__init__()
        self.setupUi(self)
        self.core = shared.core
        # (widget_name, option_name, default)
        self.checkboxes = [
            (self.sys_tray, "sys_tray", True),
            (self.auto_update, "auto_update", False),
            (self.confirm_start, "confirm_start", False),
            (self.auto_sync_cloud, "auto_sync_cloud", True),
            (self.notification, "notification", True),
            (self.save_size, "save_size", False),
            (self.log_games, "show_console", False),
        ]

        self.settings = QSettings()
        language = self.settings.value("language", self.core.language_code, type=str)
        self.logdir = os.path.join(cache_dir, "logs")

        # Select lang
        self.lang_select.addItems([i[1] for i in languages])
        if language in get_translations():
            index = [lang[0] for lang in languages].index(language)
            self.lang_select.setCurrentIndex(index)
        else:
            self.lang_select.setCurrentIndex(0)
        self.lang_select.currentIndexChanged.connect(self.update_lang)

        colors = get_color_schemes()
        self.color_select.addItems(colors)
        if (color := self.settings.value("color_scheme")) in colors:
            self.color_select.setCurrentIndex(self.color_select.findText(color))
            self.color_select.setDisabled(False)
            self.style_select.setDisabled(True)
        else:
            self.color_select.setCurrentIndex(0)
        self.color_select.currentIndexChanged.connect(self.on_color_select_changed)

        styles = get_style_sheets()
        self.style_select.addItems(styles)
        if (style := self.settings.value("style_sheet")) in styles:
            self.style_select.setCurrentIndex(self.style_select.findText(style))
            self.style_select.setDisabled(False)
            self.color_select.setDisabled(True)
        else:
            self.style_select.setCurrentIndex(0)
        self.style_select.currentIndexChanged.connect(self.on_style_select_changed)

        self.interface_info.setVisible(False)

        self.rpc = RPCSettings()
        self.rpc_layout.addWidget(self.rpc, alignment=Qt.AlignTop)

        self.init_checkboxes(self.checkboxes)
        self.sys_tray.stateChanged.connect(
            lambda: self.settings.setValue("sys_tray", self.sys_tray.isChecked())
        )
        self.auto_update.stateChanged.connect(
            lambda: self.settings.setValue("auto_update", self.auto_update.isChecked())
        )
        self.confirm_start.stateChanged.connect(
            lambda: self.settings.setValue("confirm_start", self.confirm_start.isChecked())
        )
        self.auto_sync_cloud.stateChanged.connect(
            lambda: self.settings.setValue("auto_sync_cloud", self.auto_sync_cloud.isChecked())
        )
        self.notification.stateChanged.connect(
            lambda: self.settings.setValue("notification", self.notification.isChecked())
        )
        self.save_size.stateChanged.connect(
            self.save_window_size
        )
        self.log_games.stateChanged.connect(
            lambda: self.settings.setValue("show_console", self.log_games.isChecked())
        )

        if platform.system() == "Linux":
            self.desktop_file = os.path.expanduser("~/Desktop/Rare.desktop")
            self.start_menu_link = os.path.expanduser("~/.local/share/applications/Rare.desktop")
        elif platform.system() == "Windows":
            self.desktop_file = os.path.expanduser("~/Desktop/Rare.lnk")
            self.start_menu_link = os.path.expandvars("%appdata%\\Microsoft\\Windows\\Start Menu\\Rare.lnk")
        else:
            self.desktop_link_btn.setText(self.tr("Not supported"))
            self.desktop_link_btn.setDisabled(True)
            self.startmenu_link_btn.setText(self.tr("Not supported"))
            self.startmenu_link_btn.setDisabled(True)

            self.desktop_file = ""
            self.start_menu_link = ""

        if self.desktop_file and os.path.exists(self.desktop_file):
            self.desktop_link_btn.setText(self.tr("Remove desktop link"))

        if self.start_menu_link and os.path.exists(self.start_menu_link):
            self.startmenu_link_btn.setText(self.tr("Remove start menu link"))

        self.desktop_link_btn.clicked.connect(self.create_desktop_link)
        self.startmenu_link_btn.clicked.connect(self.create_start_menu_link)

        self.log_dir_open_button.clicked.connect(self.open_dir)
        self.log_dir_clean_button.clicked.connect(self.clean_logdir)

        logdir = os.path.join(cache_dir, "logs")
        # get size of logdir
        size = 0
        for i in os.listdir(logdir):
            size += os.path.getsize(os.path.join(logdir, i))

        self.log_dir_size_label.setText(utils.get_size(size))
        # self.log_dir_clean_button.setVisible(False)
        # self.log_dir_size_label.setVisible(False)

    def clean_logdir(self):
        for i in os.listdir(os.path.join(cache_dir, "logs")):
            os.remove(os.path.join(cache_dir, "logs/") + i)
        self.log_dir_size_label.setText("0KB")

    def create_start_menu_link(self):
        try:
            if not os.path.exists(self.start_menu_link):
                utils.create_rare_desktop_link("start_menu")
                self.startmenu_link_btn.setText(self.tr("Remove start menu link"))
            else:
                os.remove(self.start_menu_link)
                self.startmenu_link_btn.setText(self.tr("Create start menu link"))
        except PermissionError as e:
            logger.error(str(e))
            QMessageBox.warning(self, "Error", "Permission error, cannot remove " + str(self.start_menu_link))

    def create_desktop_link(self):
        try:
            if not os.path.exists(self.desktop_file):
                utils.create_rare_desktop_link("desktop")
                self.desktop_link_btn.setText(self.tr("Remove Desktop link"))
            else:
                os.remove(self.desktop_file)
                self.desktop_link_btn.setText(self.tr("Create desktop link"))
        except PermissionError as e:
            logger.warning(self, "Error", "Permission error, cannot remove " + str(self.desktop_file))

    def on_color_select_changed(self, color):
        if color:
            self.style_select.setCurrentIndex(0)
            self.style_select.setDisabled(True)
            self.settings.setValue("color_scheme", self.color_select.currentText())
            set_color_pallete(self.color_select.currentText())
        else:
            self.settings.setValue("color_scheme", "")
            self.style_select.setDisabled(False)
            set_color_pallete("")
        self.interface_info.setVisible(True)

    def on_style_select_changed(self, style):
        if style:
            self.color_select.setCurrentIndex(0)
            self.color_select.setDisabled(True)
            self.settings.setValue("style_sheet", self.style_select.currentText())
            set_style_sheet(self.style_select.currentText())
        else:
            self.settings.setValue("style_sheet", "")
            self.color_select.setDisabled(False)
            set_style_sheet("")
        self.interface_info.setVisible(True)

    def open_dir(self):
        if platform.system() == "Windows":
            os.startfile(self.logdir)  # pylint: disable=E1101
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.Popen([opener, self.logdir])

    def save_window_size(self):
        self.settings.setValue("save_size", self.save_size.isChecked())
        self.settings.remove("window_size")

    def save_path(self):
        self.update_path()

    def update_lang(self, i: int):
        self.settings.setValue("language", languages[i][0])
        self.interface_info.setVisible(True)

    def init_checkboxes(self, checkboxes):
        for cb in checkboxes:
            widget, option, default = cb
            widget.setChecked(self.settings.value(option, default, bool))
