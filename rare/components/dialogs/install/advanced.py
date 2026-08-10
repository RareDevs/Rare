from PySide6.QtWidgets import QWidget

from rare.ui.components.dialogs.install.advanced import Ui_InstallDialogAdvanced
from rare.widgets.collapsible_widget import CollapsibleFrame


class InstallDialogAdvanced(CollapsibleFrame):
    def __init__(self, parent=None):
        super(InstallDialogAdvanced, self).__init__(parent=parent)

        title = self.tr('Advanced options')
        self.setTitle(title)

        self.widget = QWidget(parent=self)
        self.ui = Ui_InstallDialogAdvanced()
        self.ui.setupUi(self.widget)

        self.ui.max_workers_info.setObjectName('InfoLabel')
        self.ui.max_memory_info.setObjectName('InfoLabel')
        self.ui.install_prereqs_check.setObjectName('InfoLabel')
        self.ui.read_files_check.setObjectName('InfoLabel')
        self.ui.dl_optimizations_check.setObjectName('InfoLabel')
        self.ui.force_download_check.setObjectName('InfoLabel')
        self.ui.ignore_space_check.setObjectName('InfoLabel')
        self.ui.download_only_check.setObjectName('InfoLabel')

        self.setWidget(self.widget)


__all__ = ['InstallDialogAdvanced']
