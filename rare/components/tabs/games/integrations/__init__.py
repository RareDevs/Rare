from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QLabel, QSpacerItem, QSizePolicy

from rare.widgets.side_tab import SideTabWidget
from .egl_sync_group import EGLSyncGroup
from .eos_group import EOSGroup
from .import_group import ImportGroup
from .ubisoft_group import UbisoftGroup


class IntegrationsTabs(SideTabWidget):
    def __init__(self, parent=None):
        super(IntegrationsTabs, self).__init__(show_back=True, parent=parent)
        self.import_widget = IntegrationsWidget(
            ImportGroup(self),
            self.tr("To import games from Epic Games Store, please enable EGL Sync."),
            self,
        )
        self.import_index = self.addTab(self.import_widget, self.tr("Import Games"))

        self.egl_sync_widget = IntegrationsWidget(
            EGLSyncGroup(self),
            self.tr("To import EGL games from directories, please use Import Game."),
            self,
        )
        self.egl_sync_index = self.addTab(self.egl_sync_widget, self.tr("Sync with EGL"))

        self.eos_ubisoft = IntegrationsWidget(
            None,
            self.tr(""),
            self,
        )
        self.eos_ubisoft.addWidget(UbisoftGroup(self.eos_ubisoft))
        self.eos_ubisoft.addWidget(EOSGroup(self.eos_ubisoft))
        self.eos_ubisoft_index = self.addTab(self.eos_ubisoft, self.tr("Epic Overlay and Ubisoft"))

        self.setCurrentIndex(self.import_index)

    def show_import(self):
        self.setCurrentIndex(self.import_index)

    def show_egl_sync(self):
        self.setCurrentIndex(self.egl_sync_index)

    def show_eos_ubisoft(self):
        self.setCurrentIndex(self.eos_ubisoft_index)


class IntegrationsWidget(QWidget):
    def __init__(self, widget: Optional[QWidget], info: str, parent=None):
        super(IntegrationsWidget, self).__init__(parent=parent)
        self.info = QLabel(f"<b>{info}</b>")

        layout = QVBoxLayout(self)
        if widget is not None:
            layout.addWidget(widget)
        layout.addWidget(self.info)
        layout.addItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

    def addWidget(self, widget: QWidget, stretch: int = 0, alignment: Qt.AlignmentFlag = Qt.Alignment()):
        self.layout().insertWidget(self.layout().count() - 2, widget, stretch, alignment)
