from PyQt5.QtWidgets import QGroupBox, QTableWidgetItem
from rare.ui.components.tabs.games.env_vars import Ui_env_vars_groupbox
from rare.utils import config_helper
from rare.shared import LegendaryCoreSingleton

class EnvVars(QGroupBox, Ui_env_vars_groupbox):
    def __init__(self, parent):
        super(EnvVars, self).__init__(parent=parent)
        self.setupUi(self)
        self.env_vars_table.cellChanged.connect(self.create_new_row)
        self.env_vars_table.cellChanged.connect(self.update_env_vars)
        self.env_vars_table.verticalHeader().sectionClicked.connect(self.remove_row)
        self.app_name = None
        self.list_of_labels = []
        self.core = LegendaryCoreSingleton()
    
    def import_env_vars(self):
        self.env_vars_table.clearContents()

        list_of_keys = []
        list_of_values = []
 
        # First, we try to get all keys and values from the config
        try:
            for key in self.core.lgd.config[f"{self.app_name}.env"]:
                list_of_keys.append(key)
            for i in list_of_keys:
                list_of_values.append(self.core.lgd.config[f"{self.app_name}.env"][i])
        except KeyError:
            pass

        # We count how many keys we have and insert new lines (as many as we need).
        count = len(list_of_keys)
        i = 0
        for _ in range(count):
            self.list_of_labels.append("-")
            self.env_vars_table.insertRow(i)
            i += 1

        # We set the row count to the length of the list_of_keys
        if len(list_of_keys) == 0:
            self.env_vars_table.setRowCount(1)
        else:
            self.env_vars_table.setRowCount(len(list_of_keys))


        # We always need to append one more minus at the end, because we want to have the new empty line to also have the minus.
        self.list_of_labels.append("-")
        self.env_vars_table.setVerticalHeaderLabels(self.list_of_labels)
        for index, val in enumerate(list_of_keys):
            new_item = QTableWidgetItem()
            new_item.setText(val)
            self.env_vars_table.setItem(index, 0, new_item)
        
        for index, val in enumerate(list_of_values):
            new_item = QTableWidgetItem()
            new_item.setText(val)
            self.env_vars_table.setItem(index, 1, new_item)

    def update_env_vars(self, row, column):
        first_item = self.env_vars_table.item(row, 0)
        second_item = self.env_vars_table.item(row, 1)
        if column == 0 and first_item is not None and second_item is not None:
            config_helper.add_option(f"{self.app_name}.env", first_item.text(), second_item.text())
            config_helper.save_config()
        if column == 1 and first_item is not None and second_item is not None:
            config_helper.add_option(f"{self.app_name}.env", first_item.text(), second_item.text())
            config_helper.save_config()

    def create_new_row(self):
        # We check wether the last item in the first column is not None.
        # If yes, we insert a new row.
        row_count = self.env_vars_table.rowCount()
        last_item = self.env_vars_table.item(row_count-1, 0)

        if row_count == 1:
            self.env_vars_table.insertRow(row_count)
        elif last_item is not None:
            if last_item.text() != "":
                self.env_vars_table.insertRow(row_count)
        self.env_vars_table.setVerticalHeaderLabels(self.list_of_labels)

    def remove_row(self, index):
        # The user also should be able to delete the row even if rowCount() is lower than 1, but then the row should be just cleared. (And not deleted)
        if self.env_vars_table.rowCount() > 1:
            self.env_vars_table.removeRow(index)
            try:
                list_of_keys = []
                for key in self.core.lgd.config[f"{self.app_name}.env"]:
                    list_of_keys.append(key)
                config_helper.remove_option(f"{self.app_name}.env", list_of_keys[index])
            except KeyError:
                pass

    def update_game(self, app_name):
        self.app_name = app_name
        self.env_vars_table.clearSpans()
        self.import_env_vars()
