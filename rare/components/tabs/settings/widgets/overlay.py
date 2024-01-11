from abc import abstractmethod
from enum import Enum, IntEnum
from logging import getLogger
from typing import List, Dict, Tuple, Any, Union

from PyQt5.QtCore import QCoreApplication, pyqtSignal
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QShowEvent
from PyQt5.QtWidgets import QGroupBox, QCheckBox, QLineEdit, QComboBox

from rare.shared import LegendaryCoreSingleton
from rare.ui.components.tabs.settings.widgets.overlay import Ui_OverlaySettings
from rare.utils import config_helper as config

logger = getLogger("GameOverlays")


class OverlayLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super(OverlayLineEdit, self).__init__(parent=parent)
        self.valueChanged = self.textChanged
        self.setValue = self.setText

    def setDefault(self):
        self.setText("")

    def getValue(self):
        return self.text()


class OverlayComboBox(QComboBox):
    def __init__(self, parent=None):
        super(OverlayComboBox, self).__init__(parent=parent)
        self.valueChanged = self.currentIndexChanged
        self.setValue = self.setCurrentText
        self.getValue = self.currentText

    def setDefault(self):
        self.setCurrentIndex(0)


class CustomOption:
    option: str
    widget: Union[OverlayLineEdit, OverlayComboBox]

    @classmethod
    def string_input(cls, option: str, placeholder: str):
        tmp = cls()
        tmp.option = option
        tmp.widget = OverlayLineEdit()
        tmp.widget.setPlaceholderText(placeholder)
        return tmp

    @classmethod
    def number_input(cls, option: str, placeholder: Any, is_float: bool = False):
        tmp = cls()
        tmp.option = option
        tmp.widget = OverlayLineEdit()
        tmp.widget.setPlaceholderText(str(placeholder))
        validator = QDoubleValidator() if is_float else QIntValidator()
        tmp.widget.setValidator(validator)
        return tmp

    @classmethod
    def select_input(cls, option: str, values: List[str]):
        """options: default value in options[0]"""
        tmp = cls()
        tmp.option = option
        tmp.widget = OverlayComboBox()
        tmp.widget.addItems(values)
        return tmp


class ActivationStates(IntEnum):
    DEFAULT = -1
    HIDDEN = 0
    ENABLED = 1


class OverlaySettings(QGroupBox):
    # str: option key
    environ_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super(OverlaySettings, self).__init__(parent=parent)
        self.ui = Ui_OverlaySettings()
        self.ui.setupUi(self)

        self.core = LegendaryCoreSingleton()
        self.envvar_name: str = None
        self.force_disabled: str = None
        self.app_name: str = "default"
        self.checkboxes: Dict[str, QCheckBox] = {}
        self.values: Dict[str, Union[OverlayLineEdit, OverlayComboBox]] = {}

        self.ui.options_group.setTitle(self.tr("Custom options"))
        self.ui.show_overlay_combo.currentIndexChanged.connect(self.update_settings)

    def setupWidget(
        self,
        checkbox_map: List[Tuple[str, str]],
        custom_map: List[Tuple[CustomOption, str]],
        envvar_name: str,
        force_disabled: str,
    ):
        self.envvar_name = envvar_name
        self.force_disabled = force_disabled

        for i, (variable, text) in enumerate(checkbox_map):
            checkbox = QCheckBox(text)
            self.ui.options_grid.addWidget(checkbox, i // 4, i % 4)
            self.checkboxes[variable] = checkbox
            checkbox.stateChanged.connect(self.update_settings)

        for option, text in custom_map:
            widget = option.widget
            self.ui.options_form.addRow(text, widget)
            self.values[option.option] = widget
            widget.valueChanged.connect(self.update_settings)

    @abstractmethod
    def set_activation_state(self, state: ActivationStates):
        raise NotImplementedError

    def update_settings(self):
        if self.ui.show_overlay_combo.currentIndex() == 0:
            # System default
            config.remove_envvar(self.app_name, self.envvar_name)
            self.environ_changed.emit(self.envvar_name)
            self.ui.options_group.setDisabled(True)
            self.set_activation_state(ActivationStates.DEFAULT)
            return

        elif self.ui.show_overlay_combo.currentIndex() == 1:
            # hidden
            config.set_envvar(self.app_name, self.envvar_name, self.force_disabled)
            self.environ_changed.emit(self.envvar_name)
            self.ui.options_group.setDisabled(True)
            self.set_activation_state(ActivationStates.HIDDEN)
            return
        elif self.ui.show_overlay_combo.currentIndex() == 2:
            self.ui.options_group.setDisabled(False)
            # custom options
            var_names = []
            for var_name, cb in self.checkboxes.items():
                if cb.isChecked():
                    var_names.append(var_name)

            for var_name, widget in self.values.items():
                text = widget.getValue()
                if text not in ["default", ""]:
                    var_names.append(f"{var_name}={text}")

            if not var_names:
                list(self.checkboxes.values())[0].setChecked(True)
                var_names.append(list(self.checkboxes.keys())[0])

            config.set_envvar(self.app_name, self.envvar_name, ",".join(var_names))
            self.environ_changed.emit(self.envvar_name)
            self.set_activation_state(ActivationStates.ENABLED)

    def showEvent(self, a0: QShowEvent):
        if a0.spontaneous():
            return super().showEvent(a0)

        for checkbox in self.checkboxes.values():
            checkbox.setChecked(False)
        for widget in self.values.values():
            widget.setDefault()

        options = config.get_envvar(self.app_name, self.envvar_name, fallback=None)
        if options is None:
            logger.debug(f"No Overlay settings found {self.envvar_name}")
            self.ui.show_overlay_combo.setCurrentIndex(0)
            self.ui.options_group.setDisabled(True)

        elif options == self.force_disabled:
            # not visible
            self.ui.options_group.setDisabled(True)
            self.ui.show_overlay_combo.setCurrentIndex(1)

        else:
            self.ui.show_overlay_combo.setCurrentIndex(2)
            for option in options.split(","):
                try:
                    if "=" in option:
                        key, value = option.split("=")
                        if key in self.checkboxes.keys():
                            self.checkboxes[key].setChecked(False)
                        else:
                            self.values[key].setValue(value)
                    else:
                        self.checkboxes[option].setChecked(True)
                except Exception as e:
                    logger.warning(e)

            self.ui.options_group.setDisabled(False)

        return super().showEvent(a0)


class DxvkSettings(OverlaySettings):
    def __init__(self, parent=None):
        super(DxvkSettings, self).__init__(parent=parent)
        self.setTitle(self.tr("DXVK settings"))
        self.setupWidget(
            [
                ("fps", QCoreApplication.translate("DxvkSettings", "FPS")),
                ("frametime", QCoreApplication.translate("DxvkSettings", "Frametime")),
                ("memory", QCoreApplication.translate("DxvkSettings", "Memory usage")),
                ("gpuload", QCoreApplication.translate("DxvkSettings", "GPU usage")),
                ("devinfo", QCoreApplication.translate("DxvkSettings", "Show Device info")),
                ("version", QCoreApplication.translate("DxvkSettings", "DXVK Version")),
                ("api", QCoreApplication.translate("DxvkSettings", "D3D feature level")),
                ("compiler", QCoreApplication.translate("DxvkSettings", "Compiler activity")),
            ],
            [
                (
                    CustomOption.number_input("scale", 1, True),
                    QCoreApplication.translate("DxvkSettings", "Scale"),
                )
            ],
            "DXVK_HUD",
            "0",
        )

    def set_activation_state(self, state: ActivationStates):
        pass


mangohud_position = [
    "default",
    "top-left",
    "top-right",
    "middle-left",
    "middle-right",
    "bottom-left",
    "bottom-right",
    "top-center",
]


class MangoHudSettings(OverlaySettings):
    def __init__(self, parent=None):
        super(MangoHudSettings, self).__init__(parent=parent)
        self.setTitle(self.tr("MangoHud settings"))
        self.setupWidget(
            [
                ("fps", QCoreApplication.translate("MangoSettings", "FPS")),
                ("frame_timing", QCoreApplication.translate("MangoSettings", "Frame Time")),
                ("cpu_stats", QCoreApplication.translate("MangoSettings", "CPU Load")),
                ("gpu_stats", QCoreApplication.translate("MangoSettings", "GPU Load")),
                ("cpu_temp", QCoreApplication.translate("MangoSettings", "CPU Temp")),
                ("gpu_temp", QCoreApplication.translate("MangoSettings", "GPU Temp")),
                ("ram", QCoreApplication.translate("MangoSettings", "Memory usage")),
                ("vram", QCoreApplication.translate("MangoSettings", "VRAM usage")),
                ("time", QCoreApplication.translate("MangoSettings", "Local Time")),
                ("version", QCoreApplication.translate("MangoSettings", "MangoHud Version")),
                ("arch", QCoreApplication.translate("MangoSettings", "System architecture")),
                ("histogram", QCoreApplication.translate("MangoSettings", "FPS Graph")),
                ("gpu_name", QCoreApplication.translate("MangoSettings", "GPU Name")),
                ("cpu_power", QCoreApplication.translate("MangoSettings", "CPU Power consumption")),
                ("gpu_power", QCoreApplication.translate("MangoSettings", "GPU Power consumption")),
            ],
            [
                (
                    CustomOption.number_input("font_size", 24, is_float=False),
                    QCoreApplication.translate("MangoSettings", "Font size"),
                ),
                (
                    CustomOption.select_input("position", mangohud_position),
                    QCoreApplication.translate("MangoSettings", "Position"),
                ),
            ],
            "MANGOHUD_CONFIG",
            "no_display",
        )

    def showEvent(self, a0: QShowEvent):
        if a0.spontaneous():
            return super().showEvent(a0)

        # override
        activated = bool(config.get_envvar(self.app_name, "MANGOHUD", None))
        mango_config = config.get_envvar(self.app_name, "MANGOHUD_CONFIG", fallback="")
        if not activated:
            self.ui.options_group.setDisabled(True)
            for i, checkbox in enumerate(list(self.checkboxes.values())):
                checkbox.setChecked(i < 4)
            self.ui.show_overlay_combo.setCurrentIndex(0)
            return
        self.ui.show_overlay_combo.setCurrentIndex(2)
        self.ui.options_group.setDisabled(False)
        for var_name, checkbox in list(self.checkboxes.items())[:4]:
            checkbox.setChecked(f"{var_name}=0" not in mango_config)

        return super().showEvent(a0)

    def set_activation_state(self, state: IntEnum):  # pylint: disable=E0202
        if state == ActivationStates.DEFAULT:
            config.remove_envvar(self.app_name, "MANGOHUD")
            config.remove_envvar(self.app_name, "MANGOHUD_CONFIG")
            self.ui.options_group.setDisabled(True)

        elif state == ActivationStates.HIDDEN:
            config.set_envvar(self.app_name, "MANGOHUD", "1")
            config.set_envvar(self.app_name, "MANGOHUD_CONFIG", self.force_disabled)

        elif state == ActivationStates.ENABLED:
            mango_config = config.get_envvar(self.app_name, "MANGOHUD_CONFIG", fallback="")

            split_config = mango_config.split(",")
            for name in list(self.checkboxes.keys())[:4]:
                if name in split_config:
                    split_config.remove(name)
            mango_config = ",".join(split_config)

            # first three are activated by default
            for var_name, checkbox in list(self.checkboxes.items())[:4]:
                if not checkbox.isChecked():
                    if mango_config:
                        mango_config += f",{var_name}=0"
                    else:
                        mango_config = f"{var_name}=0"
            if mango_config:
                config.set_envvar(self.app_name, "MANGOHUD", "1")
                config.set_envvar(self.app_name, "MANGOHUD_CONFIG", mango_config)
            else:
                config.remove_envvar(self.app_name, "MANGOHUD")
                config.remove_envvar(self.app_name, "MANGOHUD_CONFIG")
        self.environ_changed.emit("MANGOHUD")
        self.environ_changed.emit("MANGOHUD_CONFIG")
