import platform
import re
import sys
from collections import ChainMap
from typing import Any, Union

from PySide6.QtCore import Qt, QModelIndex, QAbstractTableModel, Slot
from PySide6.QtGui import QFont

from rare.lgndr.core import LegendaryCore
from rare.utils.misc import qta_icon

if platform.system() != "Windows":
    from rare.utils.compat.wine import get_wine_environment

if platform.system() in {"Linux", "FreeBSD"}:
    from rare.utils.compat.steam import get_steam_environment


class EnvVarsTableModel(QAbstractTableModel):
    def __init__(self, core: LegendaryCore, parent=None):
        super(EnvVarsTableModel, self).__init__(parent=parent)
        self.core = core

        # lk: validator matches anything starting with a letter or underscore
        # lk: and containing letters, numbers or underscores.
        # lk: Empty strings are considered invalid.
        self.__validator = re.compile(r"(^[A-Za-z_][A-Za-z0-9_]*)")
        self.__data_map: ChainMap = ChainMap()

        self.__readonly = {
            "DXVK_HUD",
            "MANGOHUD",
            "MANGOHUD_CONFIG",
        }
        if platform.system() != "Windows":
            self.__readonly.update(get_wine_environment().keys())
        if platform.system() in {"Linux", "FreeBSD"}:
            self.__readonly.update(get_steam_environment().keys())

        self.__default: str = "default"
        self.__appname: str = None

    @Slot(str)
    def reset(self):
        if not self.__appname:
            return
        self.load(self.__appname)

    def load(self, app_name: str):
        self.__appname = app_name
        self.beginResetModel()
        if not self.core.lgd.config.has_section(f"{self.__appname}.env"):
            self.core.lgd.config[f"{self.__appname}.env"] = {}
        self.__data_map = ChainMap(
            self.core.lgd.config[f"{self.__appname}.env"],
            self.core.lgd.config[f"{self.__default}.env"] if self.__appname != self.__default else {}
        )
        self.endResetModel()

    def __key(self, index: Union[QModelIndex, int]):
        if isinstance(index, QModelIndex):
            index = index.row()
        try:
            return list(self.__data_map)[index]
        except Exception as e:
            return ""

    def __is_local(self, index: Union[QModelIndex, int]):
        key = self.__key(index)
        return key in self.__data_map.maps[0].keys()

    def __is_global(self, index: Union[QModelIndex, int]):
        key = self.__key(index)
        return key in self.__data_map.maps[1].keys()

    def __is_readonly(self, index: Union[QModelIndex, int]):
        key = self.__key(index)
        return key in self.__readonly

    def __value(self, index: Union[QModelIndex, int]):
        if isinstance(index, QModelIndex):
            index = index.row()
        return self.__data_map[self.__key(index)]

    def __title(self, section: int):
        if section == 0:
            return self.tr("Key")
        elif section == 1:
            return self.tr("Value")

    def __data_length(self):
        return len(self.__data_map)

    def __is_key_valid(self, value: str):
        match = self.__validator.match(value)
        if not match:
            return False
        return value == match.group(0)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if role in {Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole}:
            if index.row() == self.__data_length():
                return ""
            if index.column() == 0:
                return self.__key(index)
            else:
                return self.__value(index)

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if index.column() == 0:
                return Qt.AlignmentFlag.AlignVCenter + Qt.AlignmentFlag.AlignRight
            else:
                return Qt.AlignmentFlag.AlignVCenter + Qt.AlignmentFlag.AlignLeft

        if role == Qt.ItemDataRole.FontRole:
            font = QFont("Monospace")
            font.setStyleHint(QFont.StyleHint.Monospace)
            if index.row() < self.__data_length() and not self.__is_local(index):
                font.setWeight(QFont.Weight.Bold)
            else:
                font.setWeight(QFont.Weight.Normal)
            return font

        if role == Qt.ItemDataRole.ToolTipRole:
            if index.row() == self.__data_length():
                if index.column() == 1:
                    return self.tr("Disabled, please set the variable name first.")
                else:
                    return None
            if self.__key(index) in self.__readonly:
                return self.tr("Readonly, please edit this via setting the appropriate setting.")

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self.__title(section)
        if role == Qt.ItemDataRole.DecorationRole:
            if orientation == Qt.Orientation.Vertical:
                if section < self.__data_length():
                    if self.__is_readonly(section) or not self.__is_local(section):
                        return qta_icon("mdi.lock", "ei.lock")
                    if self.__is_global(section) and self.__is_local(section):
                        return qta_icon("mdi.refresh", "ei.refresh")
                    if self.__is_local(section):
                        return qta_icon("mdi.delete", "ei.remove-sign")
                return qta_icon("mdi.plus", "ei.plus-sign")
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignVCenter + Qt.AlignmentFlag.AlignHCenter
        return None

    def flags(self, index: QModelIndex):
        # Disable the value cell on rows without a name
        if index.row() == self.__data_length():
            if index.column() == 1:
                return super().flags(index) ^ Qt.ItemFlag.ItemIsEnabled
            else:
                return Qt.ItemFlag.ItemIsEditable | super().flags(index)

        # Disable readonly variables
        if self.__is_readonly(index):
            return super().flags(index) ^ Qt.ItemFlag.ItemIsEnabled

        return Qt.ItemFlag.ItemIsEditable | super().flags(index)

    def rowCount(self, parent: QModelIndex = None) -> int:
        parent = parent if parent else QModelIndex()
        # The length of the outer list.
        return self.__data_length() + 1

    def columnCount(self, parent: QModelIndex = None) -> int:
        parent = parent if parent else QModelIndex()
        return 2

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.DisplayRole) -> bool:
        if role != Qt.ItemDataRole.EditRole:
            return False

        if index.column() == 0:
            # lk: for what is considered valid input, look at `__validator`
            if (not self.__is_key_valid(value)) or value in self.__readonly:
                return False
            # Do not accept existing variable names (this also protects against unchanged contents)
            if value in self.__data_map.keys():
                return False

            if index.row() == self.__data_length():
                self.beginInsertRows(QModelIndex(), self.rowCount(index), self.rowCount(index))
                self.endInsertRows()
                self.__data_map[value] = ""
                self.core.lgd.save_config()
                self.dataChanged.emit(index, index, [])
                self.headerDataChanged.emit(Qt.Orientation.Vertical, index.row(), index.row())
                # if we are on the last row, add a new last row to the table when setting the variable name
            else:
                # if we are not in the last row, we have to update an existing variable name
                old_key = self.__key(index)
                self.__data_map[value] = self.__data_map[old_key]
                self.core.lgd.save_config()
                # since we delete and add a new key, the new key will be moved at the end
                # deleting a local key can have the following effects
                # unique local key:
                #   old key deleted, new key added -> update range from index to end
                # old local key masking global key:
                #   old key remains, new key added -> insert row for new key, update from index to end
                # new key masking global key:
                #   can't happen because we do not accept existing keys
                if old_key in self.__data_map.maps[0].keys():
                    # delete the old key if it is a local one, replacing a local key
                    del self.__data_map[old_key]
                    self.core.lgd.save_config()
                if old_key in self.__data_map.maps[1].keys():
                    self.beginInsertRows(QModelIndex(), self.__data_length(), self.__data_length())
                    self.endInsertRows()
                self.dataChanged.emit(index, self.index(index.row(), 1), [])
                self.dataChanged.emit(self.index(self.__data_length() - 1, 0), self.index(self.__data_length() - 1, 1), [])
                self.headerDataChanged.emit(Qt.Orientation.Vertical, index.row(), index.row())
                self.headerDataChanged.emit(Qt.Orientation.Vertical, self.__data_length() - 1, self.__data_length() - 1)

        else:
            # lk: the check for key existance before assigning a value is ommitted
            # lk: The `Value` field of the table is disabled if the `Name`/key field is empty
            # lk: making is "impossible" to assign a value to an empty key
            # Do not accept unchanged contents
            if value == self.__value(index):
                return False

            self.__data_map[self.__key(index)] = value
            self.core.lgd.save_config()
            self.dataChanged.emit(self.index(index.row(), 0), index, [])
            self.headerDataChanged.emit(Qt.Orientation.Vertical, index.row(), index.row())
        return True

    def removeRow(self, row: int, parent: QModelIndex = None) -> bool:
        parent = parent if parent else QModelIndex()
        # Refuse to remove the last row
        if row == self.__data_length():
            return False
        # Refuse to remove readonly keys
        if self.__is_readonly(row):
            return False
        # Refuse to remove keys that don't have our app_name (in this case the default)
        if not self.__is_local(row):
            return False
        if self.__is_global(row):
            del self.__data_map[self.__key(row)]
            self.core.lgd.save_config()
            self.dataChanged.emit(self.index(row, 0), self.index(row, 1), [])
            self.headerDataChanged.emit(Qt.Orientation.Vertical, row, row)
        else:
            self.beginRemoveRows(QModelIndex(), row, row)
            del self.__data_map[self.__key(row)]
            self.core.lgd.save_config()
            self.endRemoveRows()
        return True


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QTableView, QHeaderView

    from rare.utils.misc import set_style_sheet
    from legendary.core import LegendaryCore

    class MainDialog(QDialog):
        def __init__(self):
            super().__init__()

            self.table = QTableView()
            self.model = EnvVarsTableModel(LegendaryCore())
            self.model.load("Tamarind")

            self.table.setModel(self.model)
            self.table.verticalHeader().sectionPressed.disconnect()
            self.table.horizontalHeader().sectionPressed.disconnect()
            self.table.verticalHeader().sectionClicked.connect(self.model.removeRow)
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            self.table.horizontalHeader().setStretchLastSection(True)
            self.table.setCornerButtonEnabled(False)

            self.setLayout(QVBoxLayout(self))
            self.layout().addWidget(self.table)

    app = QApplication(sys.argv)

    set_style_sheet("RareStyle")

    window = MainDialog()
    window.setFixedSize(800, 600)
    window.show()
    app.exec()
