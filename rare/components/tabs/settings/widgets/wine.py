import os
from logging import getLogger
from typing import Optional

from PySide6.QtCore import Signal, Qt, QSignalBlocker, Slot
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QFileDialog, QFormLayout, QGroupBox

from rare.models.settings import RareAppSettings
from rare.shared import RareCore
from rare.utils import config_helper as lgd_conf
from rare.widgets.indicator_edit import PathEdit, IndicatorReasonsCommon

logger = getLogger("WineSettings")


class WineSettings(QGroupBox):
    # str: option key
    environ_changed = Signal(str)

    def __init__(self, parent=None):
        super(WineSettings, self).__init__(parent=parent)
        self.setTitle(self.tr("Wine"))
        self.settings = RareAppSettings.instance()
        self.signals = RareCore.instance().signals()

        self.lgd_core = RareCore.instance().core()

        self.app_name: Optional[str] = "default"

        # Wine prefix
        self.wine_prefix_edit = PathEdit(
            path="",
            file_mode=QFileDialog.FileMode.Directory,
            edit_func=lambda path: (
                os.path.isdir(path) or not path,
                path,
                IndicatorReasonsCommon.DIR_NOT_EXISTS,
            ),
            save_func=self.save_prefix,
        )

        # Wine executable
        self.wine_execut_edit = PathEdit(
            path="",
            file_mode=QFileDialog.FileMode.ExistingFile,
            name_filters=("wine", "wine64"),
            edit_func=lambda text: (
                os.path.isfile(text) or not text,
                text,
                IndicatorReasonsCommon.FILE_NOT_EXISTS,
            ),
            save_func=self.save_execut,
        )

        layout = QFormLayout(self)
        layout.addRow(self.tr("Executable"), self.wine_execut_edit)
        layout.addRow(self.tr("Prefix"), self.wine_prefix_edit)
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.setFormAlignment(Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignTop)

    def __update_widget(self):
        _ = QSignalBlocker(self.wine_prefix_edit)
        self.wine_prefix_edit.setText(self.load_prefix())
        _ = QSignalBlocker(self.wine_execut_edit)
        self.wine_execut_edit.setText(self.load_execut())
        self.setDisabled(lgd_conf.get_boolean(self.app_name, "no_wine", fallback=False))

    def showEvent(self, a0: QShowEvent):
        if a0.spontaneous():
            return super().showEvent(a0)
        self.__update_widget()
        return super().showEvent(a0)

    @Slot(str)
    def compat_path_changed(self, text: str):
        self.wine_prefix_edit.setText(os.path.join(text, "pfx") if text else text)

    @Slot(bool)
    def compat_tool_enabled(self, enabled: bool, path: str):
        old_wine_execut = self.settings.value(f"{self.app_name}/wine_execut", defaultValue=None)
        old_wine_prefix = self.settings.value(f"{self.app_name}/wine_prefix", defaultValue=None)
        if enabled:
            wine_execut = lgd_conf.get_option(self.app_name, "wine_executable", "")
            wine_prefix = lgd_conf.get_wine_prefix(self.app_name, "")
            if old_wine_execut is None:
                self.settings.setValue(f"{self.app_name}/wine_execut", wine_execut)
            if old_wine_prefix is None:
                self.settings.setValue(f"{self.app_name}/wine_prefix", wine_prefix)
            self.wine_execut_edit.setText("")
            self.wine_prefix_edit.setText(os.path.join(path, "pfx"))
            lgd_conf.set_boolean(self.app_name, "no_wine", True)
        else:
            self.settings.remove(f"{self.app_name}/wine_execut")
            self.settings.remove(f"{self.app_name}/wine_prefix")
            self.wine_execut_edit.setText(old_wine_execut)
            self.wine_prefix_edit.setText(old_wine_prefix)
            lgd_conf.remove_option(self.app_name, "no_wine")
        self.setDisabled(enabled)

    def load_prefix(self) -> str:
        if self.app_name is None:
            raise RuntimeError
        return lgd_conf.get_wine_prefix(self.app_name, "")

    def save_prefix(self, path: str) -> None:
        if self.app_name is None:
            raise RuntimeError
        lgd_conf.adjust_wine_prefix(self.app_name, path)
        self.environ_changed.emit("WINEPREFIX")

    def load_execut(self) -> str:
        if self.app_name is None:
            raise RuntimeError
        return lgd_conf.get_option(self.app_name, "wine_executable", "")

    def save_execut(self, text: str) -> None:
        if self.app_name is None:
            raise RuntimeError
        lgd_conf.adjust_option(self.app_name, "wine_executable", text)
