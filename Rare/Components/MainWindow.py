from PyQt5.QtWidgets import QMainWindow

from Rare.Components.TabWidget import TabWidget


class MainWindow(QMainWindow):
    def __init__(self, core):
        super(MainWindow, self).__init__()
        self.setGeometry(0, 0, 1200, 800)
        self.setWindowTitle("Rare - GUI for legendary")
        self.setCentralWidget(TabWidget(core))
        self.show()
