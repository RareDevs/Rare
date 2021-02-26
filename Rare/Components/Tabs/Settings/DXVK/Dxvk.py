from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QCheckBox, QVBoxLayout, QWidgetAction, QMenu, QToolButton, QHBoxLayout, QLabel
from legendary.core import LegendaryCore


class DxvkWidget(QWidget):
    dxvk_settings = {"fps": (False, "Fps"),
                     "gpuload": (False, "GPU usage"),
                     "memory": (False, "Used Memory"),
                     "devinfo": (False, "Device info"),
                     "version": (False, "DXVK version"),
                     "api": (False, "D3D Level of application")
                     }

    def __init__(self, core: LegendaryCore):
        super(DxvkWidget, self).__init__()
        self.core = core
        self.layout = QVBoxLayout()
        self.child_layout = QHBoxLayout()
        self.title = QLabel("dxvk settings")
        self.show_dxvk = QCheckBox("Show Dxvk HUD")

        self.more_settings = QToolButton()
        dxvk_hud = self.core.lgd.config.get("default.env", "DXVK_HUD", fallback="")
        self.more_settings.setDisabled(not dxvk_hud == "")
        if dxvk_hud:
            for s in dxvk_hud.split(","):
                y = list(self.dxvk_settings[s])
                y[0] = True
                self.dxvk_settings[s] = tuple(y)

        self.more_settings.setPopupMode(QToolButton.InstantPopup)
        self.more_settings.setMenu(QMenu())
        self.more_settings.setText("More DXVK settings")
        action = QWidgetAction(self)
        self.more_settings_widget = DxvkMoreSettingsWidget(self.dxvk_settings, self.core)
        action.setDefaultWidget(self.more_settings_widget)
        self.more_settings.menu().addAction(action)

        self.show_dxvk.stateChanged.connect(lambda x: self.more_settings.setDisabled(x == 0))
        self.show_dxvk.setChecked(not dxvk_hud == "")
        self.layout.addWidget(self.title)
        self.child_layout.addWidget(self.show_dxvk)

        self.child_layout.addWidget(self.more_settings)
        self.layout.addLayout(self.child_layout)

        self.setLayout(self.layout)

    def update_dettings(self):
        pass


class DxvkMoreSettingsWidget(QWidget):
    def __init__(self, settings: dict, core: LegendaryCore):
        super(DxvkMoreSettingsWidget, self).__init__()
        self.layout = QVBoxLayout()
        self.widgets = []
        self.core = core
        self.settings = settings
        for i in settings:
            widget = CheckBox(i, settings[i])
            widget.signal.connect(self.change)
            self.layout.addWidget(widget)
            self.widgets.append(widget)

        self.setLayout(self.layout)

    def change(self, signal: tuple):
        tag, checked = signal
        y = list(self.settings[tag])
        y[0] = checked
        self.settings[tag] = tuple(y)
        # print(self.settings)
        sett = []
        for i in self.settings:
            check, _ = self.settings[i]
            if check:
                sett.append(i)
        if sett:
            self.core.lgd.config["default.env"]["DXVK_HUD"] = ",".join(sett)
            self.core.lgd.save_config()


class CheckBox(QCheckBox):
    signal = pyqtSignal(tuple)

    def __init__(self, tag, settings):
        checked, text = settings
        super(CheckBox, self).__init__(text)
        self.setChecked(checked)
        self.tag = tag
        self.clicked.connect(lambda: self.signal.emit((self.tag, self.isChecked())))

    def update_settings(self):
        pass
