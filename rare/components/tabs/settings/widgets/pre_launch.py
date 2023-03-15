import os
import shutil
from typing import Tuple

from PyQt5.QtWidgets import QHBoxLayout, QCheckBox, QFileDialog

from rare.shared import LegendaryCoreSingleton
from rare.utils import config_helper
from rare.widgets.indicator_edit import PathEdit, IndicatorReasonsCommon


class PreLaunchSettings(QHBoxLayout):
    app_name: str

    def __init__(self):
        super(PreLaunchSettings, self).__init__()
        self.core = LegendaryCoreSingleton()
        self.edit = PathEdit(
            path="",
            placeholder=self.tr("Path to script"),
            file_mode=QFileDialog.ExistingFile,
            edit_func=self.edit_command,
            save_func=self.save_pre_launch_command,
        )
        self.layout().addWidget(self.edit)

        self.wait_check = QCheckBox(self.tr("Wait for finish"))
        self.layout().addWidget(self.wait_check)
        self.wait_check.stateChanged.connect(self.save_wait_finish)

    def edit_command(self, text: str) -> Tuple[bool, str, int]:
        if not text.strip():
            return True, text, IndicatorReasonsCommon.VALID

        if not os.path.isfile(text.split()[0]) and not shutil.which(text.split()[0]):
            return False, text, IndicatorReasonsCommon.FILE_NOT_EXISTS
        else:
            return True, text, IndicatorReasonsCommon.VALID

    def save_pre_launch_command(self, text):
        if text:
            config_helper.add_option(self.app_name, "pre_launch_command", text)
            self.wait_check.setDisabled(False)
        else:
            config_helper.remove_option(self.app_name, "pre_launch_command")
            self.wait_check.setDisabled(True)
            config_helper.remove_option(self.app_name, "pre_launch_wait")

    def save_wait_finish(self):
        config_helper.add_option(self.app_name, "pre_launch_wait", str(self.wait_check.isChecked()).lower())

    def load_settings(self, app_name):
        self.app_name = app_name

        command = self.core.lgd.config.get(app_name, "pre_launch_command", fallback="")
        self.edit.setText(command)

        wait = self.core.lgd.config.getboolean(app_name, "pre_launch_wait", fallback=False)
        self.wait_check.setChecked(wait)

        self.wait_check.setEnabled(bool(command))
