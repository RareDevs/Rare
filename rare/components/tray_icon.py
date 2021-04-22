from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction

from rare import style_path


class TrayIcon(QSystemTrayIcon):
    def __init__(self, parent):
        super(TrayIcon, self).__init__(parent)
        self.setIcon(QIcon(style_path + "Logo.png"))
        self.setVisible(True)
        self.setToolTip("Rare")

        self.menu = QMenu()

        self.start_rare = QAction("Rare")
        self.menu.addAction(self.start_rare)

        self.exit_action = QAction(self.tr("Exit"))
        self.menu.addSeparator()
        self.menu.addAction(self.exit_action)

        self.setContextMenu(self.menu)
