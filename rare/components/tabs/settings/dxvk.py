from logging import getLogger

from PyQt5.QtWidgets import QGroupBox

from rare import shared
from rare.ui.components.tabs.settings.dxvk import Ui_DxvkSettings

logger = getLogger("DXVK Settings")


class DxvkSettings(QGroupBox, Ui_DxvkSettings):

    def __init__(self, name=None):
        super(DxvkSettings, self).__init__()
        self.setupUi(self)

        self.name = name if name is not None else "default"
        self.core = shared.core

        self.dxvk_options_map = {
            "devinfo": self.devinfo,
            "fps": self.fps,
            "frametime": self.frametime,
            "memory": self.memory,
            "gpuload": self.gpuload,
            "version": self.version,
            "api": self.api,
        }

        self.load_settings()
        self.show_dxvk.currentIndexChanged.connect(self.store_settings)
        for opt in self.dxvk_options_map:
            self.dxvk_options_map[opt].stateChanged.connect(self.store_settings)

    # Show HUD ComboBox
    # System Default, index 0, removes DXVK_HUD to use setting from env
    # Hidden        , index 1, adds DXVK_HUD=0 to override system configuration
    # Visible       , index 2, adds DXVK_HUD=1 to override system configuration
    # Custom Options, index 3, adds DXVK_HUD=devinfo,fps and enables the customization panel

    def load_settings(self):
        dxvk_options = self.core.lgd.config.get(f"{self.name}.env", "DXVK_HUD", fallback=None)
        self.gb_dxvk_options.setDisabled(True)
        if dxvk_options is not None:
            if dxvk_options == "0":
                self.show_dxvk.setCurrentIndex(1)
            elif dxvk_options == "1":
                self.show_dxvk.setCurrentIndex(2)
            else:
                self.show_dxvk.setCurrentIndex(3)
                self.gb_dxvk_options.setDisabled(False)
                for opt in dxvk_options.split(","):
                    try:
                        self.dxvk_options_map[opt].setChecked(True)
                    except KeyError:
                        print("Malformed DXVK Option: " + opt)
                        continue
        else:
            self.show_dxvk.setCurrentIndex(0)

    def store_settings(self):
        show_dxvk_index = self.show_dxvk.currentIndex()
        if show_dxvk_index:
            if f"{self.name}.env" not in self.core.lgd.config.sections():
                self.core.lgd.config.add_section(f"{self.name}.env")
            if show_dxvk_index == 1:
                self.core.lgd.config[f"{self.name}.env"]["DXVK_HUD"] = "0"
            if show_dxvk_index == 2:
                self.core.lgd.config[f"{self.name}.env"]["DXVK_HUD"] = "1"
            if show_dxvk_index == 3:
                dxvk_options = []
                for opt in self.dxvk_options_map:
                    if self.dxvk_options_map[opt].isChecked():
                        dxvk_options.append(opt)
                if not dxvk_options:
                    # Check if this is the first activation
                    stored = self.core.lgd.config.get(f"{self.name}.env", "DXVK_HUD", fallback=None)
                    if stored not in [None, "0", "1"]:
                        self.core.lgd.config[f"{self.name}.env"]["DXVK_HUD"] = "0"
                    else:
                        dxvk_options = ["devinfo", "fps"]
                # Check again if dxvk_options changed due to first activation
                if dxvk_options:
                    self.core.lgd.config[f"{self.name}.env"]["DXVK_HUD"] = ",".join(dxvk_options)
        else:
            if self.core.lgd.config.get(f"{self.name}.env", "DXVK_HUD", fallback=None) is not None:
                self.core.lgd.config.remove_option(f"{self.name}.env", "DXVK_HUD")
                if not self.core.lgd.config[f"{self.name}.env"]:
                    self.core.lgd.config.remove_section(f"{self.name}.env")
        self.core.lgd.save_config()
        self.load_settings()
