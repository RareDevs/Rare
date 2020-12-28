from logging import getLogger

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QPushButton, QScrollArea

from Rare.Tabs.Settings.Rare import RareSettingsForm
from Rare.Tabs.Settings.LegendarySettingsForm import SettingsForm
from Rare.utils.legendaryUtils import get_name
from legendary.core import LegendaryCore

logger = getLogger("Settings")


class SettingsTab(QScrollArea):
    def __init__(self, parent, core: LegendaryCore):
        super(SettingsTab, self).__init__(parent=parent)
        self.core = core
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # Settings
        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel("<h1>Rare Settings</h1>"))
        self.logged_in_as = QLabel(f"Logged in as {get_name()}")
        self.legendary_form =SettingsForm()
        self.rare_form = RareSettingsForm()

        self.logout_button = QPushButton("Logout")
        self.logout_button.clicked.connect(self.logout)
        self.layout.addWidget(self.logged_in_as)

        self.layout.addWidget(self.rare_form)
        self.layout.addWidget(self.legendary_form)
        self.layout.addStretch(1)
        self.layout.addWidget(self.logout_button)

        self.info_label = QLabel("<h2>Credits</h2>")
        self.infotext = QLabel("Developers : Dummerle, CommandMC\nLegendary Dev: Rodney\nLicense: GPL v.3")

        self.layout.addWidget(self.info_label)
        self.layout.addWidget(self.infotext)

        self.setLayout(self.layout)

    def logout(self):
        self.core.lgd.invalidate_userdata()
        exit(0)
