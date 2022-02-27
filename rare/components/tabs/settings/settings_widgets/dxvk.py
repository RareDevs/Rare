from PyQt5.QtCore import QCoreApplication

from .overlay_settings import OverlaySettings, CustomOption


class DxvkSettings(OverlaySettings):
    def __init__(self):
        super(DxvkSettings, self).__init__(
            [
                ("fps", QCoreApplication.translate("DxvkSettings", "FPS")),
                ("frametime", QCoreApplication.translate("DxvkSettings", "Frametime")),
                ("memory", QCoreApplication.translate("DxvkSettings", "Memory usage")),
                ("gpuload", QCoreApplication.translate("DxvkSettings", "GPU usage")),
                ("devinfo", QCoreApplication.translate("DxvkSettings", "Show Device info")),
                ("version", QCoreApplication.translate("DxvkSettings", "DXVK Version")),
                ("api", QCoreApplication.translate("DxvkSettings", "D3D feature level")),
            ],
            [
                (CustomOption.number_input("scale", 1, True), QCoreApplication.translate("DxvkSettings", "Scale"))
            ],
            "DXVK_HUD", "0"
        )

        self.setTitle(self.tr("DXVK Settings"))
        self.gb_options.setTitle(self.tr("Custom options"))
