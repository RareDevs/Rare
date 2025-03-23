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
    def __init__(self, option: str, title: str, desc: str = "", default_enabled: bool = False, values: Tuple = None, parent=None):
        self.option = option
        super().__init__(title, parent=parent)
        self.setChecked(default_enabled)
        self.default_enabled = default_enabled
        self.values = values
        self.setToolTip(desc)

    def setDefault(self):
        self.setChecked(self.default_enabled)

    def getValue(self) -> Optional[str]:
        # lk: return the check state in case of non-default, otherwise None
        checked = self.isChecked()
        value = f"{self.option}={self.values[int(checked)] if self.values else int(checked)}" if self.default_enabled or self.values else self.option
        return value if checked ^ self.default_enabled else None

    def setValue(self, options: Dict[str, str]):
        if options.get(self.option, None) is not None:
            if self.values:
                self.setChecked(bool(self.values.index(options[self.option])))
            else:
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

        self.ui.overlay_state_combo.addItem(self.tr("Global"), ActivationStates.GLOBAL)
        self.ui.overlay_state_combo.addItem(self.tr("Disabled"), ActivationStates.DISABLED)
        self.ui.overlay_state_combo.addItem(self.tr("Enabled (defaults)"), ActivationStates.DEFAULTS)
        self.ui.overlay_state_combo.addItem(self.tr("Enabled (custom)"), ActivationStates.CUSTOM)

        self.envvar: Union[str, None] = None
        self.force_disabled: Union[str, None] = None
        self.force_defaults: Union[str, None] = None
        self.separator: Union[str, None] = None
        self.app_name: str = "default"

        self.option_widgets: List[Union[OverlayCheckBox, OverlayLineEdit, OverlayComboBox]] = []
        # self.checkboxes: Dict[str, OverlayCheckBox] = {}
        # self.values: Dict[str, Union[OverlayLineEdit, OverlayComboBox]] = {}

        self.ui.options_group.setTitle(self.tr("Custom options"))
        self.ui.overlay_state_combo.currentIndexChanged.connect(self.update_settings)

    def setupWidget(
        self,
        grid_map: List[OverlayCheckBox],
        form_map: List[Tuple[Union[OverlayLineEdit, OverlayComboBox], str]],
        label: str,
        envvar: str,
        force_disabled: str,
        force_defaults: str,
        separator: str,
    ):
        self.envvar = envvar
        self.force_disabled = force_disabled
        self.force_defaults = force_defaults
        self.separator = separator

        self.ui.overlay_state_label.setText(label)

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
        current_state = self.ui.overlay_state_combo.currentData(Qt.ItemDataRole.UserRole)
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

            config.set_envvar(self.app_name, self.envvar, self.separator.join(options))

        self.environ_changed.emit(self.envvar)
        self.update_settings_override(current_state)

    def setCurrentState(self, state: ActivationStates):
        self.ui.overlay_state_combo.setCurrentIndex(self.ui.overlay_state_combo.findData(state, Qt.ItemDataRole.UserRole))
        self.ui.options_group.setEnabled(state == ActivationStates.CUSTOM)

    def showEvent(self, a0: QShowEvent):
        if a0.spontaneous():
            return super().showEvent(a0)
        self.ui.options_group.blockSignals(True)

        config_options = config.get_envvar(self.app_name, self.envvar, fallback=None)
        if config_options is None:
            logger.debug("Setting %s is not present", self.envvar)
            self.setCurrentState(ActivationStates.GLOBAL)

        elif config_options == self.force_disabled:
            self.setCurrentState(ActivationStates.DISABLED)

        elif config_options == self.force_defaults:
            self.setCurrentState(ActivationStates.DEFAULTS)

        else:
            self.setCurrentState(ActivationStates.CUSTOM)
            opts = {}
            for o in config_options.split(self.separator):
                if "=" in o:
                    k, v = o.split("=")
                    opts[k] = v
                else:
                    # lk: The value doesn't matter other than not being None
                    opts[o] = "enable"

            for widget in self.option_widgets:
                widget.setValue(opts)
            if opts:
                logger.info("Remaining options without a gui switch: %s", self.separator.join(opts.keys()))

        self.ui.options_group.blockSignals(False)
        return super().showEvent(a0)


class DxvkHudSettings(OverlaySettings):
    def __init__(self, parent=None):
        super(DxvkHudSettings, self).__init__(parent=parent)
        self.setTitle(self.tr("DXVK HUD"))
        grid = [
            OverlayCheckBox("fps", self.tr("FPS")),
            OverlayCheckBox("frametimes", self.tr("Frame time graph")),
            OverlayCheckBox("memory", self.tr("Memory usage")),
            OverlayCheckBox("allocations", self.tr("Memory chunk suballocation")),
            OverlayCheckBox("gpuload", self.tr("GPU usage")),
            OverlayCheckBox("devinfo", self.tr("Device info")),
            OverlayCheckBox("version", self.tr("DXVK version")),
            OverlayCheckBox("api", self.tr("D3D feature level")),
            OverlayCheckBox("compiler", self.tr("Compiler activity")),
            OverlayCheckBox("devinfo", self.tr("GPU driver and version")),
            OverlayCheckBox("drawcalls", self.tr("Draw calls per frame")),
        ]
        form = [
            (OverlayNumberInput("scale", 1.0), self.tr("Scale")),
            (OverlayNumberInput("opacity", 1.0), self.tr("Opacity")),

        ]
        self.setupWidget(grid, form, label=self.tr("Show HUD"), envvar="DXVK_HUD", force_disabled="0", force_defaults="1", separator=",")

    def update_settings_override(self, state: ActivationStates):
        pass


class DxvkConfigSettings(OverlaySettings):
    def __init__(self, parent=None):
        super(DxvkConfigSettings, self).__init__(parent=parent)
        self.setTitle(self.tr("DXVK Config"))
        dxvk_config_trinary = (
            ("Auto", "Auto"),
            ("True", "True"),
            ("False", "False")
        )
        grid = [

        ]
        form = [
            (OverlayLineEdit("dxvk.deviceFilter", "",), "dxvk.deviceFilter"),
            (OverlayNumberInput("dxgi.syncInterval", -1,), "dxgi.syncInterval"),
            (OverlayNumberInput("d3d9.presentInterval", -1, ), "d3d9.presentInterval"),
            (OverlayNumberInput("dxgi.maxFrameRate", 0,), "dxgi.maxFrameRate"),
            (OverlayNumberInput("d3d9.maxFrameRate", 0,), "d3d9.maxFrameRate"),
            (OverlaySelectInput("dxvk.tearFree", dxvk_config_trinary), "dxvk.tearFree"),

        ]
        self.setupWidget(grid, form, label=self.tr("Mode"), envvar="DXVK_CONFIG", force_disabled="0", force_defaults="", separator=";")

    def update_settings_override(self, state: ActivationStates):
        pass


class DxvkNvapiDrsSettings(OverlaySettings):
    def __init__(self, parent=None):
        super(DxvkNvapiDrsSettings, self).__init__(parent=parent)
        self.setTitle(self.tr("DXVK NVAPI Driver Settings"))

        def preset_range(start:str, end:str) -> Tuple[Tuple, ...]:
            return tuple(tuple(f"{p}preset_{chr(c)}" for p in ("", "render_")) for c in range(ord(start), ord(end) + 1))

        ngx_rr_presets = (
            ("off", "off"),
            *preset_range("a", "o"),
            ("latest", "render_preset_latest"),
            ("default", "default"),
        )
        ngx_sr_presets = (
            ("off", "off"),
            *preset_range("a", "o"),
            ("latest", "render_preset_latest"),
            ("default", "default"),
        )
        grid = [
            OverlayCheckBox("ngx_dlss_sr_override", self.tr("Super Resolution override"), values=("off", "on")),
            OverlayCheckBox("ngx_dlss_rr_override", self.tr("Ray Reconstruction override"), values=("off", "on")),
            OverlayCheckBox("ngx_dlss_fg_override", self.tr("Frame Generation override"), values=("off", "on")),
        ]
        form = [
            (OverlaySelectInput("ngx_dlss_sr_override_render_preset_selection", ngx_sr_presets),
             "Super Resolution preset"),
            (OverlaySelectInput("ngx_dlss_rr_override_render_preset_selection", ngx_rr_presets),
             "Ray Reconstruction preset"),
        ]
        self.setupWidget(grid, form, label=self.tr("Mode"), envvar="DXVK_NVAPI_DRS_SETTINGS", force_disabled="0", force_defaults="", separator=",")

    def update_settings_override(self, state: ActivationStates):
        pass


class MangoHudSettings(OverlaySettings):
    def __init__(self, parent=None):
        super(MangoHudSettings, self).__init__(parent=parent)
        self.setTitle(self.tr("MangoHud"))
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
        self.setupWidget(grid, form, label=self.tr("Show HUD"), envvar="MANGOHUD_CONFIG", force_disabled="no_display", force_defaults="read_cfg", separator=",")

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
    from argparse import Namespace
    from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout

    global config
    config = Namespace()
    def get_envvar(x, y, fallback):
        if y == "DXVK_NVAPI_DRS_SETTINGS":
            return "ngx_dlss_sr_override=off,ngx_dlss_rr_override_render_preset_selection=render_preset_d"
        else:
            return ""
    config.get_envvar = get_envvar
    config.set_option = lambda x, y, z: print(x, y, z)
    config.set_envvar = lambda x, y, z: print(x, y, z)
    config.remove_option = lambda x, y: print(x, y)
    config.remove_envvar = lambda x, y: print(x, y)
    config.save_config = lambda: print()

    app = QApplication(sys.argv)
    dlg = QDialog()

    dxvk_hud = DxvkHudSettings(dlg)
    dxvk_cfg = DxvkConfigSettings(dlg)
    dxvk_nvapi_drs = DxvkNvapiDrsSettings(dlg)
    mangohud = MangoHudSettings(dlg)

    layout = QVBoxLayout(dlg)
    layout.addWidget(dxvk_hud)
    layout.addWidget(dxvk_cfg)
    layout.addWidget(dxvk_nvapi_drs)
    layout.addWidget(mangohud)

    dlg.show()
    ret = app.exec()
    config.save_config()
    sys.exit(ret)
