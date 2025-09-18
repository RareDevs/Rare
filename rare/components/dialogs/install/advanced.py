from PySide6.QtWidgets import QWidget

from rare.ui.components.dialogs.install.advanced import Ui_InstallDialogAdvanced
from rare.widgets.collapsible_widget import CollapsibleFrame


class InstallDialogAdvanced(CollapsibleFrame):
    def __init__(self, parent=None):
        super(InstallDialogAdvanced, self).__init__(parent=parent)

        title = self.tr("Advanced options")
        self.setTitle(title)

        self.widget = QWidget(parent=self)
        self.ui = Ui_InstallDialogAdvanced()
        self.ui.setupUi(self.widget)
        self.setWidget(self.widget)
        self.ui.exclude_prefix_label.setVisible(False)
        self.ui.exclude_prefix_info.setVisible(False)
        self.ui.exclude_prefix_button.setVisible(False)


__all__ = ["InstallDialogAdvanced"]
