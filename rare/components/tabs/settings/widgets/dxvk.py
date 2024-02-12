from PyQt5.QtCore import QCoreApplication

from .overlays import OverlaySettings, CustomOption


class DxvkSettings(OverlaySettings):
    def __init__(self, parent=None):
        super(DxvkSettings, self).__init__(
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
                (CustomOption.number_input("scale", 1, True), QCoreApplication.translate("DxvkSettings", "Scale"))
            ],
            "DXVK_HUD", "0",
            parent=parent
        )

        self.setTitle(self.tr("DXVK Settings"))
        self.gb_options.setTitle(self.tr("Custom options"))
