import os

from PyQt5.QtCore import pyqtSignal, QSettings
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QGroupBox, QHBoxLayout, QVBoxLayout, QScrollArea, QLabel, QPushButton, QMessageBox

from custom_legendary.core import LegendaryCore
from custom_legendary.models.game import Game
from rare.components.dialogs.install_dialog import InstallDialog
from rare.utils.models import InstallOptions
from rare.utils.utils import download_image


class DlcTab(QScrollArea):
    install_dlc = pyqtSignal(InstallOptions)
    game: Game

    def __init__(self, core: LegendaryCore, parent):
        super(DlcTab, self).__init__(parent=parent)
        self.core = core
        self.widget = QGroupBox("DLCs")
        self.widget.setObjectName("group")
        self.setWidgetResizable(True)
        self.layout = QVBoxLayout()
        self.installed_dlcs = [i.app_name for i in self.core.get_installed_dlc_list()]

        self.installed_dlc_widget = QGroupBox(self.tr("Installed DLCs"))
        self.installed_layout = QVBoxLayout()
        self.available_dlcs = QGroupBox(self.tr("Available DLCs"))
        self.available_dlcs_layout = QVBoxLayout()

        self.installed = []
        self.available = []

    def update_dlcs(self, app_name, dlcs: list):
        self.installed_dlcs = [i.app_name for i in self.core.get_installed_dlc_list()]
        self.installed_dlc_widget = QGroupBox(self.tr("Installed DLCs"))
        self.installed_layout = QVBoxLayout()
        self.available_dlcs = QGroupBox(self.tr("Available DLCs"))
        self.available_dlcs_layout = QVBoxLayout()
        self.installed = []
        self.available = []
        QVBoxLayout().addWidget(self.widget)

        self.game = self.core.get_game(app_name)

        for dlc in sorted(dlcs[self.game.asset_info.catalog_item_id], key=lambda x: x.app_title):
            if dlc.app_name in self.installed_dlcs:
                w = DLCWidget(dlc, True)
                self.installed_layout.addWidget(w)
                self.installed.append(dlc)
            else:
                w = DLCWidget(dlc, False)
                w.install.connect(self.install)
                self.available_dlcs_layout.addWidget(w)
                self.available.append(dlc)
        if len(self.installed) == 0:
            self.installed_layout.addWidget(QLabel(self.tr("No DLCs are installed")))
        if len(self.available) == 0:
            self.available_dlcs_layout.addWidget(QLabel(self.tr("No DLCs are available")))

        self.widget = QGroupBox("DLCs")
        self.layout = QVBoxLayout()
        self.installed_dlc_widget.setLayout(self.installed_layout)
        self.available_dlcs.setLayout(self.available_dlcs_layout)
        self.layout.addWidget(self.installed_dlc_widget)
        self.layout.addWidget(self.available_dlcs)
        self.layout.addStretch(1)
        self.widget.setLayout(self.layout)
        self.setWidget(self.widget)

    def install(self, app_name):
        if not self.core.is_installed(self.game.app_name):
            QMessageBox.warning(self, "Error", self.tr("Base Game is not installed. Please install {} first").format(
                self.game.app_title))
            return
        infos = InstallDialog(self.game.app_name, self.core, True).get_information()
        if infos != 0:
            path, max_workers, force, ignore_free_space = infos
            self.install_dlc.emit(
                InstallOptions(app_name=app_name, max_workers=max_workers, path=path, force=force,
                               ignore_free_space=ignore_free_space))


class DLCWidget(QGroupBox):
    install = pyqtSignal(str)  # Appname

    def __init__(self, dlc: Game, installed: bool):
        super(DLCWidget, self).__init__()
        self.main_layout = QHBoxLayout()
        self.dlc = dlc
        IMAGE_DIR = QSettings().value("img_dir", os.path.expanduser("~/.cache/rare/images"))
        if installed:

            if os.path.exists(os.path.join(IMAGE_DIR, dlc.app_name, "FinalArt.png")):
                pixmap = QPixmap(os.path.join(IMAGE_DIR, dlc.app_name, "FinalArt.png"))
            elif os.path.exists(os.path.join(IMAGE_DIR, dlc.app_name, "DieselGameBoxTall.png")):
                pixmap = QPixmap(os.path.join(IMAGE_DIR, dlc.app_name, "DieselGameBoxTall.png"))
            elif os.path.exists(os.path.join(IMAGE_DIR, dlc.app_name, "DieselGameBoxLogo.png")):
                pixmap = QPixmap(os.path.join(IMAGE_DIR, dlc.app_name, "DieselGameBoxLogo.png"))
            else:
                print(f"No Image found: {dlc.app_title}")
                pixmap = None
            if not pixmap or pixmap.isNull():
                print(dlc.app_title + " has corrupt Image")
                download_image(dlc, force=True)
                pixmap = QPixmap(f"{IMAGE_DIR}/{dlc.app_name}/UninstalledArt.png")
        else:
            if os.path.exists(f"{IMAGE_DIR}/{dlc.app_name}/UninstalledArt.png"):
                pixmap = QPixmap(f"{IMAGE_DIR}/{dlc.app_name}/DieselGameBoxTall.png")

            else:
                pixmap = None

            if not pixmap or pixmap.isNull():
                print(dlc.app_title + " has corrupt Image")
                download_image(dlc, force=True)
                pixmap = QPixmap(f"{IMAGE_DIR}/{dlc.app_name}/UninstalledArt.png")

        image = QLabel()
        image.setPixmap(pixmap)
        self.main_layout.addWidget(image)

        self.layout = QVBoxLayout()

        self.layout.addWidget(QLabel(dlc.app_title))
        self.layout.addWidget(QLabel("Version: " + str(dlc.app_version)))

        self.layout.addWidget(QLabel("App Name: " + dlc.app_name))
        if not installed:
            self.install_button = QPushButton(self.tr("Install"))
            self.layout.addWidget(self.install_button)

            self.install_button.clicked.connect(lambda: self.install.emit(dlc.app_name))
        else:
            self.layout.addWidget(QLabel(self.tr("Installed. Uninstalling DLCs is not supported")))

        self.main_layout.addLayout(self.layout)

        self.setLayout(self.main_layout)

        self.layout.addStretch(1)

    def install_game(self):
        self.install_button.setDisabled(True)
        self.install_button.setText(self.tr("Installing"))
        self.install.emit(self.dlc.app_name)
