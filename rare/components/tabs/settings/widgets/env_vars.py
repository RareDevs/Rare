from logging import getLogger

from PyQt5.QtCore import QFileSystemWatcher
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
        self.config_file_watcher = QFileSystemWatcher([str(self.core.lgd.config_path)], self)
        self.config_file_watcher.fileChanged.connect(self.table_model.reset)

        row_height = self.table_view.rowHeight(0)
        self.table_view.setMinimumHeight(row_height * 7)

        layout = QVBoxLayout(self)
        layout.addWidget(self.table_view)

    # def keyPressEvent(self, e):
    #     if e.key() == Qt.Key_Delete or e.key() == Qt.Key_Backspace:
    #         selected_items = self.ui.env_vars_table.selectedItems()
    #
    #         if len(selected_items) == 0:
    #             return
    #
    #         item_in_table = self.ui.env_vars_table.findItems(selected_items[0].text(), Qt.MatchExactly)
    #
    #         # Our first selection is in column 0.  So, we have to find out if the user
    #         # only selected keys, or keys and values. we use the check_if_item func
    #         if item_in_table[0].column() == 0:
    #             which_index_to_use = 1
    #             if len(selected_items) == 1:
    #                 which_index_to_use = 0
    #             if self.check_if_item(selected_items[which_index_to_use]):
    #                 # User selected keys and values, so we skip the values
    #                 for i in selected_items[::2]:
    #                     if i:
    #                         config_helper.remove_option(f"{self.app_name}.env", i.text())
    #                         self.ui.env_vars_table.removeRow(i.row())
    #                 self.append_row()
    #             else:
    #                 # user only selected keys
    #                 for i in selected_items:
    #                     if i:
    #                         config_helper.remove_option(f"{self.app_name}.env", i.text())
    #                         self.ui.env_vars_table.removeRow(i.row())
    #                 self.append_row()
    #
    #         # User only selected values, so we just set the text to ""
    #         elif item_in_table[0].column() == 1:
    #             [i.setText("") for i in selected_items]
    #
    #     elif e.key() == Qt.Key_Escape:
    #         e.ignore()

    def update_game(self, app_name):
        self.table_model.load(app_name)
