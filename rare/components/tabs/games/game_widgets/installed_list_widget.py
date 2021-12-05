from logging import getLogger

from PyQt5.QtCore import QProcess, pyqtSignal, Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout
from qtawesome import icon

from rare.components.tabs.games.game_widgets.base_installed_widget import BaseInstalledWidget
from rare.utils.utils import get_size

logger = getLogger("GameWidget")


class InstalledListWidget(BaseInstalledWidget):
    proc: QProcess
    signal = pyqtSignal(str)
    update_game = pyqtSignal()

    def __init__(self, app_name, pixmap, game_utils):
        super(InstalledListWidget, self).__init__(app_name, pixmap, game_utils)
        self.dev = self.game.metadata["developer"]
        if self.game.third_party_store != "Origin":
            self.size = self.igame.install_size
        else:
            self.size = 0

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.image)

        ##Layout on the right
        self.childLayout = QVBoxLayout()
        self.layout.addLayout(self.childLayout)

        play_icon = icon("ei.play")
        self.title_label = QLabel(f"<h1>{self.game.app_title}</h1>")
        self.title_label.setWordWrap(True)
        self.childLayout.addWidget(self.title_label)
        self.app_name_label = QLabel(self.game.app_name)
        self.launch_button = QPushButton(play_icon, self.tr("Launch") if not self.is_origin else self.tr("Link/Play"))
        self.launch_button.setObjectName("launch_game_button")
        self.launch_button.setFixedWidth(150)

        self.info = QPushButton("Info")
        self.info.clicked.connect(lambda: self.show_info.emit(self.game.app_name))
        self.info.setFixedWidth(80)

        self.info_label = QLabel("")
        self.childLayout.addWidget(self.info_label)
        self.update_text()

        self.launch_button.clicked.connect(self.launch)

        self.childLayout.addWidget(self.launch_button)
        self.childLayout.addWidget(self.info)
        self.childLayout.addWidget(self.app_name_label)
        self.developer_label = QLabel(self.tr("Developer: ") + self.dev)
        self.childLayout.addWidget(self.developer_label)
        if not self.is_origin:
            self.version_label = QLabel("Version: " + str(self.igame.version))
            self.size_label = QLabel(f"{self.tr('Installed size')}: {get_size(self.size)}")

            self.childLayout.addWidget(self.version_label)
            self.childLayout.addWidget(self.size_label)

        self.childLayout.setAlignment(Qt.AlignTop)
        self.layout.setAlignment(Qt.AlignLeft)

        self.game_utils.cloud_save_finished.connect(self.sync_finished)
        self.game_utils.finished.connect(self.game_finished)

        self.leaveEvent = self.update_text
        self.enterEvent = self.update_text

        self.game_utils.game_launched.connect(self.game_started)

    def update_text(self, e=None):
        if self.update_available:
            self.info_label.setText(self.texts["default"]["update_available"])
        elif self.igame and self.igame.needs_verification:
            self.info_label.setText(self.texts["needs_verification"])
        elif self.syncing_cloud_saves:
            self.info_label.setText(self.texts["default"]["syncing"])
        else:
            self.info_label.setText("")

    def game_started(self, app_name):
        if app_name == self.game.app_name:
            self.game_running = True
            self.update_text()
            self.launch_button.setDisabled(True)

    def game_finished(self, app_name, error):
        if app_name != self.game.app_name:
            return
        super().game_finished(app_name, error)
        self.update_text(None)
        self.launch_button.setDisabled(False)
