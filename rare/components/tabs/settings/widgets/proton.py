import os
from logging import getLogger
from typing import Tuple, Union, Optional

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QShowEvent
from PyQt5.QtWidgets import QGroupBox, QFileDialog

from rare.models.wrapper import Wrapper, WrapperType
from rare.shared import RareCore
from rare.shared.wrappers import Wrappers
from rare.ui.components.tabs.settings.proton import Ui_ProtonSettings
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
        self.ui = Ui_ProtonSettings()
        self.ui.setupUi(self)

        self.ui.proton_combo.currentIndexChanged.connect(self.__on_proton_changed)
        self.proton_prefix = PathEdit(
            file_mode=QFileDialog.DirectoryOnly,
            edit_func=self.proton_prefix_edit,
            save_func=self.proton_prefix_save,
            placeholder=self.tr("Please select path for proton prefix"),
        )
        self.ui.prefix_layout.addWidget(self.proton_prefix)

        self.app_name: str = "default"
        self.core = RareCore.instance().core()
        self.wrappers: Wrappers = RareCore.instance().wrappers()
        self.tool_wrapper: Optional[Wrapper] = None

    def showEvent(self, a0: QShowEvent) -> None:
        if a0.spontaneous():
            return super().showEvent(a0)
        self.ui.proton_combo.blockSignals(True)
        self.ui.proton_combo.clear()
        self.ui.proton_combo.addItem(self.tr("Don't use a compatibility tool"), None)
        tools = proton.find_tools()
        for tool in tools:
            self.ui.proton_combo.addItem(tool.name, tool)
        try:
            wrapper = next(
                filter(lambda w: w.is_compat_tool, self.wrappers.get_game_wrapper_list(self.app_name))
            )
            self.tool_wrapper = wrapper
            tool = next(filter(lambda t: t.checksum == wrapper.checksum, tools))
            index = self.ui.proton_combo.findData(tool)
        except StopIteration:
            index = 0
        self.ui.proton_combo.setCurrentIndex(index)
        self.ui.proton_combo.blockSignals(False)
        enabled = bool(self.ui.proton_combo.currentIndex())
        self.proton_prefix.blockSignals(True)
        self.proton_prefix.setText(config.get_envvar(self.app_name, "STEAM_COMPAT_DATA_PATH", fallback=""))
        self.proton_prefix.setEnabled(enabled)
        self.proton_prefix.blockSignals(False)
        self.tool_enabled.emit(enabled)
        super().showEvent(a0)

    def __on_proton_changed(self, index):
        steam_tool: Union[proton.ProtonTool, proton.CompatibilityTool] = self.ui.proton_combo.itemData(index)

        steam_environ = proton.get_steam_environment(steam_tool)
        for key, value in steam_environ.items():
            if not value:
                config.remove_envvar(self.app_name, key)
            else:
                config.add_envvar(self.app_name, key, value)
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

        self.proton_prefix.setEnabled(steam_tool is not None)
        self.proton_prefix.setText(os.path.expanduser("~/.proton") if steam_tool is not None else "")

        self.tool_enabled.emit(steam_tool is not None)
        config.save_config()

    @staticmethod
    def proton_prefix_edit(text: str) -> Tuple[bool, str, int]:
        if not text:
            return False, text, IndicatorReasonsCommon.EMPTY
        parent_dir = os.path.dirname(text)
        return os.path.exists(parent_dir), text, IndicatorReasonsCommon.DIR_NOT_EXISTS

    def proton_prefix_save(self, text: str):
        if not text:
            return
        config.add_envvar(self.app_name, "STEAM_COMPAT_DATA_PATH", text)
        self.environ_changed.emit("STEAM_COMPAT_DATA_PATH")
        config.save_config()

    def load_settings(self, app_name: str):
        self.app_name = app_name
