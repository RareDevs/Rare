import os
from logging import getLogger
from typing import Tuple, Union, Optional

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QShowEvent
from PyQt5.QtWidgets import QGroupBox, QFileDialog, QFormLayout, QComboBox, QLabel

from rare.models.wrapper import Wrapper, WrapperType
from rare.shared import RareCore
from rare.shared.wrappers import Wrappers
from rare.utils import config_helper as config
from rare.utils.runners import proton
from rare.widgets.indicator_edit import PathEdit, IndicatorReasonsCommon

logger = getLogger("ProtonSettings")


class ProtonSettings(QGroupBox):
    # str: option key
    environ_changed: pyqtSignal = pyqtSignal(str)
    # bool: state
    tool_enabled: pyqtSignal = pyqtSignal(bool)

    def __init__(self, parent=None):
        super(ProtonSettings, self).__init__(parent=parent)
        self.setTitle(self.tr("Proton Settings"))

        self.tool_combo = QComboBox(self)
        self.tool_combo.currentIndexChanged.connect(self.__on_proton_changed)

        self.tool_prefix = PathEdit(
            file_mode=QFileDialog.DirectoryOnly,
            edit_func=self.proton_prefix_edit,
            save_func=self.proton_prefix_save,
            placeholder=self.tr("Please select path for proton prefix"),
            parent=self
        )

        layout = QFormLayout(self)
        layout.addRow(self.tr("Proton tool"), self.tool_combo)
        layout.addRow(self.tr("Compat data"), self.tool_prefix)
        layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.setFormAlignment(Qt.AlignLeading | Qt.AlignTop)

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
        tools = proton.find_tools()
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

        enabled = bool(self.tool_combo.currentData(Qt.UserRole))
        self.tool_prefix.blockSignals(True)
        self.tool_prefix.setText(config.get_proton_compatdata(self.app_name, fallback=""))
        self.tool_prefix.setEnabled(enabled)
        self.tool_prefix.blockSignals(False)

        super().showEvent(a0)

    def __on_proton_changed(self, index):
        steam_tool: Union[proton.ProtonTool, proton.CompatibilityTool] = self.tool_combo.itemData(index)

        steam_environ = proton.get_steam_environment(steam_tool)
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
        if steam_tool and not config.get_proton_compatdata(self.app_name, fallback=""):
            self.tool_prefix.setText(os.path.expanduser("~/.proton"))

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

