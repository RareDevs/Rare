import os
from logging import getLogger
from typing import Optional

from PySide6.QtCore import Signal, Qt, QSignalBlocker
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QFileDialog, QFormLayout, QGroupBox

from rare.shared import LegendaryCoreSingleton, GlobalSignalsSingleton
from rare.utils import config_helper as config
from rare.widgets.indicator_edit import PathEdit, IndicatorReasonsCommon

logger = getLogger("WineSettings")


class WineSettings(QGroupBox):
    # str: option key
    environ_changed = Signal(str)

    def __init__(self, parent=None):
        super(WineSettings, self).__init__(parent=parent)
        self.setTitle(self.tr("Wine settings"))

        self.core = LegendaryCoreSingleton()
        self.signals = GlobalSignalsSingleton()

        self.app_name: Optional[str] = "default"

        # Wine prefix
        self.wine_prefix = PathEdit(
            path="",
            file_mode=QFileDialog.FileMode.Directory,
            edit_func=lambda path: (os.path.isdir(path) or not path, path, IndicatorReasonsCommon.DIR_NOT_EXISTS),
            save_func=self.save_prefix,
        )

        # Wine executable
        self.wine_exec = PathEdit(
            path="",
            file_mode=QFileDialog.FileMode.ExistingFile,
            name_filters=("wine", "wine64"),
            edit_func=lambda text: (os.path.isfile(text) or not text, text, IndicatorReasonsCommon.FILE_NOT_EXISTS),
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
        self.setDisabled(config.get_boolean(self.app_name, "no_wine", fallback=False))

        return super().showEvent(a0)

    def tool_enabled(self, enabled: bool):
        if enabled:
            config.set_boolean(self.app_name, "no_wine", True)
        else:
            config.remove_option(self.app_name, "no_wine")
        self.setDisabled(enabled)

    def load_prefix(self) -> str:
        if self.app_name is None:
            raise RuntimeError
        return config.get_wine_prefix(self.app_name, "")

    def save_prefix(self, path: str) -> None:
        if self.app_name is None:
            raise RuntimeError
        config.save_wine_prefix(self.app_name, path)
        self.environ_changed.emit("WINEPREFIX")

    def load_exec(self) -> str:
        if self.app_name is None:
            raise RuntimeError
        return config.get_option(self.app_name, "wine_executable", "")

    def save_exec(self, text: str) -> None:
        if self.app_name is None:
            raise RuntimeError
        config.save_option(self.app_name, "wine_executable", text)
