import platform

from PyQt5.QtCore import Qt, QThreadPool
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QWidget, QTreeView
from legendary.models.game import Game

from rare.shared import (
    LegendaryCoreSingleton,
    GlobalSignalsSingleton,
    ArgumentsSingleton,
    ApiResultsSingleton,
)
from rare.shared.image_manager import ImageManagerSingleton, ImageSize
from rare.ui.components.tabs.games.game_info.game_info import Ui_GameInfo
from rare.utils.extra_widgets import SideTabWidget
from rare.utils.json_formatter import QJsonModel
from rare.utils.models import InstallOptionsModel
from rare.utils.steam_grades import SteamWorker


class UninstalledInfoTabs(SideTabWidget):
    def __init__(self, ue_default_name, parent=None):
        super(UninstalledInfoTabs, self).__init__(show_back=True, parent=parent)
        self.core = LegendaryCoreSingleton()
        self.signals = GlobalSignalsSingleton()
        self.args = ArgumentsSingleton()

        self.info = UninstalledInfo(ue_default_name)
        self.info.install_button.setDisabled(self.args.offline)
        self.addTab(self.info, self.tr("Information"))

        self.view = GameMetadataView()
        self.addTab(self.view, self.tr("Metadata"))

        # self.setTabEnabled(1, False)
        self.setCurrentIndex(1)

    def update_game(self, game: Game):
        self.setCurrentIndex(1)
        self.info.update_game(game)
        self.view.update_game(game)

    def keyPressEvent(self, e: QKeyEvent):
        if e.key() == Qt.Key_Escape:
            self.parent().setCurrentIndex(0)


class GameMetadataView(QTreeView):
    game: Game

    def __init__(self, parent=None):
        super(GameMetadataView, self).__init__(parent=parent)
        self.setColumnWidth(0, 300)
        self.setWordWrap(True)
        self.model = QJsonModel()
        self.setModel(self.model)

    def update_game(self, game: Game):
        self.game = game
        self.title.setTitle(self.game.app_title)
        self.model.clear()
        try:
            self.model.load(game.__dict__)
        except:
            pass
        self.resizeColumnToContents(0)


class UninstalledInfo(QWidget, Ui_GameInfo):
    game: Game

    def __init__(self, ue_default_name, parent=None):
        super(UninstalledInfo, self).__init__(parent=parent)
        self.setupUi(self)
        self.core = LegendaryCoreSingleton()
        self.signals = GlobalSignalsSingleton()
        self.api_results = ApiResultsSingleton()
        self.image_manager = ImageManagerSingleton()

        self.install_button.clicked.connect(self.install_game)
        if platform.system() != "Windows":
            self.steam_worker = SteamWorker(self.core)
            self.steam_worker.signals.rating_signal.connect(self.grade.setText)
            self.steam_worker.setAutoDelete(False)

        else:
            self.lbl_grade.setVisible(False)
            self.grade.setVisible(False)

        self.install_size.setEnabled(False)
        self.lbl_install_size.setEnabled(False)
        self.install_path.setEnabled(False)
        self.lbl_install_path.setEnabled(False)

        self.game_actions_stack.setCurrentIndex(1)
        self.game_actions_stack.resize(self.game_actions_stack.minimumSize())
        self.lbl_platform.setText(self.tr("Platforms"))
        self.ue_default_name = ue_default_name

    def install_game(self):
        self.signals.install_game.emit(InstallOptionsModel(app_name=self.game.app_name))

    def update_game(self, game: Game):
        self.game = game
        self.title.setTitle(self.game.app_title)
        available_platforms = ["Windows"]
        if self.game.app_name in self.api_results.bit32_games:
            available_platforms.append("32 Bit")
        if self.game.app_name in self.api_results.mac_games:
            available_platforms.append("macOS")
        self.platform.setText(", ".join(available_platforms))

        pixmap = self.image_manager.get_pixmap(game.app_name, color=False)
        if pixmap.isNull():
            pixmap = self.image_manager.get_pixmap(self.ue_default_name, color=False)
        pixmap = pixmap.scaled(ImageSize.Display.size)
        self.image.setPixmap(pixmap)

        self.app_name.setText(self.game.app_name)
        self.version.setText(self.game.app_version("Windows"))
        self.dev.setText(self.game.metadata["developer"])
        self.install_size.setText("N/A")
        self.install_path.setText("N/A")

        is_ue = self.core.get_asset(game.app_name).namespace == "ue"
        self.grade.setVisible(not is_ue)
        self.lbl_grade.setVisible(not is_ue)

        if platform.system() != "Windows" and not is_ue:
            self.grade.setText(self.tr("Loading"))
            self.steam_worker.set_app_name(game.app_name)
            QThreadPool.globalInstance().start(self.steam_worker)
