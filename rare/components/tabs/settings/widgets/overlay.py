from abc import abstractmethod
from enum import IntEnum
from logging import getLogger
from typing import List, Dict, Tuple, Union, Optional

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QShowEvent
from PyQt5.QtWidgets import QGroupBox, QCheckBox, QLineEdit, QComboBox

from rare.ui.components.tabs.settings.widgets.overlay import Ui_OverlaySettings
from rare.utils import config_helper as config

logger = getLogger("GameOverlays")


class OverlayLineEdit(QLineEdit):
    def __init__(self, option: str, placeholder: str, parent=None):
        self.option = option
        super(OverlayLineEdit, self).__init__(parent=parent)
        self.valueChanged = self.textChanged

        self.setPlaceholderText(placeholder)

    def setDefault(self):
        self.setText("")

    def getValue(self) -> Optional[str]:
        return f"{self.option}={text}" if (text := self.text()) else None

    def setValue(self, options: Dict[str, str]):
        if (value := options.get(self.option, None)) is not None:
            self.setText(value)
            options.pop(self.option)
        else:
            self.setDefault()


class OverlayComboBox(QComboBox):
    def __init__(self, option: str, parent=None):
        self.option = option
        super(OverlayComboBox, self).__init__(parent=parent)
        self.valueChanged = self.currentIndexChanged

    def setDefault(self):
        self.setCurrentIndex(0)

    def getValue(self) -> Optional[str]:
        return f"{self.option}={self.currentText()}" if self.currentIndex() > 0 else None

    def setValue(self, options: Dict[str, str]):
        if (value := options.get(self.option, None)) is not None:
            self.setCurrentText(value)
            options.pop(self.option)
        else:
            self.setDefault()


class OverlayCheckBox(QCheckBox):
    def __init__(self, option: str, title: str, desc: str = "", default_enabled: bool = False, parent=None):
        self.option = option
        super().__init__(title, parent=parent)
        self.setChecked(default_enabled)
        self.default_enabled = default_enabled
        self.setToolTip(desc)

    def setDefault(self):
        self.setChecked(self.default_enabled)

    def getValue(self) -> Optional[str]:
        # lk: return the check state in case of non-default, otherwise None
        checked = self.isChecked()
        value = f"{self.option}={int(checked)}" if self.default_enabled else self.option
        return value if checked ^ self.default_enabled else None

    def setValue(self, options: Dict[str, str]):
        if options.get(self.option, None) is not None:
            self.setChecked(not self.default_enabled)
            options.pop(self.option)
        else:
            self.setChecked(self.default_enabled)


class OverlayStringInput(OverlayLineEdit):
    def __init__(self, option: str, placeholder: str, parent=None):
        super().__init__(option, placeholder, parent=parent)


class OverlayNumberInput(OverlayLineEdit):
    def __init__(self, option: str, placeholder: Union[int, float], parent=None):
        super().__init__(option, str(placeholder), parent=parent)
        validator = QDoubleValidator(self) if isinstance(placeholder, float) else QIntValidator(self)
        self.setValidator(validator)


class OverlaySelectInput(OverlayComboBox):
    def __init__(self, option: str, values: List, parent=None):
        super().__init__(option, parent=parent)
        self.addItems([str(v) for v in values])


class ActivationStates(IntEnum):
    GLOBAL = -1
    DISABLED = 0
    DEFAULTS = 1
    CUSTOM = 2


class OverlaySettings(QGroupBox):
    # str: option key
    environ_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super(OverlaySettings, self).__init__(parent=parent)
        self.ui = Ui_OverlaySettings()
        self.ui.setupUi(self)

        self.ui.show_overlay_combo.addItem(self.tr("Global"), ActivationStates.GLOBAL)
        self.ui.show_overlay_combo.addItem(self.tr("Disabled"), ActivationStates.DISABLED)
        self.ui.show_overlay_combo.addItem(self.tr("Enabled (defaults)"), ActivationStates.DEFAULTS)
        self.ui.show_overlay_combo.addItem(self.tr("Enabled (custom)"), ActivationStates.CUSTOM)

        self.envvar: str = None
        self.force_disabled: str = None
        self.force_defaults: str = None
        self.app_name: str = "default"

        self.option_widgets: List[Union[OverlayCheckBox, OverlayLineEdit, OverlayComboBox]] = []
        # self.checkboxes: Dict[str, OverlayCheckBox] = {}
        # self.values: Dict[str, Union[OverlayLineEdit, OverlayComboBox]] = {}

        self.ui.options_group.setTitle(self.tr("Custom options"))
        self.ui.show_overlay_combo.currentIndexChanged.connect(self.update_settings)

    def setupWidget(
        self,
        grid_map: List[OverlayCheckBox],
        form_map: List[Tuple[Union[OverlayLineEdit, OverlayComboBox], str]],
        envvar: str,
        force_disabled: str,
        force_defaults: str,
    ):
        self.envvar = envvar
        self.force_disabled = force_disabled
        self.force_defaults = force_defaults

        for i, widget in enumerate(grid_map):
            widget.setParent(self.ui.options_group)
            self.ui.options_grid.addWidget(widget, i // 4, i % 4)
            # self.checkboxes[widget.option] = widget
            self.option_widgets.append(widget)
            widget.stateChanged.connect(self.update_settings)

        for widget, label in form_map:
            widget.setParent(self.ui.options_group)
            self.ui.options_form.addRow(label, widget)
            # self.values[widget.option] = widget
            self.option_widgets.append(widget)
            widget.valueChanged.connect(self.update_settings)

    @abstractmethod
    def update_settings_override(self, state: ActivationStates):
        raise NotImplementedError

    def update_settings(self):
        current_state = self.ui.show_overlay_combo.currentData(Qt.UserRole)
        self.ui.options_group.setEnabled(current_state == ActivationStates.CUSTOM)

        if current_state == ActivationStates.GLOBAL:
            # System default (don't add any env variables)
            config.remove_envvar(self.app_name, self.envvar)

        elif current_state == ActivationStates.DISABLED:
            # hidden
            config.set_envvar(self.app_name, self.envvar, self.force_disabled)

        elif current_state == ActivationStates.DEFAULTS:
            config.set_envvar(self.app_name, self.envvar, self.force_defaults)

        elif current_state == ActivationStates.CUSTOM:
            self.ui.options_group.setDisabled(False)
            # custom options
            options = [widget.getValue() for widget in self.option_widgets]

            # options = []
            # for var_name, cb in self.checkboxes.items():
            #     options.append(cb.getValue())
            #
            # for var_name, widget in self.values.items():
            #     options.append(widget.getValue())

            options = [name for name in options if name is not None]

            config.set_envvar(self.app_name, self.envvar, ",".join(options))

        self.environ_changed.emit(self.envvar)
        self.update_settings_override(current_state)

        print(f"{self.envvar} = {config.get_envvar(self.app_name, self.envvar)}")

    def setCurrentState(self, state: ActivationStates):
        self.ui.show_overlay_combo.setCurrentIndex(self.ui.show_overlay_combo.findData(state, Qt.UserRole))
        self.ui.options_group.setEnabled(state == ActivationStates.CUSTOM)

    def showEvent(self, a0: QShowEvent):
        if a0.spontaneous():
            return super().showEvent(a0)
        self.ui.options_group.blockSignals(True)

        # for checkbox in self.checkboxes.values():
        #     checkbox.setChecked(False)
        # for widget in self.values.values():
        #     widget.setDefault()

        config_options = config.get_envvar(self.app_name, self.envvar, fallback=None)
        if config_options is None:
            logger.debug("Overlay setting %s is not present", self.envvar)
            self.setCurrentState(ActivationStates.GLOBAL)

        elif config_options == self.force_disabled:
            self.setCurrentState(ActivationStates.DISABLED)

        elif config_options == self.force_defaults:
            self.setCurrentState(ActivationStates.DEFAULTS)

        else:
            self.setCurrentState(ActivationStates.CUSTOM)
            opts = {}
            for o in config_options.split(","):
                if "=" in o:
                    k, v = o.split("=")
                    opts[k] = v
                else:
                    # lk: The value doesn't matter other than not being None
                    opts[o] = "enable"

            for widget in self.option_widgets:
                print(opts)
                widget.setValue(opts)
            # for checkbox in self.checkboxes.values():
            #     print(opts)
            #     checkbox.setValue(opts)
            #
            # for values in self.values.values():
            #     print(opts)
            #     values.setValue(opts)

            print(opts)
            # try:
            #     if "=" in option:
            #         key, value = option.split("=")
            #         if key in self.checkboxes.keys():
            #             self.checkboxes[key].setChecked(False)
            #         else:
            #             self.values[key].setValue(value)
            #     else:
            #         self.checkboxes[option].setChecked(True)
            # except Exception as e:
            #     logger.warning(e)

        self.ui.options_group.blockSignals(False)
        return super().showEvent(a0)


class DxvkSettings(OverlaySettings):
    def __init__(self, parent=None):
        super(DxvkSettings, self).__init__(parent=parent)
        self.setTitle(self.tr("DXVK settings"))
        grid = [
            OverlayCheckBox("fps", self.tr("FPS")),
            OverlayCheckBox("frametime", self.tr("Frametime")),
            OverlayCheckBox("memory", self.tr("Memory usage")),
            OverlayCheckBox("gpuload", self.tr("GPU usage")),
            OverlayCheckBox("devinfo", self.tr("Device info")),
            OverlayCheckBox("version", self.tr("DXVK version")),
            OverlayCheckBox("api", self.tr("D3D feature level")),
            OverlayCheckBox("compiler", self.tr("Compiler activity")),
        ]
        form = [(OverlayNumberInput("scale", 1.0), self.tr("Scale"))]
        self.setupWidget(grid, form, "DXVK_HUD", "0", "1")

    def update_settings_override(self, state: ActivationStates):
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
        grid = [
            OverlayCheckBox("read_cfg", self.tr("Read config")),
            OverlayCheckBox("fps", self.tr("FPS"), default_enabled=True),
            OverlayCheckBox("frame_timing", self.tr("Frame time"), default_enabled=True),
            OverlayCheckBox("cpu_stats", self.tr("CPU load"), default_enabled=True),
            OverlayCheckBox("gpu_stats", self.tr("GPU load"), default_enabled=True),
            OverlayCheckBox("cpu_temp", self.tr("CPU temperature")),
            OverlayCheckBox("gpu_temp", self.tr("GPU temperature")),
            OverlayCheckBox("ram", self.tr("Memory usage")),
            OverlayCheckBox("vram", self.tr("VRAM usage")),
            OverlayCheckBox("time", self.tr("Local time")),
            OverlayCheckBox("version", self.tr("MangoHud version")),
            OverlayCheckBox("arch", self.tr("System architecture")),
            OverlayCheckBox("histogram", self.tr("FPS graph")),
            OverlayCheckBox("gpu_name", self.tr("GPU name")),
            OverlayCheckBox("cpu_power", self.tr("CPU power consumption")),
            OverlayCheckBox("gpu_power", self.tr("GPU power consumption")),
        ]
        form = [
            (OverlayNumberInput("font_size", 24), self.tr("Font size")),
            (OverlaySelectInput("position", mangohud_position), self.tr("Position")),
        ]

        self.setupWidget(grid, form, "MANGOHUD_CONFIG", "no_display", "read_cfg")

    def showEvent(self, a0: QShowEvent):
        if a0.spontaneous():
            return super().showEvent(a0)
        self.ui.options_group.blockSignals(True)

        # override
        # activated = config.get_envvar(self.app_name, "MANGOHUD", None)
        # mango_config = config.get_envvar(self.app_name, "MANGOHUD_CONFIG", fallback="")
        # if activated is None:
        #     self.setCurrentState(ActivationStates.SYSTEM)
        # else:
        #     if activated == "1":
        # if not activated:
        #     self.ui.options_group.setDisabled(True)
        #     for i, checkbox in enumerate(list(self.checkboxes.values())):
        #         checkbox.setChecked(i < 4)
        #     self.ui.show_overlay_combo.setCurrentIndex(0)
        #     return
        # self.ui.show_overlay_combo.setCurrentIndex(2)
        # self.ui.options_group.setDisabled(False)
        # for var_name, checkbox in list(self.checkboxes.items())[:4]:
        #     checkbox.setChecked(f"{var_name}=0" not in mango_config)

        self.ui.options_group.blockSignals(False)
        return super().showEvent(a0)

    def update_settings_override(self, state: IntEnum):  # pylint: disable=E0202
        if state == ActivationStates.GLOBAL:
            config.remove_envvar(self.app_name, "MANGOHUD")

        elif state == ActivationStates.DISABLED:
            config.set_envvar(self.app_name, "MANGOHUD", "0")

        elif state == ActivationStates.DEFAULTS:
            config.set_envvar(self.app_name, "MANGOHUD", "1")

        elif state == ActivationStates.CUSTOM:
            config.set_envvar(self.app_name, "MANGOHUD", "1")
            # mango_config = config.get_envvar(self.app_name, self.envvar, fallback="")
            # mango_config = f"read_cfg,{mango_config}" if mango_config else "read_cfg"
            # config.set_envvar(self.app_name, self.envvar, mango_config)
            # self.environ_changed.emit("MANGOHUD_CONFIG")

            # split_config = mango_config.split(",")
            # for name in list(self.checkboxes.keys())[:4]:
            #     if name in split_config:
            #         split_config.remove(name)
            # mango_config = ",".join(split_config)
            #
            # # first three are activated by default
            # for var_name, checkbox in list(self.checkboxes.items())[:4]:
            #     if not checkbox.isChecked():
            #         if mango_config:
            #             mango_config += f",{var_name}=0"
            #         else:
            #             mango_config = f"{var_name}=0"
            # if mango_config:
            #     config.set_envvar(self.app_name, "MANGOHUD", "1")
            #     config.set_envvar(self.app_name, "MANGOHUD_CONFIG", mango_config)
            # else:
            #     config.remove_envvar(self.app_name, "MANGOHUD")
            #     config.remove_envvar(self.app_name, "MANGOHUD_CONFIG")

        self.environ_changed.emit("MANGOHUD")

        print(f"MANGOHUD = {config.get_envvar(self.app_name, 'MANGOHUD')}")


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout

    from legendary.core import LegendaryCore

    core = LegendaryCore()
    config.init_config_handler(core)

    app = QApplication(sys.argv)
    dlg = QDialog()

    dxvk = DxvkSettings(dlg)
    mangohud = MangoHudSettings(dlg)

    layout = QVBoxLayout(dlg)
    layout.addWidget(dxvk)
    layout.addWidget(mangohud)

    dlg.show()
    ret = app.exec()
    config.save_config()
    sys.exit(ret)
