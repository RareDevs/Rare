from typing import Optional, List

from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QFrame, QMessageBox, QToolBox

from rare.models.game import RareGame
from rare.shared import LegendaryCoreSingleton, GlobalSignalsSingleton
from rare.ui.components.tabs.games.game_info.game_dlc import Ui_GameDlc
from rare.ui.components.tabs.games.game_info.game_dlc_widget import Ui_GameDlcWidget
from rare.widgets.image_widget import ImageWidget, ImageSize
from rare.widgets.side_tab import SideTabContents
from rare.utils.misc import widget_object_name


class GameDlcWidget(QFrame):
    def __init__(self, rgame: RareGame, rdlc: RareGame, parent=None):
        super(GameDlcWidget, self).__init__(parent=parent)
        self.ui = Ui_GameDlcWidget()
        self.ui.setupUi(self)
        self.setObjectName(widget_object_name(self, rdlc.app_name))
        self.rgame = rgame
        self.rdlc = rdlc

        self.image = ImageWidget(self)
        self.image.setFixedSize(ImageSize.Icon)
        self.ui.dlc_layout.insertWidget(0, self.image)

        self.ui.dlc_name.setText(rdlc.app_title)
        self.ui.version.setText(rdlc.version)
        self.ui.app_name.setText(rdlc.app_name)

        self.image.setPixmap(rdlc.pixmap)


class InstalledGameDlcWidget(GameDlcWidget):
    uninstalled = pyqtSignal(RareGame)

    def __init__(self, rgame: RareGame, rdlc: RareGame, parent=None):
        super(InstalledGameDlcWidget, self).__init__(rgame=rgame, rdlc=rdlc, parent=parent)
        # lk: set object names for CSS properties
        self.ui.action_button.setObjectName("UninstallButton")
        self.ui.action_button.clicked.connect(self.uninstall_dlc)
        self.ui.action_button.setText(self.tr("Uninstall DLC"))
        # lk: don't reference `self.rdlc` here because the object has been deleted
        rdlc.signals.game.uninstalled.connect(lambda: self.uninstalled.emit(rdlc))

    def uninstall_dlc(self):
        self.rdlc.uninstall()


class AvailableGameDlcWidget(GameDlcWidget):
    installed = pyqtSignal(RareGame)

    def __init__(self, rgame: RareGame, rdlc: RareGame, parent=None):
        super(AvailableGameDlcWidget, self).__init__(rgame=rgame, rdlc=rdlc, parent=parent)
        # lk: set object names for CSS properties
        self.ui.action_button.setObjectName("InstallButton")
        self.ui.action_button.clicked.connect(self.install_dlc)
        self.ui.action_button.setText(self.tr("Install DLC"))
        # lk: don't reference `self.rdlc` here because the object has been deleted
        rdlc.signals.game.installed.connect(lambda: self.installed.emit(rdlc))

    def install_dlc(self):
        if not self.rgame.is_installed:
            QMessageBox.warning(
                self,
                self.tr("Error"),
                self.tr("Base Game is not installed. Please install {} first").format(self.rgame.app_title),
            )
            return
        self.rdlc.install()


class GameDlc(QToolBox, SideTabContents):

    def __init__(self, parent=None):
        super(GameDlc, self).__init__(parent=parent)
        self.implements_scrollarea = True
        self.ui = Ui_GameDlc()
        self.ui.setupUi(self)
        self.core = LegendaryCoreSingleton()
        self.signals = GlobalSignalsSingleton()

        self.rgame: Optional[RareGame] = None

    def list_installed(self) -> List[InstalledGameDlcWidget]:
        return self.ui.installed_dlc_container.findChildren(InstalledGameDlcWidget, options=Qt.FindDirectChildrenOnly)

    def list_available(self) -> List[AvailableGameDlcWidget]:
        return self.ui.available_dlc_container.findChildren(AvailableGameDlcWidget, options=Qt.FindDirectChildrenOnly)

    def get_installed(self, app_name: str) -> Optional[InstalledGameDlcWidget]:
        return self.ui.installed_dlc_container.findChild(
            InstalledGameDlcWidget,
            name=widget_object_name(InstalledGameDlcWidget, app_name),
            options=Qt.FindDirectChildrenOnly
        )

    def get_available(self, app_name: str) -> Optional[AvailableGameDlcWidget]:
        return self.ui.available_dlc_container.findChild(
            AvailableGameDlcWidget,
            name=widget_object_name(AvailableGameDlcWidget, app_name),
            options=Qt.FindDirectChildrenOnly
        )

    def update_installed_page(self):
        have_installed = bool(self.list_installed())
        self.ui.installed_dlc_label.setVisible(not have_installed)
        self.ui.installed_dlc_container.setVisible(have_installed)
        if not have_installed:
            self.setCurrentWidget(self.ui.available_dlc_page)

    def update_available_page(self):
        have_available = bool(self.list_available())
        self.ui.available_dlc_label.setVisible(not have_available)
        self.ui.available_dlc_container.setVisible(have_available)
        if not have_available:
            self.setCurrentWidget(self.ui.installed_dlc_page)

    def append_installed(self, rdlc: RareGame):
        self.ui.installed_dlc_label.setVisible(False)
        self.ui.installed_dlc_container.setVisible(True)
        a_widget: AvailableGameDlcWidget = self.get_available(rdlc.app_name)
        if a_widget is not None:
            self.ui.available_dlc_container.layout().removeWidget(a_widget)
            a_widget.deleteLater()
        i_widget: InstalledGameDlcWidget = InstalledGameDlcWidget(
            self.rgame, rdlc, self.ui.installed_dlc_container
        )
        i_widget.destroyed.connect(self.update_installed_page)
        i_widget.uninstalled.connect(self.append_available)
        self.ui.installed_dlc_container.layout().addWidget(i_widget)

    def append_available(self, rdlc: RareGame):
        self.ui.available_dlc_label.setVisible(False)
        self.ui.available_dlc_container.setVisible(True)
        i_widget: InstalledGameDlcWidget = self.get_installed(rdlc.app_name)
        if i_widget is not None:
            self.ui.available_dlc_container.layout().removeWidget(i_widget)
            i_widget.deleteLater()
        a_widget: AvailableGameDlcWidget = AvailableGameDlcWidget(
            self.rgame, rdlc, self.ui.available_dlc_container
        )
        a_widget.destroyed.connect(self.update_available_page)
        a_widget.installed.connect(self.append_installed)
        self.ui.available_dlc_container.layout().addWidget(a_widget)

    def update_dlcs(self, rgame: RareGame):
        self.rgame = rgame
        self.set_title.emit(self.rgame.app_title)

        for i_widget in self.list_installed():
            self.ui.installed_dlc_container.layout().removeWidget(i_widget)
            i_widget.deleteLater()

        for a_widget in self.list_available():
            self.ui.available_dlc_container.layout().removeWidget(a_widget)
            a_widget.deleteLater()

        for dlc in sorted(self.rgame.owned_dlcs, key=lambda x: x.app_title):
            if dlc.is_installed:
                self.append_installed(rdlc=dlc)
            else:
                self.append_available(rdlc=dlc)

        if not self.list_available():
            self.setCurrentWidget(self.ui.installed_dlc_page)
        if not self.list_installed():
            self.setCurrentWidget(self.ui.available_dlc_page)
