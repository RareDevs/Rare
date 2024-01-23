import os
import platform
import subprocess
import sys
from logging import getLogger

from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtWidgets import QWidget, QMessageBox

from rare.components.tabs.settings.widgets.rpc import RPCSettings
from rare.models.options import options
from rare.shared import LegendaryCoreSingleton
from rare.ui.components.tabs.settings.rare import Ui_RareSettings
from rare.utils.misc import (
    get_translations,
    get_color_schemes,
    set_color_pallete,
    get_style_sheets,
    set_style_sheet,
    format_size,
)
from rare.utils.paths import create_desktop_link, desktop_link_path, log_dir, desktop_links_supported

logger = getLogger("RareSettings")


class RareSettings(QWidget, Ui_RareSettings):
    def __init__(self, parent=None):
        super(RareSettings, self).__init__(parent=parent)
        self.setupUi(self)
        self.core = LegendaryCoreSingleton()
        self.settings = QSettings(self)

        # Select lang
        language = self.settings.value(*options.language)
        self.lang_select.addItem(self.tr("System default"), "")
        for locale, title in get_translations():
            self.lang_select.addItem(title, locale)
        if (index := self.lang_select.findData(language, Qt.UserRole)) > 0:
            self.lang_select.setCurrentIndex(index)
        else:
            self.lang_select.setCurrentIndex(0)
        self.lang_select.currentIndexChanged.connect(self.on_lang_changed)

        self.color_select.addItems(get_color_schemes())
        if (color := self.settings.value("color_scheme")) in get_color_schemes():
            self.color_select.setCurrentIndex(self.color_select.findText(color))
            self.color_select.setDisabled(False)
            self.style_select.setDisabled(True)
        else:
            self.color_select.setCurrentIndex(0)
        self.color_select.currentIndexChanged.connect(self.on_color_select_changed)

        self.style_select.addItems(get_style_sheets())
        if (style := self.settings.value("style_sheet")) in get_style_sheets():
            self.style_select.setCurrentIndex(self.style_select.findText(style))
            self.style_select.setDisabled(False)
            self.color_select.setDisabled(True)
        else:
            self.style_select.setCurrentIndex(0)
        self.style_select.currentIndexChanged.connect(self.on_style_select_changed)

        self.rpc = RPCSettings(self)
        self.right_layout.insertWidget(1, self.rpc, alignment=Qt.AlignTop)

        self.sys_tray.setChecked(self.settings.value(*options.sys_tray))
        self.sys_tray.stateChanged.connect(
            lambda: self.settings.setValue(options.sys_tray.key, self.sys_tray.isChecked())
        )

        self.auto_update.setChecked(self.settings.value(*options.auto_update))
        self.auto_update.stateChanged.connect(
            lambda: self.settings.setValue(options.auto_update.key, self.auto_update.isChecked())
        )

        self.confirm_start.setChecked(self.settings.value(*options.confirm_start))
        self.confirm_start.stateChanged.connect(
            lambda: self.settings.setValue(options.confirm_start.key, self.confirm_start.isChecked())
        )

        self.auto_sync_cloud.setChecked(self.settings.value(*options.auto_sync_cloud))
        self.auto_sync_cloud.stateChanged.connect(
            lambda: self.settings.setValue(options.auto_sync_cloud.key, self.auto_sync_cloud.isChecked())
        )

        self.notification.setChecked(self.settings.value(*options.notification))
        self.notification.stateChanged.connect(
            lambda: self.settings.setValue(options.notification.key, self.notification.isChecked())
        )

        self.save_size.setChecked(self.settings.value(*options.save_size))
        self.save_size.stateChanged.connect(self.save_window_size)

        self.log_games.setChecked(self.settings.value(*options.log_games))
        self.log_games.stateChanged.connect(
            lambda: self.settings.setValue(options.log_games.key, self.log_games.isChecked())
        )

        if desktop_links_supported():
            self.desktop_link = desktop_link_path("Rare", "desktop")
            self.start_menu_link = desktop_link_path("Rare", "start_menu")
        else:
            self.desktop_link_btn.setToolTip(self.tr("Not supported"))
            self.desktop_link_btn.setDisabled(True)
            self.startmenu_link_btn.setToolTip(self.tr("Not supported"))
            self.startmenu_link_btn.setDisabled(True)
            self.desktop_link = ""
            self.start_menu_link = ""

        if self.desktop_link and self.desktop_link.exists():
            self.desktop_link_btn.setText(self.tr("Remove desktop link"))

        if self.start_menu_link and self.start_menu_link.exists():
            self.startmenu_link_btn.setText(self.tr("Remove start menu link"))

        self.desktop_link_btn.clicked.connect(self.create_desktop_link)
        self.startmenu_link_btn.clicked.connect(self.create_start_menu_link)

        self.log_dir_open_button.clicked.connect(self.open_directory)
        self.log_dir_clean_button.clicked.connect(self.clean_logdir)

        # get size of logdir
        size = sum(
            log_dir().joinpath(f).stat().st_size
            for f in log_dir().iterdir()
            if log_dir().joinpath(f).is_file()
        )
        self.log_dir_size_label.setText(format_size(size))
        # self.log_dir_clean_button.setVisible(False)
        # self.log_dir_size_label.setVisible(False)

    def clean_logdir(self):
        for f in log_dir().iterdir():
            try:
                if log_dir().joinpath(f).is_file():
                    log_dir().joinpath(f).unlink()
            except PermissionError as e:
                logger.error(e)
        size = sum(
            log_dir().joinpath(f).stat().st_size
            for f in log_dir().iterdir()
            if log_dir().joinpath(f).is_file()
        )
        self.log_dir_size_label.setText(format_size(size))

    def create_start_menu_link(self):
        try:
            if not os.path.exists(self.start_menu_link):
                if not create_desktop_link(app_name="rare_shortcut", link_type="start_menu"):
                    return
                self.startmenu_link_btn.setText(self.tr("Remove start menu link"))
            else:
                os.remove(self.start_menu_link)
                self.startmenu_link_btn.setText(self.tr("Create start menu link"))
        except PermissionError as e:
            logger.error(str(e))
            QMessageBox.warning(
                self,
                self.tr("Error"),
                self.tr("Permission error, cannot remove {}").format(self.start_menu_link),
            )

    def create_desktop_link(self):
        try:
            if not os.path.exists(self.desktop_link):
                if not create_desktop_link(app_name="rare_shortcut", link_type="desktop"):
                    return
                self.desktop_link_btn.setText(self.tr("Remove Desktop link"))
            else:
                os.remove(self.desktop_link)
                self.desktop_link_btn.setText(self.tr("Create desktop link"))
        except PermissionError as e:
            logger.error(str(e))
            logger.warning(
                self,
                self.tr("Error"),
                self.tr("Permission error, cannot remove {}").format(self.start_menu_link),
            )

    def on_color_select_changed(self, scheme):
        if scheme:
            self.style_select.setCurrentIndex(0)
            self.style_select.setDisabled(True)
            self.settings.setValue("color_scheme", self.color_select.currentText())
            set_color_pallete(self.color_select.currentText())
        else:
            self.settings.setValue("color_scheme", "")
            self.style_select.setDisabled(False)
            set_color_pallete("")

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

    @staticmethod
    def open_directory():
        if platform.system() == "Windows":
            os.startfile(log_dir())  # pylint: disable=E1101
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.Popen([opener, log_dir()])

    def save_window_size(self):
        self.settings.setValue(options.save_size.key, self.save_size.isChecked())
        self.settings.remove(options.window_size.key)

    def on_lang_changed(self, index: int):
        if not index:
            self.settings.remove(options.language.key)
            return
        language = self.lang_select.itemData(index, Qt.UserRole)
        self.settings.setValue(options.language.key, language)
