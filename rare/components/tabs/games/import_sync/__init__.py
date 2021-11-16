from PyQt5.QtWidgets import QVBoxLayout, QWidget, QLabel, QSpacerItem, QSizePolicy

from rare.utils.extra_widgets import SideTabWidget
from .egl_sync_group import EGLSyncGroup
from .import_group import ImportGroup


class ImportSyncTabs(SideTabWidget):

    def __init__(self, parent=None):
        super(ImportSyncTabs, self).__init__(show_back=True, parent=parent)
        self.import_widget = ImportSyncWidget(
            ImportGroup(self),
            self.tr('Import Game'),
            self.tr('To import games from Epic Games Store, please enable EGL Sync.'),
            self
        )
        self.addTab(self.import_widget, self.tr("Import Games"))

        self.egl_sync_widget = ImportSyncWidget(
            EGLSyncGroup(self),
            self.tr('Sync with EGL'),
            self.tr('To import EGL games from directories, please use Import Game.'),
            self
        )
        self.addTab(self.egl_sync_widget, self.tr("Sync with EGL"))
        # FIXME: Until it is ready
        # self.setTabEnabled(2, False)

        self.tabBar().setCurrentIndex(1)

    def show_import(self):
        self.setCurrentIndex(1)

    def show_egl_sync(self):
        self.setCurrentIndex(2)


class ImportSyncWidget(QWidget):

    def __init__(self, widget: QWidget, title: str, info: str, parent=None):
        super(ImportSyncWidget, self).__init__(parent=parent)
        self.layout = QVBoxLayout()
        self.title = QLabel(f"<h2>{title}</h2")
        self.layout.addWidget(self.title)
        self.title.setVisible(False)
        self.group = widget
        self.layout.addWidget(self.group)
        self.info = QLabel(f"<h4>{info}</h4>")
        self.layout.addWidget(self.info)
        self.layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.setLayout(self.layout)
