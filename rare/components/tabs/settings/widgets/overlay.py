from abc import abstractmethod
from enum import IntEnum
from logging import getLogger
from typing import List, Dict, Tuple, Union, Optional

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QIntValidator, QDoubleValidator, QShowEvent
from PySide6.QtWidgets import QGroupBox, QCheckBox, QLineEdit, QComboBox

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
        return f"{self.option}={self.currentData(Qt.ItemDataRole.UserRole)}" if self.currentIndex() > 0 else None

    def setValue(self, options: Dict[str, str]):
        if (value := options.get(self.option, None)) is not None:
            self.setCurrentIndex(self.findData(value, Qt.ItemDataRole.UserRole))
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
    def __init__(self, option: str, values: Tuple, parent=None):
        super().__init__(option, parent=parent)
        for item in values:
            text, data = item
            self.addItem(text, data)
        # self.addItems([str(v) for v in values])
        # self.addItems(map(str, values))


class ActivationStates(IntEnum):
    GLOBAL = -1
    DISABLED = 0
    DEFAULTS = 1
    CUSTOM = 2


class OverlaySettings(QGroupBox):
    # str: option key
    environ_changed = Signal(str)

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
        current_state = self.ui.show_overlay_combo.currentData(Qt.ItemDataRole.UserRole)
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
            options = (name for widget in self.option_widgets if (name := widget.getValue()) is not None)

            config.set_envvar(self.app_name, self.envvar, ",".join(options))

        self.environ_changed.emit(self.envvar)
        self.update_settings_override(current_state)

    def setCurrentState(self, state: ActivationStates):
        self.ui.show_overlay_combo.setCurrentIndex(self.ui.show_overlay_combo.findData(state, Qt.ItemDataRole.UserRole))
        self.ui.options_group.setEnabled(state == ActivationStates.CUSTOM)

    def showEvent(self, a0: QShowEvent):
        if a0.spontaneous():
            return super().showEvent(a0)
        self.ui.options_group.blockSignals(True)

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
                widget.setValue(opts)
            if opts:
                logger.info("Remaining options without a gui switch: %s", ",".join(opts.keys()))

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
        form = [
            (OverlayNumberInput("scale", 1.0), self.tr("Scale"))
        ]
        self.setupWidget(grid, form, "DXVK_HUD", "0", "1")

    def update_settings_override(self, state: ActivationStates):
        pass


mangohud_position = (
    ("default", "default"),
    ("top-left", "top-left"),
    ("top-right", "top-right"),
    ("middle-left", "middle-left"),
    ("middle-right", "middle-right"),
    ("bottom-left", "bottom-left"),
    ("bottom-right", "bottom-right"),
    ("top-center", "top-center"),
)

mangohud_vsync = (
    ("config", None),
    ("adaptive", "0"),
    ("off", "1"),
    ("mailbox", "2"),
    ("on", "3"),
)

mangohud_gl_vsync = (
    ("config", None),
    ("off", "0"),
    ("on", "1"),
    ("half", "2"),
    ("third", "3"),
    ("quarter", "4"),
)


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
            (OverlayNumberInput("fps_limit", 0), self.tr("FPS limit")),
            (OverlaySelectInput("vsync", mangohud_vsync), self.tr("Vulkan vsync")),
            (OverlaySelectInput("gl_vsync", mangohud_gl_vsync), self.tr("OpenGL vsync")),
            (OverlayNumberInput("font_size", 24), self.tr("Font size")),
            (OverlaySelectInput("position", mangohud_position), self.tr("Position")),
        ]

        self.setupWidget(grid, form, "MANGOHUD_CONFIG", "no_display", "read_cfg")

    def showEvent(self, a0: QShowEvent):
        if a0.spontaneous():
            return super().showEvent(a0)
        self.ui.options_group.blockSignals(True)
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

        self.environ_changed.emit("MANGOHUD")


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout

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
