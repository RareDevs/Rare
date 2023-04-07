from enum import Enum
from logging import getLogger
from typing import List, Dict, Tuple, Any, Callable

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5.QtWidgets import QGroupBox, QCheckBox, QWidget, QLineEdit, QLabel, QComboBox

from rare.shared import LegendaryCoreSingleton
from rare.ui.components.tabs.settings.widgets.overlay import Ui_OverlaySettings
from rare.utils import config_helper

logger = getLogger("Overlay")


class TextInputField(QLineEdit):
    def __init__(self):
        super(TextInputField, self).__init__()
        self.value_changed = self.textChanged
        self.set_value = self.setText
        self.set_default = lambda: self.setText("")

    def get_value(self):
        return self.text()


class ComboBox(QComboBox):
    def __init__(self):
        super(ComboBox, self).__init__()
        self.value_changed = self.currentIndexChanged
        self.get_value = self.currentText
        self.set_value = self.setCurrentText
        self.set_default = lambda: self.setCurrentIndex(0)


class CustomOption:
    input_field: QWidget
    var_name: str

    @classmethod
    def string_input(cls, var_name: str, placeholder: str):
        tmp = cls()
        tmp.input_field = TextInputField()
        tmp.var_name = var_name
        tmp.input_field.setPlaceholderText(placeholder)
        return tmp

    @classmethod
    def number_input(cls, var_name: str, placeholder: Any, is_float: bool = False):
        tmp = cls()
        tmp.input_field = TextInputField()
        tmp.var_name = var_name
        tmp.input_field.setPlaceholderText(str(placeholder))
        if is_float:
            validator = QDoubleValidator()
        else:
            validator = QIntValidator()
        tmp.input_field.setValidator(validator)
        return tmp

    @classmethod
    def select_input(cls, var_name: str, options: List[str]):
        """options: default value in options[0]"""
        tmp = cls()
        tmp.input_field = ComboBox()
        tmp.var_name = var_name
        tmp.input_field.addItems(options)
        return tmp


class ActivationStates(Enum):
    DEFAULT = 0
    HIDDEN = 1
    ACTIVATED = 2


class OverlaySettings(QGroupBox, Ui_OverlaySettings):
    # str: option key
    environ_changed = pyqtSignal(str)
    name: str = "default"
    settings_updatable = True

    def __init__(self, checkboxes_map: List[Tuple[str, str]], value_map: List[Tuple[CustomOption, str]],
                 config_env_var_name: str, no_display_value: str,
                 set_activation_state: Callable[[Enum], None] = lambda x: None):
        super(OverlaySettings, self).__init__()
        self.setupUi(self)
        self.core = LegendaryCoreSingleton()
        self.config_env_var_name = config_env_var_name
        self.no_display_value = no_display_value
        self.set_activation_state = set_activation_state

        self.checkboxes: Dict[str, QCheckBox] = {}

        for i, (var_name, translated_text) in enumerate(checkboxes_map):
            cb = QCheckBox(translated_text)
            self.options_grid.addWidget(cb, i // 4, i % 4)
            self.checkboxes[var_name] = cb
            cb.stateChanged.connect(self.update_settings)

        self.values: Dict[str, QWidget] = {}

        num_rows = len(checkboxes_map) // 4
        for custom_option, translated_text in value_map:
            input_field = custom_option.input_field
            self.options_form.addRow(QLabel(translated_text), input_field)
            self.values[custom_option.var_name] = input_field
            input_field.value_changed.connect(self.update_settings)
            num_rows += 1

        self.show_overlay_combo.currentIndexChanged.connect(self.update_settings)

    def update_settings(self):
        if not self.settings_updatable:
            return
        if self.show_overlay_combo.currentIndex() == 0:
            # System default
            config_helper.remove_option(f"{self.name}.env", self.config_env_var_name)
            self.environ_changed.emit(self.config_env_var_name)
            self.gb_options.setDisabled(True)
            self.set_activation_state(ActivationStates.DEFAULT)
            return

        elif self.show_overlay_combo.currentIndex() == 1:
            # hidden
            config_helper.add_option(f"{self.name}.env", self.config_env_var_name, self.no_display_value)
            self.environ_changed.emit(self.config_env_var_name)
            self.gb_options.setDisabled(True)
            self.set_activation_state(ActivationStates.HIDDEN)
            return
        elif self.show_overlay_combo.currentIndex() == 2:
            self.gb_options.setDisabled(False)
            # custom options
            var_names = []
            for var_name, cb in self.checkboxes.items():
                if cb.isChecked():
                    var_names.append(var_name)

            for var_name, input_field in self.values.items():
                text = input_field.get_value()
                if text not in ["default", ""]:
                    var_names.append(f"{var_name}={text}")

            if not var_names:
                list(self.checkboxes.values())[0].setChecked(True)
                var_names.append(list(self.checkboxes.keys())[0])

            config_helper.add_option(f"{self.name}.env", self.config_env_var_name, ",".join(var_names))
            self.environ_changed.emit(self.config_env_var_name)
            self.set_activation_state(ActivationStates.ACTIVATED)

    def load_settings(self, name: str):
        self.settings_updatable = False
        # load game specific
        self.name = name

        for checkbox in self.checkboxes.values():
            checkbox.setChecked(False)
        for input_field in self.values.values():
            input_field.set_default()

        options = self.core.lgd.config.get(f"{self.name}.env", self.config_env_var_name, fallback=None)
        if options is None:
            logger.debug(f"No Overlay settings found {self.config_env_var_name}")
            self.show_overlay_combo.setCurrentIndex(0)
            self.gb_options.setDisabled(True)

        elif options == self.no_display_value:
            # not visible
            self.gb_options.setDisabled(True)
            self.show_overlay_combo.setCurrentIndex(1)

        else:
            self.show_overlay_combo.setCurrentIndex(2)
            for option in options.split(","):
                try:
                    if "=" in option:
                        var_name, value = option.split("=")
                        if var_name in self.checkboxes.keys():
                            self.checkboxes[var_name].setChecked(False)
                        else:
                            self.values[var_name].set_value(value)
                    else:
                        self.checkboxes[option].setChecked(True)
                except Exception as e:
                    logger.warning(e)

            self.gb_options.setDisabled(False)

        self.settings_updatable = True
