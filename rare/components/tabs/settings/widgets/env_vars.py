from logging import getLogger

from PyQt5.QtCore import Qt, QFileSystemWatcher
from PyQt5.QtWidgets import QGroupBox, QTableWidgetItem, QMessageBox, QPushButton

from rare.shared import LegendaryCoreSingleton
from rare.ui.components.tabs.settings.widgets.env_vars import Ui_EnvVars
from rare.utils import config_helper
from rare.utils.misc import icon

logger = getLogger("EnvVars")


class EnvVars(QGroupBox, Ui_EnvVars):
    def __init__(self, parent):
        super(EnvVars, self).__init__(parent=parent)
        self.setupUi(self)
        self.app_name = None
        self.core = LegendaryCoreSingleton()
        self.latest_item = None
        self.list_of_readonly = ["STEAM_COMPAT_DATA_PATH", "DXVK_HUD", "WINEPREFIX", "STEAM_COMPAT_CLIENT_INSTALL_PATH"]
        self.warn_msg = self.tr("Readonly, please edit this via the appropriate setting above.")
        self.setup_file_watcher()
        self.env_vars_table.cellChanged.connect(self.update_env_vars)
        self.env_vars_table.verticalHeader().sectionClicked.connect(self.remove_row)

    # We use this function to keep an eye on the config.
    # When the user uses for example the wineprefix settings, we need to update the table.
    # With this function, when the config file changes, we update the table.
    def setup_file_watcher(self):
        self.config_file_watcher = QFileSystemWatcher([str(self.core.lgd.config_path)], self)
        self.config_file_watcher.fileChanged.connect(self.import_env_vars)

    def append_row(self):
        # If the last row is not None, we insert a new one and set the correct icon.
        row_count = self.env_vars_table.rowCount()

        if row_count == 0:
            self.env_vars_table.insertRow(0)
            trash_icon = QTableWidgetItem()
            trash_icon.setIcon(icon("mdi.delete", "ei.minus"))
            self.env_vars_table.setVerticalHeaderItem(row_count, trash_icon)
            return

        last_item = self.env_vars_table.item(self.env_vars_table.rowCount() - 1, 0)

        if last_item is not None:
            self.env_vars_table.insertRow(row_count)
            trash_icon = QTableWidgetItem()
            trash_icon.setIcon(icon("mdi.delete", "ei.minus"))
            self.env_vars_table.setVerticalHeaderItem(row_count, trash_icon)

    def import_env_vars(self):
        self.env_vars_table.blockSignals(True)
        self.env_vars_table.clearContents()

        # If the config file doesnt have an env var section, we just set RowCount to 1 and return.
        if not self.core.lgd.config.has_section(f"{self.app_name}.env"):
            self.env_vars_table.setRowCount(1)
            trash_icon = QTableWidgetItem()
            trash_icon.setIcon(icon("mdi.delete", "ei.minus"))
            self.env_vars_table.setVerticalHeaderItem(0, trash_icon)
            self.env_vars_table.blockSignals(False)
            return

        # We count how many keys we have and insert new lines
        # (as many as we need).
        self.env_vars_table.setRowCount(len(self.core.lgd.config[f"{self.app_name}.env"]) + 1)

        # Each iteration we have to create a new QTableWidgetItem object,
        # else we segfault. (For using the same object in multiple references.)
        for i, (key, value) in enumerate(self.core.lgd.config[f"{self.app_name}.env"].items()):
            trash_icon = QTableWidgetItem()
            trash_icon.setIcon(icon("mdi.delete", "ei.minus"))
            self.env_vars_table.setVerticalHeaderItem(i, trash_icon)

            key_item = QTableWidgetItem()
            key_item.setText(key)
            self.env_vars_table.setItem(i, 0, key_item)

            value_item = QTableWidgetItem()
            value_item.setText(value)
            self.env_vars_table.setItem(i, 1, value_item)
            if key in self.list_of_readonly:
                key_item.setFlags(key_item.flags() ^ Qt.ItemIsEnabled)
                key_item.setToolTip(self.warn_msg)

                value_item.setFlags(value_item.flags() ^ Qt.ItemIsEnabled)
                value_item.setToolTip(self.warn_msg)

        trash_icon = QTableWidgetItem()
        trash_icon.setIcon(icon("mdi.delete", "ei.minus"))
        self.env_vars_table.setVerticalHeaderItem(self.env_vars_table.rowCount() - 1, trash_icon)

        self.env_vars_table.blockSignals(False)

    def update_env_vars(self, row, column):
        self.config_file_watcher.removePath(str(self.core.lgd.config_path))
        row_count = self.env_vars_table.rowCount()
        key_item = self.env_vars_table.item(row, 0)
        value_item = self.env_vars_table.item(row, 1)

        if key_item is not None and not key_item.text():
            try:
                list_of_config_keys = list(self.core.lgd.config[f"{self.app_name}.env"].keys())
            except KeyError:
                list_of_config_keys = []
            try:
                config_helper.remove_option(f"{self.app_name}.env", list_of_config_keys[row])
            except IndexError:
                # Item hasnt been saved to the config yet.
                pass
            self.env_vars_table.removeRow(key_item.row())
            self.append_row()
            return

        # get all config keys
        try:
            list_of_config_keys = list(self.core.lgd.config[f"{self.app_name}.env"].keys())
        except KeyError:
            list_of_config_keys = []

        # get all table keys
        list_of_keys_in_table = []
        for i in range(row_count):
            item = self.env_vars_table.item(i, 0)
            if item:
                list_of_keys_in_table.append(item.text())

        missing_item = list(set(list_of_config_keys) - set(list_of_keys_in_table))
        if len(missing_item) != 0:
            config_helper.remove_option(f"{self.app_name}.env", missing_item[0])

        # A env var always needs to have a key.
        # If it's none, we return.
        if key_item is None:
            return

        if key_item.text() in self.list_of_readonly:
            error_dialog = QMessageBox()
            error_dialog.setText(
                self.tr("Please don't manually add this environment variable. Use the appropriate game setting above."))
            error_dialog.exec()
            key_item.setText("")
            if value_item is not None:
                value_item.setText("")
            config_helper.remove_option(f"{self.app_name}.env", key_item.text())
            return

        if key_item.text():
            if "=" in key_item.text():
                error_dialog = QMessageBox()
                error_dialog.setText(
                    self.tr("Please don't use an equal sign in an env var."))
                error_dialog.exec()
                self.env_vars_table.removeRow(row)
                self.append_row()
                return

            if key_item.text() in list_of_config_keys and column == 0:
                ask_user = QMessageBox()
                ask_user.setText(
                    self.tr("The config already contains this environment variable."))
                ask_user.setInformativeText(
                    self.tr("Do you want to keep the newer one or the older one?"))

                ask_user.addButton(QPushButton("Keep the newer one"), QMessageBox.YesRole)
                ask_user.addButton(QPushButton("Keep the older one"), QMessageBox.NoRole)

                response = ask_user.exec()

                if response == 0:
                    if value_item is not None:
                        config_helper.add_option(f"{self.app_name}.env", key_item.text(), value_item.text())
                    else:
                        config_helper.add_option(f"{self.app_name}.env", key_item.text(), "")

                    item_to_safe = self.env_vars_table.findItems(key_item.text(), Qt.MatchExactly)

                    # aznd:
                    # This is to fix an issue where the user updates a env var, thats above the older one.
                    # so say if you have two env vars:
                    # something = newkey
                    # yes = oldkey
                    # if the user updates the something key to yes, it would delete the wrong row,
                    # since item_to_safe[0] is the first search result. but we dont want to delete that,
                    # we want to delete the second result.
                    # we use this simple if check to find out which case we have.
                    if key_item.row() < item_to_safe[0].row():
                        self.env_vars_table.removeRow(item_to_safe[0].row())
                    elif key_item.row() > item_to_safe[0].row():
                        self.env_vars_table.removeRow(item_to_safe[0].row())
                    else:
                        self.env_vars_table.removeRow(item_to_safe[1].row())

                    self.append_row()
                    return

                elif response == 1:
                    self.env_vars_table.removeRow(row)
                    self.append_row()
                    return

            # When the value_item is None, we just use an empty string for the value.
            if value_item is None:
                if self.latest_item in list_of_config_keys:
                    config_helper.remove_option(f"{self.app_name}.env", self.latest_item)
                    config_helper.save_config()

                config_helper.add_option(f"{self.app_name}.env", key_item.text(), "")
                config_helper.save_config()
            else:
                if self.latest_item in list_of_config_keys:
                    config_helper.remove_option(f"{self.app_name}.env", self.latest_item)
                    config_helper.save_config()

                config_helper.add_option(
                    f"{self.app_name}.env",
                    key_item.text(),
                    value_item.text()
                )
                config_helper.save_config()

        self.append_row()
        self.config_file_watcher.addPath(str(self.core.lgd.config_path))

    def remove_row(self, index):
        self.config_file_watcher.removePath(str(self.core.lgd.config_path))
        key_item = self.env_vars_table.item(index, 0)
        value_item = self.env_vars_table.item(index, 1)

        if key_item is None:
            if value_item is not None:
                value_item.setText("")
            return

        # If the user tries to delete one of the readonly vars, we return immediately.
        if key_item.text() in self.list_of_readonly:
            return

        if key_item is not None:
            self.env_vars_table.removeRow(index)
        try:
            list_of_keys = []
            for key in self.core.lgd.config[f"{self.app_name}.env"]:
                list_of_keys.append(key)
            config_helper.remove_option(f"{self.app_name}.env", list_of_keys[index])
        except (KeyError, IndexError):
            pass
        self.config_file_watcher.addPath(str(self.core.lgd.config_path))

    def check_if_item(self, item: QTableWidgetItem) -> bool:
        item_to_check = self.env_vars_table.findItems(item.text(), Qt.MatchExactly)
        if item_to_check[0].column() == 0:
            return False
        return True

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Delete or e.key() == Qt.Key_Backspace:
            selected_items = self.env_vars_table.selectedItems()

            if len(selected_items) == 0:
                return

            item_in_table = self.env_vars_table.findItems(selected_items[0].text(), Qt.MatchExactly)

            # Our first selection is in column 0.  So, we have to find out if the user 
            # only selected keys, or keys and values. we use the check_if_item func
            if item_in_table[0].column() == 0:
                which_index_to_use = 1
                if len(selected_items) == 1:
                    which_index_to_use = 0
                if self.check_if_item(selected_items[which_index_to_use]):
                    # User selected keys and values, so we skip the values
                    for i in selected_items[::2]:
                        if i:
                            config_helper.remove_option(f"{self.app_name}.env", i.text())
                            self.env_vars_table.removeRow(i.row())
                    self.append_row()
                else:
                    # user only selected keys
                    for i in selected_items:
                        if i:
                            config_helper.remove_option(f"{self.app_name}.env", i.text())
                            self.env_vars_table.removeRow(i.row())
                    self.append_row()

            # User only selected values, so we just set the text to ""
            elif item_in_table[0].column() == 1:
                [i.setText("") for i in selected_items]

        elif e.key() == Qt.Key_Escape:
            e.ignore()

    def update_game(self, app_name):
        self.app_name = app_name
        self.import_env_vars()
