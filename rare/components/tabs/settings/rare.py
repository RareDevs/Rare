import os
import locale
from logging import getLogger

from PySide6.QtCore import QSettings, Qt, Slot, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QWidget, QMessageBox

from rare.components.tabs.settings.widgets.discord_rpc import DiscordRPCSettings
from rare.models.options import options, LibraryView
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


class RareSettings(QWidget):
    def __init__(self, parent=None):
        super(RareSettings, self).__init__(parent=parent)
        self.ui = Ui_RareSettings()
        self.ui.setupUi(self)
        self.core = LegendaryCoreSingleton()
        self.settings = QSettings(self)

        # Select lang
        self.ui.lang_select.addItem(self.tr("System default"), options.language.default)
        for lang_code, title in get_translations():
            self.ui.lang_select.addItem(title, lang_code)
        language = self.settings.value(*options.language)
        if (index := self.ui.lang_select.findData(language, Qt.ItemDataRole.UserRole)) > 0:
            self.ui.lang_select.setCurrentIndex(index)
        else:
            self.ui.lang_select.setCurrentIndex(0)
        self.ui.lang_select.currentIndexChanged.connect(self.on_lang_changed)

        self.ui.color_select.addItem(self.tr("None"), "")
        for item in get_color_schemes():
            self.ui.color_select.addItem(item, item)
        color = self.settings.value(*options.color_scheme)
        if (index := self.ui.color_select.findData(color, Qt.ItemDataRole.UserRole)) > 0:
            self.ui.color_select.setCurrentIndex(index)
            self.ui.color_select.setDisabled(False)
            self.ui.style_select.setDisabled(True)
        else:
            self.ui.color_select.setCurrentIndex(0)
        self.ui.color_select.currentIndexChanged.connect(self.on_color_select_changed)

        self.ui.style_select.addItem(self.tr("None"), "")
        for item in get_style_sheets():
            self.ui.style_select.addItem(item, item)
        style = self.settings.value(*options.style_sheet)
        if (index := self.ui.style_select.findData(style, Qt.ItemDataRole.UserRole)) > 0:
            self.ui.style_select.setCurrentIndex(index)
            self.ui.style_select.setDisabled(False)
            self.ui.color_select.setDisabled(True)
        else:
            self.ui.style_select.setCurrentIndex(0)
        self.ui.style_select.currentIndexChanged.connect(self.on_style_select_changed)

        self.ui.view_combo.addItem(self.tr("Game covers"), LibraryView.COVER)
        self.ui.view_combo.addItem(self.tr("Vertical list"), LibraryView.VLIST)
        view = LibraryView(self.settings.value(*options.library_view))
        if (index := self.ui.view_combo.findData(view)) > -1:
            self.ui.view_combo.setCurrentIndex(index)
        else:
            self.ui.view_combo.setCurrentIndex(0)
        self.ui.view_combo.currentIndexChanged.connect(self.on_view_combo_changed)

        self.discord_rpc_settings = DiscordRPCSettings(self)
        self.ui.right_layout.insertWidget(1, self.discord_rpc_settings, alignment=Qt.AlignmentFlag.AlignTop)

        self.ui.sys_tray.setChecked(self.settings.value(*options.sys_tray))
        self.ui.sys_tray.stateChanged.connect(
            lambda: self.settings.setValue(options.sys_tray.key, self.ui.sys_tray.isChecked())
        )

        self.ui.auto_update.setChecked(self.settings.value(*options.auto_update))
        self.ui.auto_update.stateChanged.connect(
            lambda: self.settings.setValue(options.auto_update.key, self.ui.auto_update.isChecked())
        )

        self.ui.confirm_start.setChecked(self.settings.value(*options.confirm_start))
        self.ui.confirm_start.stateChanged.connect(
            lambda: self.settings.setValue(options.confirm_start.key, self.ui.confirm_start.isChecked())
        )
        # TODO: implement use when starting game, disable for now
        self.ui.confirm_start.setDisabled(True)

        self.ui.auto_sync_cloud.setChecked(self.settings.value(*options.auto_sync_cloud))
        self.ui.auto_sync_cloud.stateChanged.connect(
            lambda: self.settings.setValue(options.auto_sync_cloud.key, self.ui.auto_sync_cloud.isChecked())
        )

        self.ui.notification.setChecked(self.settings.value(*options.notification))
        self.ui.notification.stateChanged.connect(
            lambda: self.settings.setValue(options.notification.key, self.ui.notification.isChecked())
        )

        self.ui.save_size.setChecked(self.settings.value(*options.restore_window))
        self.ui.save_size.stateChanged.connect(self.save_window_size)

        self.ui.log_games.setChecked(self.settings.value(*options.log_games))
        self.ui.log_games.stateChanged.connect(
            lambda: self.settings.setValue(options.log_games.key, self.ui.log_games.isChecked())
        )

        if desktop_links_supported():
            self.desktop_link = desktop_link_path("Rare", "desktop")
            self.start_menu_link = desktop_link_path("Rare", "start_menu")
        else:
            self.ui.desktop_link_btn.setToolTip(self.tr("Not supported"))
            self.ui.desktop_link_btn.setDisabled(True)
            self.ui.startmenu_link_btn.setToolTip(self.tr("Not supported"))
            self.ui.startmenu_link_btn.setDisabled(True)
            self.desktop_link = ""
            self.start_menu_link = ""

        if self.desktop_link and self.desktop_link.exists():
            self.ui.desktop_link_btn.setText(self.tr("Remove desktop link"))

        if self.start_menu_link and self.start_menu_link.exists():
            self.ui.startmenu_link_btn.setText(self.tr("Remove start menu link"))

        self.ui.desktop_link_btn.clicked.connect(self.create_desktop_link)
        self.ui.startmenu_link_btn.clicked.connect(self.create_start_menu_link)

        self.ui.log_dir_open_button.clicked.connect(self.open_directory)
        self.ui.log_dir_clean_button.clicked.connect(self.clean_logdir)

        # get size of logdir
        size = sum(
            log_dir().joinpath(f).stat().st_size
            for f in log_dir().iterdir()
            if log_dir().joinpath(f).is_file()
        )
        self.ui.log_dir_size_label.setText(format_size(size))
        # self.log_dir_clean_button.setVisible(False)
        # self.log_dir_size_label.setVisible(False)

    @Slot()
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
        self.ui.log_dir_size_label.setText(format_size(size))

    @Slot()
    def create_start_menu_link(self):
        try:
            if not os.path.exists(self.start_menu_link):
                if not create_desktop_link(app_name="rare_shortcut", link_type="start_menu"):
                    return
                self.ui.startmenu_link_btn.setText(self.tr("Remove start menu link"))
            else:
                os.remove(self.start_menu_link)
                self.ui.startmenu_link_btn.setText(self.tr("Create start menu link"))
        except PermissionError as e:
            logger.error(str(e))
            QMessageBox.warning(
                self,
                self.tr("Error"),
                self.tr("Permission error, cannot remove {}").format(self.start_menu_link),
            )

    @Slot()
    def create_desktop_link(self):
        try:
            if not os.path.exists(self.desktop_link):
                if not create_desktop_link(app_name="rare_shortcut", link_type="desktop"):
                    return
                self.ui.desktop_link_btn.setText(self.tr("Remove Desktop link"))
            else:
                os.remove(self.desktop_link)
                self.ui.desktop_link_btn.setText(self.tr("Create desktop link"))
        except PermissionError as e:
            logger.error(str(e))
            logger.warning(
                self,
                self.tr("Error"),
                self.tr("Permission error, cannot remove {}").format(self.start_menu_link),
            )

    @Slot(int)
    def on_color_select_changed(self, index: int):
        scheme = self.ui.color_select.itemData(index, Qt.ItemDataRole.UserRole)
        if scheme:
            self.ui.style_select.setCurrentIndex(0)
            self.ui.style_select.setDisabled(True)
        else:
            self.ui.style_select.setDisabled(False)
        self.settings.setValue("color_scheme", scheme)
        set_color_pallete(scheme)

    @Slot(int)
    def on_style_select_changed(self, index: int):
        style = self.ui.style_select.itemData(index, Qt.ItemDataRole.UserRole)
        if style:
            self.ui.color_select.setCurrentIndex(0)
            self.ui.color_select.setDisabled(True)
        else:
            self.ui.color_select.setDisabled(False)
        self.settings.setValue("style_sheet", style)
        set_style_sheet(style)

    @Slot(int)
    def on_view_combo_changed(self, index: int):
        view = LibraryView(self.ui.view_combo.itemData(index, Qt.ItemDataRole.UserRole))
        self.settings.setValue(options.library_view.key, int(view))

    @Slot()
    def open_directory(self):
        QDesktopServices.openUrl(QUrl(f"file://{log_dir()}"))

    @Slot()
    def save_window_size(self):
        self.settings.setValue(options.restore_window.key, self.ui.save_size.isChecked())
        self.settings.remove(options.window_width.key)
        self.settings.remove(options.window_height.key)

    @Slot(int)
    def on_lang_changed(self, index: int):
        lang_code = self.ui.lang_select.itemData(index, Qt.ItemDataRole.UserRole)
        if lang_code == locale.getlocale()[0]:
            self.settings.remove(options.language.key)
        else:
            self.settings.setValue(options.language.key, lang_code)
