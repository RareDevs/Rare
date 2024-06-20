import os
from logging import getLogger
from typing import Tuple, Union, Optional

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QGroupBox, QFileDialog, QFormLayout, QComboBox

from rare.models.wrapper import Wrapper, WrapperType
from rare.shared import RareCore
from rare.shared.wrappers import Wrappers
from rare.utils import config_helper as config
from rare.utils.compat import steam
from rare.utils.paths import proton_compat_dir
from rare.widgets.indicator_edit import PathEdit, IndicatorReasonsCommon

logger = getLogger("ProtonSettings")


class ProtonSettings(QGroupBox):
    # str: option key
    environ_changed: Signal = Signal(str)
    # bool: state
    tool_enabled: Signal = Signal(bool)

    def __init__(self, parent=None):
        super(ProtonSettings, self).__init__(parent=parent)
        self.setTitle(self.tr("Proton settings"))

        self.tool_combo = QComboBox(self)
        self.tool_combo.currentIndexChanged.connect(self.__on_proton_changed)

        self.tool_prefix = PathEdit(
            file_mode=QFileDialog.FileMode.Directory,
            edit_func=self.proton_prefix_edit,
            save_func=self.proton_prefix_save,
            placeholder=self.tr("Please select path for proton prefix"),
            parent=self
        )

        layout = QFormLayout(self)
        layout.addRow(self.tr("Proton tool"), self.tool_combo)
        layout.addRow(self.tr("Compat data"), self.tool_prefix)
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.setFormAlignment(Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignTop)

        self.app_name: str = "default"
        self.core = RareCore.instance().core()
        self.wrappers: Wrappers = RareCore.instance().wrappers()
        self.tool_wrapper: Optional[Wrapper] = None

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
                filter(lambda w: w.is_compat_tool, self.wrappers.get_game_wrapper_list(self.app_name))
            )
            self.tool_wrapper = wrapper
            tool = next(filter(lambda t: t.checksum == wrapper.checksum, tools))
            index = self.tool_combo.findData(tool)
        except StopIteration:
            index = 0
        self.tool_combo.setCurrentIndex(index)
        self.tool_combo.blockSignals(False)

        enabled = bool(self.tool_combo.currentData(Qt.ItemDataRole.UserRole))
        self.tool_prefix.blockSignals(True)
        self.tool_prefix.setText(config.get_proton_compatdata(self.app_name, fallback=""))
        self.tool_prefix.setEnabled(enabled)
        self.tool_prefix.blockSignals(False)

        super().showEvent(a0)

    def __on_proton_changed(self, index):
        steam_tool: Union[steam.ProtonTool, steam.CompatibilityTool] = self.tool_combo.itemData(index)

        steam_environ = steam.get_steam_environment(steam_tool, self.tool_prefix.text())
        for key, value in steam_environ.items():
            config.save_envvar(self.app_name, key, value)
            self.environ_changed.emit(key)

        wrappers = self.wrappers.get_game_wrapper_list(self.app_name)
        if self.tool_wrapper and self.tool_wrapper in wrappers:
            wrappers.remove(self.tool_wrapper)
        if steam_tool is None:
            self.tool_wrapper = None
        else:
            wrapper = Wrapper(
                command=steam_tool.command(), name=steam_tool.name, wtype=WrapperType.COMPAT_TOOL
            )
            wrappers.append(wrapper)
            self.tool_wrapper = wrapper
        self.wrappers.set_game_wrapper_list(self.app_name, wrappers)

        self.tool_prefix.setEnabled(steam_tool is not None)
        if steam_tool:
            if not (compatdata_path := config.get_proton_compatdata(self.app_name, fallback="")):
                compatdata_path = proton_compat_dir(self.app_name)
                config.save_proton_compatdata(self.app_name, str(compatdata_path))
                target = compatdata_path.joinpath("pfx")
                if not target.is_dir():
                    os.makedirs(target, exist_ok=True)
            self.tool_prefix.setText(str(compatdata_path))
        else:
            self.tool_prefix.setText("")

        self.tool_enabled.emit(steam_tool is not None)

    @staticmethod
    def proton_prefix_edit(text: str) -> Tuple[bool, str, int]:
        if not text:
            return False, text, IndicatorReasonsCommon.EMPTY
        parent_dir = os.path.dirname(text)
        return os.path.exists(parent_dir), text, IndicatorReasonsCommon.DIR_NOT_EXISTS

    def proton_prefix_save(self, text: str):
        if not text:
            return
        config.save_proton_compatdata(self.app_name, text)
        self.environ_changed.emit("STEAM_COMPAT_DATA_PATH")

