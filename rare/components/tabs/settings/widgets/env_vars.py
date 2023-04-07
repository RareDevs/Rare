from logging import getLogger

from PyQt5.QtCore import QFileSystemWatcher, Qt
from PyQt5.QtWidgets import (
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

        self.table_model = EnvVarsTableModel(self.core)
        self.table_view = QTableView(self)
        self.table_view.setModel(self.table_model)
        self.table_view.verticalHeader().sectionPressed.disconnect()
        self.table_view.horizontalHeader().sectionPressed.disconnect()
        self.table_view.verticalHeader().sectionClicked.connect(self.table_model.removeRow)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
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

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Delete or e.key() == Qt.Key_Backspace:
            indexes = self.table_view.selectedIndexes()
            if not len(indexes):
                return
            for idx in indexes:
                if idx.column() == 0:
                    self.table_view.model().removeRow(idx.row())
                elif idx.column() == 1:
                    self.table_view.model().setData(idx, "", Qt.EditRole)
        elif e.key() == Qt.Key_Escape:
            e.ignore()

    def reset_model(self):
        self.table_model.reset()

    def update_game(self, app_name):
        self.table_model.load(app_name)
