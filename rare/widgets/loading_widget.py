import qtawesome
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QApplication

from rare.utils.misc import icon


class LoadingWidget(qtawesome.IconWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setIconSize(QSize(128, 128))
        spin_icon = icon('mdi.loading',
                         animation=qtawesome.Spin(self, interval=5))
        self.setIcon(spin_icon)


if __name__ == '__main__':
    app = QApplication([])
    w = LoadingWidget()
    w.show()
    app.exec_()
