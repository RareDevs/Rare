from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
from qtawesome import icon


class TrayIcon(QSystemTrayIcon):
    def __init__(self, parent):
        super(TrayIcon, self).__init__(parent)
        self.setIcon(icon("ei.cogs", color="white"))  # TODO change icon to logo
        self.setVisible(True)
        self.setToolTip("Rare")

        self.menu = QMenu()

        self.start_rare = QAction("Rare")
        self.menu.addAction(self.start_rare)

        self.exit_action = QAction(self.tr("Exit"))
        self.menu.addSeparator()
        self.menu.addAction(self.exit_action)

        self.setContextMenu(self.menu)
