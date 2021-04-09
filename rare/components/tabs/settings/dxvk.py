from logging import getLogger

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QCheckBox, QVBoxLayout, QWidgetAction, QMenu, QToolButton, QHBoxLayout, QGroupBox

from custom_legendary.core import LegendaryCore

logger = getLogger("DXVK Settings")


class DxvkWidget(QGroupBox):

    def __init__(self, core: LegendaryCore):
        super(DxvkWidget, self).__init__()
        self.core = core
        self.setObjectName("settings_widget")
        self.dxvk_settings = {
            "fps": [False, "Fps"],
            "gpuload": [False, self.tr("GPU usage")],
            "memory": [False, self.tr("Used Memory")],
            "devinfo": [False, self.tr("Device info")],
            "version": [False, self.tr("DXVK version")],
            "api": [False, self.tr("D3D Level of application")],
            "frametime": [False, self.tr("Frame time graph")]
        }
        self.name = "default"
        self.layout = QVBoxLayout()
        self.child_layout = QHBoxLayout()
        self.setTitle(self.tr("dxvk settings"))
        self.show_dxvk = QCheckBox("Show Dxvk HUD")

        self.more_settings = QToolButton()
        dxvk_hud = self.core.lgd.config.get(f"{self.name}.env", "DXVK_HUD", fallback="")

        self.more_settings.setDisabled(not dxvk_hud == "")
        if dxvk_hud:
            for s in dxvk_hud.split(","):
                self.dxvk_settings[s][0] = True

        self.more_settings.setPopupMode(QToolButton.InstantPopup)
        self.more_settings.setMenu(QMenu())
        self.more_settings.setText("More DXVK settings")

        action = QWidgetAction(self)
        self.more_settings_widget = DxvkMoreSettingsWidget(self.dxvk_settings, self.core)
        self.more_settings_widget.show_dxvk.connect(lambda x: self.show_dxvk.setChecked(x))
        action.setDefaultWidget(self.more_settings_widget)
        self.more_settings.menu().addAction(action)

        self.show_dxvk.stateChanged.connect(self.update_dxvk_active)
        self.show_dxvk.setChecked(not dxvk_hud == "")
        self.child_layout.addWidget(self.show_dxvk)

        self.child_layout.addWidget(self.more_settings)
        self.layout.addLayout(self.child_layout)

        self.setLayout(self.layout)

    def update_settings(self, app_name):
        self.name = app_name
        dxvk_hud = self.core.lgd.config.get(f"{self.name}.env", "DXVK_HUD", fallback="")
        if dxvk_hud:
            self.more_settings.setDisabled(False)
            for s in dxvk_hud.split(","):
                self.dxvk_settings[s][0] = True
        else:
            self.show_dxvk.setChecked(False)
            self.more_settings.setDisabled(True)

    def update_dxvk_active(self):
        if self.show_dxvk.isChecked():
            if not f"{self.name}.env" in self.core.lgd.config.sections():
                print("add section dxvk")
                self.core.lgd.config.add_section(f"{self.name}.env")
            self.more_settings.setDisabled(False)

            for i in self.more_settings_widget.settings:
                if i in ["fps", "gpuload"]:
                    self.more_settings_widget.settings[i][0] = True

            self.core.lgd.config[f"{self.name}.env"]["DXVK_HUD"] = "fps,gpuload"
            for w in self.more_settings_widget.widgets:
                if w.tag == "fps" or w.tag == "gpuload":
                    w.setChecked(True)

                else:
                    w.setChecked(False)
        else:
            self.more_settings.setDisabled(True)
            if not self.core.lgd.config.get(f"{self.name}.env", "DXVK_HUD", fallback="") == "":
                self.core.lgd.config.remove_option(f"{self.name}.env", "DXVK_HUD")
                if not self.core.lgd.config[f"{self.name}.env"]:
                    self.core.lgd.config.remove_section(f"{self.name}.env")
        self.core.lgd.save_config()


class DxvkMoreSettingsWidget(QWidget):
    show_dxvk = pyqtSignal(bool)

    def __init__(self, settings: dict, core: LegendaryCore):
        super(DxvkMoreSettingsWidget, self).__init__()
        self.layout = QVBoxLayout()
        self.name = "default"
        self.widgets = []
        self.core = core
        self.settings = settings
        for i in settings:
            widget = CheckBox(i, settings[i])
            widget.signal.connect(self.change)
            self.layout.addWidget(widget)
            self.widgets.append(widget)

        self.setLayout(self.layout)

    def change(self, signal: list):
        tag, checked = signal
        self.settings[tag][0] = checked

        sett = []
        logger.debug(self.settings)
        for i in self.settings:
            check, _ = self.settings[i]
            if check:
                sett.append(i)
        if len(sett) > 0:
            self.core.lgd.config.set(f"{self.name}.env", "DXVK_HUD", ",".join(sett))

        else:
            self.core.lgd.config.remove_option(f"{self.name}.env", "DXVK_HUD")
            self.show_dxvk.emit(False)
            if not self.core.lgd.config.options(f"{self.name}.env"):
                self.core.lgd.config.remove_section(f"{self.name}.env")
        self.core.lgd.save_config()


class CheckBox(QCheckBox):
    signal = pyqtSignal(tuple)

    def __init__(self, tag, settings):
        checked, text = settings
        super(CheckBox, self).__init__(text)
        self.setChecked(checked)
        self.tag = tag
        self.clicked.connect(lambda: self.signal.emit((self.tag, self.isChecked())))
