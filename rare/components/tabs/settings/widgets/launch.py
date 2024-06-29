import os
import shlex
import shutil
from typing import Tuple, Type, TypeVar

from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QShowEvent
from PyQt5.QtWidgets import QCheckBox, QFileDialog, QFormLayout, QVBoxLayout, QGroupBox

from rare.shared import LegendaryCoreSingleton
import rare.utils.config_helper as config
from rare.widgets.indicator_edit import PathEdit, IndicatorReasonsCommon
from .wrappers import WrapperSettings


class LaunchSettingsBase(QGroupBox):

    def __init__(
        self,
        wrapper_widget: Type[WrapperSettings],
        parent=None
    ):
        super(LaunchSettingsBase, self).__init__(parent=parent)
        self.setTitle(self.tr("Launch settings"))

        self.core = LegendaryCoreSingleton()
        self.app_name: str = "default"

        self.prelaunch_edit = PathEdit(
            path="",
            placeholder=self.tr("Path to script or program to run before the game launches"),
            file_mode=QFileDialog.FileMode.ExistingFile,
            edit_func=self.__prelaunch_edit_callback,
            save_func=self.__prelaunch_save_callback,
        )

        self.wrappers_widget = wrapper_widget(self)

        self.prelaunch_check = QCheckBox(self.tr("Wait for command to finish before starting the game"))
        font = self.font()
        font.setItalic(True)
        self.prelaunch_check.setFont(font)
        self.prelaunch_check.stateChanged.connect(self.__prelauch_check_changed)

        prelaunch_layout = QVBoxLayout()
        prelaunch_layout.addWidget(self.prelaunch_edit)
        prelaunch_layout.addWidget(self.prelaunch_check)

        self.main_layout = QFormLayout(self)
        self.main_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.main_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.main_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignTop)

        self.main_layout.addRow(self.tr("Wrappers"), self.wrappers_widget)
        self.main_layout.addRow(self.tr("Prelaunch"), prelaunch_layout)

    def showEvent(self, a0: QShowEvent):
        if a0.spontaneous():
            return super().showEvent(a0)
        command = config.get_option(self.app_name, "pre_launch_command", fallback="")
        wait = config.get_boolean(self.app_name, "pre_launch_wait", fallback=False)

        self.prelaunch_edit.setText(command)
        self.prelaunch_check.setChecked(wait)
        self.prelaunch_check.setEnabled(bool(command))

        return super().showEvent(a0)

    @pyqtSlot()
    def tool_enabled(self):
        self.wrappers_widget.update_state()

    @staticmethod
    def __prelaunch_edit_callback(text: str) -> Tuple[bool, str, int]:
        if not text.strip():
            return True, text, IndicatorReasonsCommon.VALID
        try:
            command = shlex.split(text)[0]
        except ValueError:
            return False, text, IndicatorReasonsCommon.WRONG_FORMAT
        if not os.path.isfile(command) and not shutil.which(command):
            return False, text, IndicatorReasonsCommon.FILE_NOT_EXISTS
        else:
            return True, text, IndicatorReasonsCommon.VALID

    def __prelaunch_save_callback(self, text):
        config.save_option(self.app_name, "pre_launch_command", text)
        self.prelaunch_check.setEnabled(bool(text))
        if not text:
            config.remove_option(self.app_name, "pre_launch_wait")

    def __prelauch_check_changed(self):
        config.set_boolean(self.app_name, "pre_launch_wait", self.prelaunch_check.isChecked())


LaunchSettingsType = TypeVar("LaunchSettingsType", bound=LaunchSettingsBase)
