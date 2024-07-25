from logging import getLogger

from PySide6.QtCore import QFileSystemWatcher, Qt
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (
    QGroupBox,
    QHeaderView,
    QVBoxLayout,
    QTableView,
)

from rare.shared import LegendaryCoreSingleton
from .env_vars_model import EnvVarsTableModel

logger = getLogger("EnvVars")


class EnvVars(QGroupBox):
    def __init__(self, parent):
        super(EnvVars, self).__init__(parent=parent)
        self.setTitle(self.tr("Environment variables"))

        self.core = LegendaryCoreSingleton()
        self.app_name: str = "default"

        self.table_model = EnvVarsTableModel(self.core)
        self.table_view = QTableView(self)
        self.table_view.setModel(self.table_model)
        self.table_view.verticalHeader().sectionPressed.disconnect()
        self.table_view.horizontalHeader().sectionPressed.disconnect()
        self.table_view.verticalHeader().sectionClicked.connect(self.table_model.removeRow)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.setCornerButtonEnabled(False)

        # FIXME: investigate signaling between widgets
        # We use this function to keep an eye on the config.
        # When the user uses for example the wineprefix settings, we need to update the table.
        # With this function, when the config file changes, we update the table.
        # self.config_file_watcher = QFileSystemWatcher([str(self.core.lgd.config_path)], self)
        # self.config_file_watcher.fileChanged.connect(self.table_model.reset)

        row_height = self.table_view.rowHeight(0)
        self.table_view.setMinimumHeight(row_height * 7)

        layout = QVBoxLayout(self)
        layout.addWidget(self.table_view)

    def showEvent(self, a0: QShowEvent):
        if a0.spontaneous():
            return super().showEvent(a0)
        self.table_model.load(self.app_name)
        return super().showEvent(a0)

    def keyPressEvent(self, a0):
        if a0.key() in {Qt.Key.Key_Delete, Qt.Key.Key_Backspace}:
            indexes = self.table_view.selectedIndexes()
            if not len(indexes):
                return
            for idx in indexes:
                if idx.column() == 0:
                    self.table_view.model().removeRow(idx.row())
                elif idx.column() == 1:
                    self.table_view.model().setData(idx, "", Qt.ItemDataRole.EditRole)
        elif a0.key() == Qt.Key.Key_Escape:
            a0.ignore()

    def reset_model(self):
        self.table_model.reset()
