from PyQt5.QtWidgets import QGroupBox, QTableWidgetItem, QMessageBox
import qtawesome
from rare.ui.components.tabs.games.env_vars import Ui_EnvVars
from rare.utils import config_helper
from rare.shared import LegendaryCoreSingleton
from PyQt5.QtCore import Qt, QFileSystemWatcher

class EnvVars(QGroupBox, Ui_EnvVars):
    def __init__(self, parent):
        super(EnvVars, self).__init__(parent=parent)
        self.setupUi(self)
        self.app_name = None
        self.core = LegendaryCoreSingleton()
        self.latest_item = None
        self.list_of_readonly = ["STEAM_COMPAT_DATA_PATH", "DXVK_HUD", "WINEPREFIX"]
        self.warn_msg = "Readonly, please edit this via the appropriate setting above."
        self.setup_file_watcher()

    # We use this function to keep an eye on the config.
    # When the user uses for example the wineprefix settings, we need to update the table.
    # With this function, when the config file changes, we update the table.
    def setup_file_watcher(self):
        self.config_file_watcher = QFileSystemWatcher([self.core.lgd.config_path], self)
        self.config_file_watcher.fileChanged.connect(self.import_env_vars)

    def compare_config_and_table(self):
        list_of_keys_in_table = []
        row_count = self.env_vars_table.rowCount()

        for i in range(row_count):
            item = self.env_vars_table.item(i, 0)
            try:
                list_of_keys_in_table.append(item.text())
            except AttributeError:
                pass

        list_of_keys_in_config = []
        try:
            for key in self.core.lgd.config[f"{self.app_name}.env"]:
                list_of_keys_in_config.append(key)
        except KeyError:
            pass

    def import_env_vars(self):
        self.env_vars_table.disconnect()
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

        # We count how many keys we have and insert new lines
        # (as many as we need).
        # Each iteration we have to create a new QTableWidgetItem object,
        # else we segfault. (For using the same object in multiple references.)
        count = len(list_of_keys)
        for i in range(count):
            self.env_vars_table.insertRow(i)

            trash_icon = QTableWidgetItem()
            trash_icon.setIcon(qtawesome.icon("mdi.delete"))
            self.env_vars_table.setVerticalHeaderItem(i, trash_icon)
        # We set the row count to the length of the list_of_keys
        if len(list_of_keys) == 0:
            self.env_vars_table.setRowCount(1)
        else:
            self.env_vars_table.setRowCount(len(list_of_keys))

        for index, val in enumerate(list_of_keys):
            new_item = QTableWidgetItem()
            new_item.setText(val)

            if new_item.text() in self.list_of_readonly:
                new_item.setFlags(new_item.flags() ^ Qt.ItemIsEnabled)
                new_item.setToolTip(self.warn_msg)

            self.env_vars_table.setItem(index, 0, new_item)

        for index, val in enumerate(list_of_values):
            new_item = QTableWidgetItem()
            new_item.setText(val)

            # We need to check if the first_item is in the list of readonly vars.
            # If yes, we also need to disable column 1.
            first_item = self.env_vars_table.item(index, 0)
            if first_item.text() in self.list_of_readonly:
                new_item.setFlags(new_item.flags() ^ Qt.ItemIsEnabled)
                new_item.setToolTip(self.warn_msg)
            self.env_vars_table.setItem(index, 1, new_item)

        row_count = self.env_vars_table.rowCount()
        last_item = self.env_vars_table.item(row_count - 1, 0)
        if last_item is not None:
            self.env_vars_table.insertRow(row_count)
            trash_icon = QTableWidgetItem()
            trash_icon.setIcon(qtawesome.icon("mdi.delete"))
            self.env_vars_table.setVerticalHeaderItem(row_count, trash_icon)

        new_thing = QTableWidgetItem()
        new_thing.setIcon(qtawesome.icon("mdi.delete"))
        self.env_vars_table.setVerticalHeaderItem(0, new_thing)

        self.compare_config_and_table()

        # We need to call this at the end, since at startup we import the
        # config and update the table. Thus, the cellChanged signal reacts, but
        # we don't want that. Maybe we should only call this once, at startup?
        # Like this we always connect at every update_game.
        self.env_vars_table.cellChanged.connect(self.update_env_vars)
        self.env_vars_table.verticalHeader().sectionClicked.connect(self.remove_row)

    def update_env_vars(self, row):
        row_count = self.env_vars_table.rowCount()
        first_item = self.env_vars_table.item(row, 0)
        second_item = self.env_vars_table.item(row, 1)

        list_of_keys = []
        try:
            for key in self.core.lgd.config[f"{self.app_name}.env"]:
                list_of_keys.append(key)
        except KeyError:
            pass

        list_of_keys_in_table = []

        for i in range(row_count):
            item = self.env_vars_table.item(i, 0)
            try:
                list_of_keys_in_table.append(item.text())
            except AttributeError:
                pass

        missing_item = list(set(list_of_keys) - set(list_of_keys_in_table))
        if len(missing_item) != 0:
            config_helper.remove_option(f"{self.app_name}.env", missing_item[0])

        # A env var always needs to have a key.
        # If it's none, we return.
        if first_item is None:
            return

        if first_item.text() in self.list_of_readonly:
            error_dialog = QMessageBox()
            error_dialog.setText("Please don't manually add this environment variable. Use the appropriate game setting above.")
            error_dialog.exec()
            first_item.setText("")
            return

        if first_item.text():
            # When the second_item is None, we just use an empty string for the value.
            if second_item is None:
                if self.latest_item in list_of_keys:
                    config_helper.remove_option(f"{self.app_name}.env", self.latest_item)
                    config_helper.save_config()

                config_helper.add_option(f"{self.app_name}.env", first_item.text(), "")
                config_helper.save_config()
            else:
                if self.latest_item in list_of_keys:
                    config_helper.remove_option(f"{self.app_name}.env", self.latest_item)
                    config_helper.save_config()

                config_helper.add_option(
                    f"{self.app_name}.env",
                    first_item.text(),
                    second_item.text()
                )
                config_helper.save_config()

        row_count = self.env_vars_table.rowCount()
        last_item = self.env_vars_table.item(row_count - 1, 0)

        if last_item is not None:
            if last_item.text():
                self.env_vars_table.insertRow(row_count)
                trash_icon = QTableWidgetItem()
                trash_icon.setIcon(qtawesome.icon("mdi.delete"))
                self.env_vars_table.setVerticalHeaderItem(row_count, trash_icon)

    def remove_row(self, index):
        # The user also should be able to delete the row,
        # even if rowCount() is lower than 1, but then the row
        # should be just cleared. (And not deleted)

        first_item = self.env_vars_table.item(index, 0)

        # The first item needs to have some text, else we don't delete it.
        if first_item is None:
            return

        # If the user tries to delete one of the readonly vars, we show a message and return.
        if first_item.text() in self.list_of_readonly:
            error_dialog = QMessageBox()
            error_dialog.setText("Please use the appropriate setting above to remove this key.")
            error_dialog.exec()
            return

        if first_item is not None:
            self.env_vars_table.removeRow(index)
        try:
            list_of_keys = []
            for key in self.core.lgd.config[f"{self.app_name}.env"]:
                list_of_keys.append(key)
            config_helper.remove_option(f"{self.app_name}.env", list_of_keys[index])
        except (KeyError, IndexError):
            pass

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Delete or e.key() == Qt.Key_Backspace:
            selected_items = self.env_vars_table.selectedItems()
            for i in selected_items:
                config_helper.remove_option(f"{self.app_name}.env", i.text())
                self.env_vars_table.removeRow(i.row())
        elif e.key() == Qt.Key_Escape:
            self.parent().layout().setCurrentIndex(0)

    def update_game(self, app_name):
        self.app_name = app_name
        self.import_env_vars()
