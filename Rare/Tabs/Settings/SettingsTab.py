from logging import getLogger

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QPushButton, QScrollArea, QWidget
from legendary.core import LegendaryCore

from Rare.Tabs.Settings.RareSettingsForm import RareSettingsForm
from Rare.ext.SettingsForm import SettingsForm
from Rare.utils.constants import default_settings, legendary_settings
from Rare.utils.legendaryUtils import get_name

logger = getLogger("Settings")


class SettingsTab(QScrollArea):
    def __init__(self, core: LegendaryCore):
        super(SettingsTab, self).__init__()
        self.core = core
        self.widget = QWidget()
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # Settings
        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel("<h1>Rare Settings</h1>"))
        self.logged_in_as = QLabel(f"Logged in as {get_name()}")
        # self.legendary_form =SettingsForm()

        self.default_settings = SettingsForm("default", default_settings, True)
        self.legendary_form = SettingsForm("Legendary", legendary_settings, False)

        self.rare_form = RareSettingsForm()

        self.logout_button = QPushButton("Logout")
        self.logout_button.clicked.connect(self.logout)
        self.layout.addWidget(self.logged_in_as)

        self.layout.addWidget(self.rare_form)
        self.layout.addWidget(self.default_settings)
        self.layout.addWidget(self.legendary_form)

        self.layout.addStretch(1)
        self.layout.addWidget(self.logout_button)

        self.info_label = QLabel("<h2>Credits</h2>")
        self.infotext = QLabel("Developers : Dummerle, CommandMC\nLegendary Dev: Rodney\nLicense: GPL v.3")

        self.layout.addWidget(self.info_label)
        self.layout.addWidget(self.infotext)

        self.widget.setLayout(self.layout)
        self.widget.setFixedWidth(self.width())
        self.setWidget(self.widget)

    def logout(self):
        self.core.lgd.invalidate_userdata()
        exit(0)
