import shutil
from enum import Enum

from PyQt5.QtCore import QCoreApplication, pyqtSignal
from PyQt5.QtWidgets import QMessageBox

from rare.shared import LegendaryCoreSingleton
from .overlay_settings import OverlaySettings, CustomOption, ActivationStates
from rare.utils import config_helper

position_values = ["default", "top-left", "top-right", "middle-left", "middle-right", "bottom-left",
                   "bottom-right", "top-center"]


class MangoHudSettings(OverlaySettings):

    set_wrapper_activated = pyqtSignal(bool)

    def __init__(self):
        super(MangoHudSettings, self).__init__(
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
                    QCoreApplication.translate("MangoSettings", "Font size")
                ),
                (
                    CustomOption.select_input("position", position_values),
                    QCoreApplication.translate("MangoSettings", "Position")
                )
            ],
            "MANGOHUD_CONFIG", "no_display", set_activation_state=self.set_activation_state
        )
        self.core = LegendaryCoreSingleton()
        self.setTitle(self.tr("MangoHud Settings"))
        self.gb_options.setTitle(self.tr("Custom options"))

    def load_settings(self, name: str):
        self.settings_updatable = False
        self.name = name
        # override
        cfg = self.core.lgd.config.get(f"{name}.env", "MANGOHUD_CONFIG", fallback="")
        activated = "mangohud" in self.core.lgd.config.get(name, "wrapper", fallback="")
        if not activated:
            self.settings_updatable = False
            self.gb_options.setDisabled(True)
            for i, checkbox in enumerate(list(self.checkboxes.values())):
                checkbox.setChecked(i < 4)
            self.show_overlay_combo.setCurrentIndex(0)
            self.settings_updatable = True
            return
        super(MangoHudSettings, self).load_settings(name)
        self.settings_updatable = False
        self.show_overlay_combo.setCurrentIndex(2)
        self.gb_options.setDisabled(False)
        for var_name, checkbox in list(self.checkboxes.items())[:4]:
            checkbox.setChecked(f"{var_name}=0" not in cfg)
        self.settings_updatable = True

    def set_activation_state(self, state: Enum):  # pylint: disable=E0202
        if state in [ActivationStates.DEFAULT, ActivationStates.HIDDEN]:
            self.set_wrapper_activated.emit(False)
            self.gb_options.setDisabled(True)

        elif state == ActivationStates.ACTIVATED:
            if not shutil.which("mangohud"):
                self.show_overlay_combo.setCurrentIndex(0)
                QMessageBox.warning(self, "Error", self.tr("Mangohud is not installed or not in path"))
                return

            cfg = self.core.lgd.config.get(f"{self.name}.env", "MANGOHUD_CONFIG", fallback="")

            split_config = cfg.split(",")
            for name in list(self.checkboxes.keys())[:4]:
                if name in split_config:
                    split_config.remove(name)
            cfg = ",".join(split_config)

            for var_name, checkbox in list(self.checkboxes.items())[:4]:  # first three are by default activated
                if not checkbox.isChecked():
                    if cfg:
                        cfg += f",{var_name}=0"
                    else:
                        cfg = f"{var_name}=0"
            if cfg:
                config_helper.add_option(f"{self.name}.env", "MANGOHUD_CONFIG", cfg)
                self.environ_changed.emit(self.config_env_var_name)
            else:
                config_helper.remove_option(f"{self.name}.env", "MANGOHUD_CONFIG")
                self.environ_changed.emit(self.config_env_var_name)

            self.set_wrapper_activated.emit(True)
