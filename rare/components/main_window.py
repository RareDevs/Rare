from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QMainWindow, QMessageBox

from rare.components.tab_widget import TabWidget


class MainWindow(QMainWindow):
    def __init__(self, core):
        super(MainWindow, self).__init__()
        settings = QSettings()
        width, height = 1200, 800
        if settings.value("save_size", False):
            width, height = settings.value("window_size", (1200, 800), tuple)

        self.setGeometry(0, 0, width, height)
        self.setWindowTitle("Rare - GUI for legendary")
        self.tab_widget = TabWidget(core)
        self.setCentralWidget(self.tab_widget)
        self.show()

    def closeEvent(self, e: QCloseEvent):
        settings = QSettings()
        if settings.value("sys_tray", True, bool):
            self.hide()
            e.ignore()
            return
        elif self.tab_widget.downloadTab.active_game is not None:
            if not QMessageBox.question(self, "Close", self.tr("There is a download active. Do you really want to exit app?"), QMessageBox.Yes, QMessageBox.No) == QMessageBox.Yes:
                e.ignore()
                return
        if settings.value("save_size", False, bool):
            size = self.size().width(), self.size().height()
            settings.setValue("window_size", size)
        e.accept()

