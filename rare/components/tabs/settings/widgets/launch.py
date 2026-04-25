import os
import shlex
import shutil
from typing import TypeVar

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QVBoxLayout,
)

import rare.utils.config_helper as config
from rare.shared import RareCore
from rare.utils.wrapper_exe import wrapper_path
from rare.widgets.indicator_edit import IndicatorReasonsCommon, PathEdit

from .wrappers import WrapperSettings


class LaunchSettingsBase(QGroupBox):
    # str: option key
    environ_changed: Signal = Signal(str)

    def __init__(self, rcore: RareCore, wrapper_widget: type[WrapperSettings], parent=None):
        super(LaunchSettingsBase, self).__init__(parent=parent)
        self.setTitle(self.tr('Launch'))

        self.core = rcore.core()
        self.app_name: str = 'default'

        self.prelaunch_cmd = PathEdit(
            path='',
            placeholder=self.tr('Path to a script or program to run before the game'),
            file_mode=QFileDialog.FileMode.ExistingFile,
            edit_func=self._prelaunch_cmd_edit_callback,
            save_func=self._prelaunch_cmd_save_callback,
        )

        self.prelaunch_args = QLineEdit('')
        self.prelaunch_args.setPlaceholderText(self.tr('Arguments to the script or program to run before the game'))
        self.prelaunch_args.setToolTip(self.prelaunch_args.placeholderText())
        self.prelaunch_args.textChanged.connect(self._prelaunch_changed)

        font = self.font()
        font.setItalic(True)

        self.prelaunch_check = QCheckBox(self.tr('Wait for the pre-launch command to finish before launching the game'))
        self.prelaunch_check.setFont(font)
        self.prelaunch_check.checkStateChanged.connect(self._prelauch_check_changed)

        prelaunch_layout = QVBoxLayout()
        prelaunch_layout.addWidget(self.prelaunch_cmd)
        prelaunch_layout.addWidget(self.prelaunch_args)
        prelaunch_layout.addWidget(self.prelaunch_check)

        self.main_layout = QFormLayout(self)
        self.main_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.main_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.main_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignVCenter)

        self.wrappers_widget = wrapper_widget(rcore, self)

        self.lgd_wrapper = QCheckBox(
            self.tr('Use "EpicGamesLauncher.exe" shim for compatibility with third-party launchers (Rockstar etc.)')
        )
        self.lgd_wrapper.setFont(font)
        self.lgd_wrapper.checkStateChanged.connect(self._lgd_wrapper_check_changed)

        self.main_layout.addRow(self.tr('Use fake EGL'), self.lgd_wrapper)
        self.main_layout.addRow(self.tr('Wrappers'), self.wrappers_widget)
        self.main_layout.addRow(self.tr('Pre-launch'), prelaunch_layout)

    def showEvent(self, a0: QShowEvent):
        if a0.spontaneous():
            return super().showEvent(a0)
        prelaunch = shlex.split(config.get_option(self.app_name, 'pre_launch_command', fallback=''))
        command = prelaunch.pop(0) if len(prelaunch) else ''
        arguments = prelaunch if len(prelaunch) else []
        wait = config.get_boolean(self.app_name, 'pre_launch_wait', fallback=False)

        self.prelaunch_cmd.setText(command)
        self.prelaunch_args.setText(shlex.join(arguments))
        self.prelaunch_check.setChecked(wait)
        self.prelaunch_check.setEnabled(bool(command))

        wrapper = config.get_envvar_with_global(self.app_name, 'LEGENDARY_WRAPPER_EXE', fallback=False)

        self.lgd_wrapper.setEnabled(wrapper_path().exists())
        self.lgd_wrapper.setChecked(wrapper_path().exists() and bool(wrapper) and os.path.exists(wrapper))

        return super().showEvent(a0)

    @Slot()
    def tool_enabled(self):
        self.wrappers_widget.update_state()

    @staticmethod
    def _prelaunch_cmd_edit_callback(text: str) -> tuple[bool, str, int]:
        if not text.strip():
            return True, text, IndicatorReasonsCommon.UNDEFINED
        if not os.path.isfile(text) and not shutil.which(text):
            return False, text, IndicatorReasonsCommon.FILE_NOT_EXISTS
        else:
            return True, text, IndicatorReasonsCommon.VALID

    def _prelaunch_cmd_save_callback(self, text):
        self.prelaunch_check.setEnabled(bool(text))
        self._prelaunch_changed()

    @Slot(Qt.CheckState)
    def _prelauch_check_changed(self, state: Qt.CheckState):
        config.set_boolean(self.app_name, 'pre_launch_wait', state != Qt.CheckState.Unchecked)

    @Slot()
    def _prelaunch_changed(self):
        command = self.prelaunch_cmd.text().strip()
        if not command:
            config.adjust_option(self.app_name, 'pre_launch_command', command)
            config.remove_option(self.app_name, 'pre_launch_wait')
            return
        command = shlex.quote(command)
        arguments = self.prelaunch_args.text().strip()
        config.adjust_option(self.app_name, 'pre_launch_command', ' '.join([command, arguments]))

    @Slot(Qt.CheckState)
    def _lgd_wrapper_check_changed(self, state: Qt.CheckState):
        _wrapper = str(wrapper_path())
        config.adjust_envvar(self.app_name, 'LEGENDARY_WRAPPER_EXE', _wrapper if state == Qt.CheckState.Checked else '')
        self.environ_changed.emit('LEGENDARY_WRAPPER_EXE')


LaunchSettingsType = TypeVar('LaunchSettingsType', bound=LaunchSettingsBase)
