import os
from enum import IntEnum
from logging import getLogger
from typing import Optional, Tuple, Union

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
)

from rare.models.wrapper import Wrapper, WrapperType
from rare.shared import RareCore
from rare.shared.wrappers import Wrappers
from rare.utils import config_helper as lgd_conf
from rare.utils.compat import steam
from rare.utils.paths import proton_compat_dir
from rare.widgets.indicator_edit import IndicatorReasonsCommon, PathEdit

logger = getLogger("ProtonSettings")


class ProtonSettings(QGroupBox):
    # str: option key
    environ_changed: Signal = Signal(str)
    # bool: state, str: path
    compat_tool_enabled: Signal = Signal(bool, str)
    # str: path
    compat_path_changed: Signal = Signal(str)

    class CompatLocation(IntEnum):
        NONE = 0
        SHARED = 1
        ISOLATED = 2
        CUSTOM = 3

    def __init__(self, rcore: RareCore, parent=None):
        super(ProtonSettings, self).__init__(parent=parent)
        self.rcore = rcore
        self.core = rcore.core()
        self.wrappers: Wrappers = rcore.wrappers()
        self.tool_wrapper: Optional[Wrapper] = None
        self.app_name: str = "default"

        self.setTitle(self.tr("Proton"))

        self.tool_combo = QComboBox(self)
        self.tool_combo.currentIndexChanged.connect(self.__on_tool_changed)

        self.compat_combo = QComboBox(self)
        self.compat_combo.addItem(self.tr("Shared"), ProtonSettings.CompatLocation.SHARED)
        self.compat_combo.addItem(self.tr("Isolated"), ProtonSettings.CompatLocation.ISOLATED)
        self.compat_combo.addItem(self.tr("Custom"), ProtonSettings.CompatLocation.CUSTOM)
        self.compat_combo.currentIndexChanged.connect(self.__on_compat_changed)

        self.compat_edit = PathEdit(
            file_mode=QFileDialog.FileMode.Directory,
            edit_func=self.proton_prefix_edit,
            save_func=self.proton_prefix_save,
            placeholder=self.tr("Please select path for proton prefix"),
            parent=self,
        )

        # self.winetricks_button = QPushButton(self.tr("Winetricks"), self)
        # self.create_button = QPushButton(self.tr("Create prefix"), self)
        #
        # button_layout = QHBoxLayout()
        # button_layout.addWidget(self.winetricks_button)
        # button_layout.addWidget(self.create_button)
        # button_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        layout = QFormLayout(self)
        layout.addRow(self.tr("Proton tool"), self.tool_combo)
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(self.compat_combo)
        folder_layout.addWidget(self.compat_edit)
        layout.addRow(self.tr("Compat folder"), folder_layout)
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.setFormAlignment(Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignTop)
        # layout.addRow(button_layout)

    def _get_compat_path(self, compat_location: CompatLocation):
        folder_name = "default"
        compat_path = proton_compat_dir(folder_name)
        return compat_path

    def _update_compat_folder(self, compat_path: str):
        shared_path = str(self._get_compat_path(ProtonSettings.CompatLocation.SHARED))
        isolated_path = str(self._get_compat_path(ProtonSettings.CompatLocation.ISOLATED))
        compat_location = ProtonSettings.CompatLocation.CUSTOM
        if compat_path == isolated_path:
            compat_location = ProtonSettings.CompatLocation.ISOLATED
        if compat_path == shared_path:
            compat_location = ProtonSettings.CompatLocation.SHARED
        self.compat_combo.setCurrentIndex(self.compat_combo.findData(compat_location, Qt.ItemDataRole.UserRole))
        self.compat_edit.setEnabled(compat_location is ProtonSettings.CompatLocation.CUSTOM)
        return compat_location

    def showEvent(self, a0: QShowEvent) -> None:
        if a0.spontaneous():
            return super().showEvent(a0)

        self.tool_combo.blockSignals(True)
        self.tool_combo.clear()
        self.tool_combo.addItem(self.tr("Don't use a compatibility tool"), None)
        tools = steam.find_tools()
        for tool in tools:
            self.tool_combo.addItem(tool.name, tool)
        try:
            wrapper = next(
                filter(
                    lambda w: w.is_compat_tool,
                    self.wrappers.get_wrappers(self.app_name),
                )
            )
            self.tool_wrapper = wrapper
            tool = next(filter(lambda t: t.checksum == wrapper.checksum, tools))
            index = self.tool_combo.findData(tool)
        except StopIteration:
            index = 0
        self.tool_combo.setCurrentIndex(index)
        self.tool_combo.blockSignals(False)

        enabled = bool(self.tool_combo.currentData(Qt.ItemDataRole.UserRole))
        compat_path = lgd_conf.get_compat_data_path(self.app_name, fallback="")

        self.compat_combo.blockSignals(True)
        compat_location = self._update_compat_folder(compat_path)
        self.compat_combo.setEnabled(enabled)
        self.compat_combo.blockSignals(False)

        self.compat_edit.blockSignals(True)
        self.compat_edit.setText(compat_path)
        self.compat_edit.setEnabled(enabled and compat_location is ProtonSettings.CompatLocation.CUSTOM)
        self.compat_edit.blockSignals(False)

        return super().showEvent(a0)

    @Slot(int)
    def __on_tool_changed(self, index):
        steam_tool: Union[steam.ProtonTool, steam.CompatibilityTool] = self.tool_combo.itemData(index, Qt.ItemDataRole.UserRole)

        steam_environ = steam.get_steam_environment(steam_tool, self.compat_edit.text())
        library_paths = steam_environ["STEAM_COMPAT_LIBRARY_PATHS"] if "STEAM_COMPAT_LIBRARY_PATHS" in steam_environ else ""
        if self.app_name != "default":
            install_path = self.rcore.get_game(self.app_name).install_path
            library_paths = (
                ":".join([library_paths, os.path.dirname(install_path)]) if library_paths else os.path.dirname(install_path)
            )
            # https://gitlab.steamos.cloud/steamrt/steam-runtime-tools/-/blob/main/docs/steam-compat-tool-interface.md#non-steam-games
            steam_environ["STEAM_COMPAT_INSTALL_PATH"] = install_path
        steam_environ["STEAM_COMPAT_LIBRARY_PATHS"] = library_paths
        for key, value in steam_environ.items():
            lgd_conf.adjust_envvar(self.app_name, key, value)
            self.environ_changed.emit(key)

        wrappers = self.wrappers.get_wrappers(self.app_name)
        if self.tool_wrapper and self.tool_wrapper in wrappers:
            wrappers.remove(self.tool_wrapper)
        if steam_tool is None:
            self.tool_wrapper = None
        else:
            wrapper = Wrapper(
                command=steam_tool.command(),
                name=steam_tool.name,
                wtype=WrapperType.COMPAT_TOOL,
            )
            wrappers.append(wrapper)
            self.tool_wrapper = wrapper
        self.wrappers.set_wrappers(self.app_name, wrappers)

        self.compat_combo.setEnabled(steam_tool is not None)
        self.compat_edit.setEnabled(steam_tool is not None)
        compat_path = ""
        if steam_tool:
            compat_path = lgd_conf.get_compat_data_path(self.app_name, fallback="")
            if not compat_path:
                compat_path = str(self._get_compat_path(ProtonSettings.CompatLocation.NONE))
            self._update_compat_folder(compat_path)
        self.compat_edit.setText(compat_path)
        self.compat_tool_enabled.emit(steam_tool is not None, compat_path)

    @Slot(int)
    def __on_compat_changed(self, index):
        compat_location: ProtonSettings.CompatLocation = self.compat_combo.itemData(index, Qt.ItemDataRole.UserRole)
        compat_path = str(self._get_compat_path(compat_location))
        lgd_conf.adjust_compat_data_path(self.app_name, compat_path)
        self.compat_edit.setText(compat_path)
        self.compat_edit.setEnabled(
            compat_location
            not in {
                ProtonSettings.CompatLocation.SHARED,
                ProtonSettings.CompatLocation.ISOLATED,
            }
        )

    @staticmethod
    def proton_prefix_edit(text: str) -> Tuple[bool, str, int]:
        if not text:
            return False, text, IndicatorReasonsCommon.IS_EMPTY
        if os.path.isdir(text):
            if os.listdir(text) and not os.path.exists(os.path.join(text, "pfx")):
                return False, text, IndicatorReasonsCommon.DIR_NOT_EMPTY
            return True, text, IndicatorReasonsCommon.VALID
        else:
            return False, text, IndicatorReasonsCommon.DIR_NOT_EXISTS

    def proton_prefix_save(self, text: str):
        lgd_conf.adjust_compat_data_path(self.app_name, text)
        self.environ_changed.emit("STEAM_COMPAT_DATA_PATH")
        self.compat_path_changed.emit(text)
