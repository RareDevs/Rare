from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QMainWindow, QMessageBox

from Rare.Components.TabWidget import TabWidget


class MainWindow(QMainWindow):
    def __init__(self, core):
        super(MainWindow, self).__init__()
        self.setGeometry(0, 0, 1200, 800)
        self.setWindowTitle("Rare - GUI for legendary")
        self.tab_widget = TabWidget(core)
        self.setCentralWidget(self.tab_widget)
        self.show()

    def closeEvent(self, e: QCloseEvent):
        if QSettings().value("sys_tray", True, bool):
            self.hide()
            e.ignore()
        elif self.tab_widget.downloadTab.active_game is not None and QMessageBox.question(self, "Close", self.tr("There is a download active. Do you really want to exit app?"), QMessageBox.Yes, QMessageBox.No) == QMessageBox.Yes:
            e.accept()
        else:
            e.accept()
