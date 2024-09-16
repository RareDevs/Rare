import os
import shlex
import shutil
from typing import Tuple, Type, TypeVar

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QCheckBox, QFileDialog, QFormLayout, QVBoxLayout, QGroupBox, QLineEdit

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

        self.prelaunch_cmd = PathEdit(
            path="",
            placeholder=self.tr("Path to a script or program to run before the game"),
            file_mode=QFileDialog.FileMode.ExistingFile,
            edit_func=self.__prelaunch_cmd_edit_callback,
            save_func=self.__prelaunch_cmd_save_callback,
        )

        self.prelaunch_args = QLineEdit("")
        self.prelaunch_args.setPlaceholderText(self.tr("Arguments to the script or program to run before the game"))
        self.prelaunch_args.setToolTip(self.prelaunch_args.placeholderText())
        self.prelaunch_args.textChanged.connect(self.__prelaunch_changed)

        self.prelaunch_check = QCheckBox(self.tr("Wait for the pre-launch command to finish before launching the game"))
        font = self.font()
        font.setItalic(True)
        self.prelaunch_check.setFont(font)
        self.prelaunch_check.stateChanged.connect(self.__prelauch_check_changed)

        prelaunch_layout = QVBoxLayout()
        prelaunch_layout.addWidget(self.prelaunch_cmd)
        prelaunch_layout.addWidget(self.prelaunch_args)
        prelaunch_layout.addWidget(self.prelaunch_check)

        self.main_layout = QFormLayout(self)
        self.main_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.main_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.main_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignTop)

        self.wrappers_widget = wrapper_widget(self)

        self.main_layout.addRow(self.tr("Wrappers"), self.wrappers_widget)
        self.main_layout.addRow(self.tr("Pre-launch"), prelaunch_layout)

    def showEvent(self, a0: QShowEvent):
        if a0.spontaneous():
            return super().showEvent(a0)
        prelaunch = shlex.split(config.get_option(self.app_name, "pre_launch_command", fallback=""))
        command = prelaunch.pop(0) if len(prelaunch) else ""
        arguments = prelaunch if len(prelaunch) else []
        wait = config.get_boolean(self.app_name, "pre_launch_wait", fallback=False)

        self.prelaunch_cmd.setText(command)
        self.prelaunch_args.setText(shlex.join(arguments))
        self.prelaunch_check.setChecked(wait)
        self.prelaunch_check.setEnabled(bool(command))

        return super().showEvent(a0)

    @Slot()
    def tool_enabled(self):
        self.wrappers_widget.update_state()

    @staticmethod
    def __prelaunch_cmd_edit_callback(text: str) -> Tuple[bool, str, int]:
        if not text.strip():
            return True, text, IndicatorReasonsCommon.VALID
        if not os.path.isfile(text) and not shutil.which(text):
            return False, text, IndicatorReasonsCommon.FILE_NOT_EXISTS
        else:
            return True, text, IndicatorReasonsCommon.VALID

    def __prelaunch_cmd_save_callback(self, text):
        self.prelaunch_check.setEnabled(bool(text))
        self.__prelaunch_changed()

    def __prelauch_check_changed(self):
        config.set_boolean(self.app_name, "pre_launch_wait", self.prelaunch_check.isChecked())

    @Slot()
    def __prelaunch_changed(self):
        command = self.prelaunch_cmd.text().strip()
        if not command:
            config.save_option(self.app_name, "pre_launch_command", command)
            config.remove_option(self.app_name, "pre_launch_wait")
            return
        command = shlex.quote(command)
        arguments = self.prelaunch_args.text().strip()
        config.save_option(self.app_name, "pre_launch_command", " ".join([command, arguments]))


LaunchSettingsType = TypeVar("LaunchSettingsType", bound=LaunchSettingsBase)
