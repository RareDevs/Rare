from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

from rare.shared import RareCore
from rare.widgets.side_tab import SideTabWidget

from .egl_sync_group import EGLSyncGroup
from .eos_group import EosGroup
from .import_group import ImportGroup
from .ubisoft_group import UbisoftGroup


class IntegrationsTab(SideTabWidget):
    def __init__(self, rcore: RareCore, parent=None):
        super(IntegrationsTab, self).__init__(show_back=False, parent=parent)
        self.import_group = ImportGroup(rcore, self)
        self.import_widget = IntegrationsWidget(
            self.import_group,
            self.tr("To import games from Epic Games Store, please enable EGL Sync."),
            self,
        )
        self.import_index = self.addTab(self.import_widget, self.tr("Import Games"))

        self.egl_sync_group = EGLSyncGroup(rcore, self)
        self.egl_sync_widget = IntegrationsWidget(
            self.egl_sync_group,
            self.tr("To import EGL games from directories, please use Import Game."),
            self,
        )
        self.egl_sync_index = self.addTab(self.egl_sync_widget, self.tr("Sync with EGL"))

        self.eos_group = EosGroup(rcore, self)
        self.eos_widget = IntegrationsWidget(
            self.eos_group,
            self.tr(""),
            self,
        )
        self.eos_index = self.addTab(self.eos_widget, self.tr("Epic Overlay"))

        self.ubisoft_group = UbisoftGroup(rcore, self)
        self.ubisoft_widget = IntegrationsWidget(
            self.ubisoft_group,
            self.tr(""),
            self,
        )
        self.ubisoft_index = self.addTab(self.ubisoft_widget, self.tr("Ubisoft Link"))

        self.setCurrentIndex(self.import_index)

    def show_import(self, app_name: str = None):
        self.setCurrentIndex(self.import_index)
        self.import_group.set_game(app_name)

    def show_egl_sync(self):
        self.setCurrentIndex(self.egl_sync_index)

    def show_eos(self):
        self.setCurrentIndex(self.eos_index)

    def show_ubisoft(self):
        self.setCurrentIndex(self.ubisoft_index)


class IntegrationsWidget(QWidget):
    def __init__(self, widget: Optional[QWidget], info: str, parent=None):
        super(IntegrationsWidget, self).__init__(parent=parent)
        self.info = QLabel(f"<b>{info}</b>")

        self.__layout = QVBoxLayout(self)
        if widget is not None:
            self.__layout.addWidget(widget)
        self.__layout.addWidget(self.info)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def addWidget(self, widget: QWidget, stretch: int = 0, alignment: Qt.AlignmentFlag = None):
        alignment = alignment if alignment is not None else Qt.AlignmentFlag(0)
        self.__layout.insertWidget(self.layout().count() - 1, widget, stretch, alignment)
