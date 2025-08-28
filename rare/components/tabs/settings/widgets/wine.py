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
        self.wine_prefix = PathEdit(
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
        self.wine_exec = PathEdit(
            path="",
            file_mode=QFileDialog.FileMode.ExistingFile,
            name_filters=("wine", "wine64"),
            edit_func=lambda text: (
                os.path.isfile(text) or not text,
                text,
                IndicatorReasonsCommon.FILE_NOT_EXISTS,
            ),
            save_func=self.save_exec,
        )

        layout = QFormLayout(self)
        layout.addRow(self.tr("Executable"), self.wine_exec)
        layout.addRow(self.tr("Prefix"), self.wine_prefix)
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.setFormAlignment(Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignTop)

    def showEvent(self, a0: QShowEvent):
        if a0.spontaneous():
            return super().showEvent(a0)

        _ = QSignalBlocker(self.wine_prefix)
        self.wine_prefix.setText(self.load_prefix())
        _ = QSignalBlocker(self.wine_exec)
        self.wine_exec.setText(self.load_exec())
        self.setDisabled(lgd_conf.get_boolean(self.app_name, "no_wine", fallback=False))

        return super().showEvent(a0)

    @Slot(bool)
    def tool_enabled(self, enabled: bool):
        if enabled:
            lgd_conf.set_boolean(self.app_name, "no_wine", True)
            if wine_exec := self.load_exec():
                self.settings.setValue(f"{self.app_name}/wine_exec", wine_exec)
            self.wine_exec.setText("")
            if wine_prefix := self.load_prefix():
                self.settings.setValue(f"{self.app_name}/wine_prefix", wine_prefix)
            self.wine_prefix.setText("")
        else:
            lgd_conf.remove_option(self.app_name, "no_wine")
            if not self.load_exec():
                self.wine_exec.setText(self.settings.value(f"{self.app_name}/wine_exec", defaultValue="", type=str))
            if not self.load_prefix():
                self.wine_prefix.setText(self.settings.value(f"{self.app_name}/wine_prefix", defaultValue="", type=str))
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

    def load_exec(self) -> str:
        if self.app_name is None:
            raise RuntimeError
        return lgd_conf.get_option(self.app_name, "wine_executable", "")

    def save_exec(self, text: str) -> None:
        if self.app_name is None:
            raise RuntimeError
        lgd_conf.adjust_option(self.app_name, "wine_executable", text)
