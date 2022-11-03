from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QLabel, QSpacerItem, QSizePolicy

from rare.utils.extra_widgets import SideTabWidget
from .egl_sync_group import EGLSyncGroup
from .import_group import ImportGroup
from .eos_group import EOSGroup
from .ubisoft_group import UbisoftGroup


class ImportSyncTabs(SideTabWidget):
    def __init__(self, parent=None):
        super(ImportSyncTabs, self).__init__(show_back=True, parent=parent)
        self.import_widget = ImportSyncWidget(
            ImportGroup(self),
            self.tr("To import games from Epic Games Store, please enable EGL Sync."),
            self,
        )
        self.addTab(self.import_widget, self.tr("Import Games"))

        self.egl_sync_widget = ImportSyncWidget(
            EGLSyncGroup(self),
            self.tr("To import EGL games from directories, please use Import Game."),
            self,
        )
        self.addTab(self.egl_sync_widget, self.tr("Sync with EGL"))

        self.egl_eos_ubisoft = ImportSyncWidget(
            None,
            self.tr(""),
            self,
        )
        self.egl_eos_ubisoft.addWidget(UbisoftGroup(self.egl_eos_ubisoft))
        self.egl_eos_ubisoft.addWidget(EOSGroup(self.egl_eos_ubisoft))
        self.addTab(self.egl_eos_ubisoft, self.tr("EOS and Ubisoft"))

        self.tabBar().setCurrentIndex(1)

    def show_import(self):
        self.setCurrentIndex(1)

    def show_egl_sync(self):
        self.setCurrentIndex(2)

    def show_eos_ubisoft(self):
        self.setCurrentIndex(3)


class ImportSyncWidget(QWidget):
    def __init__(self, widget: Optional[QWidget], info: str, parent=None):
        super(ImportSyncWidget, self).__init__(parent=parent)
        self.info = QLabel(f"<b>{info}</b>")

        layout = QVBoxLayout()
        if widget is not None:
            layout.addWidget(widget)
        layout.addWidget(self.info)
        layout.addItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )
        self.setLayout(layout)

    def addWidget(self, widget: QWidget, stretch: int = 0, alignment: Qt.AlignmentFlag = Qt.Alignment()):
        self.layout().insertWidget(self.layout().count() - 2, widget, stretch, alignment)
