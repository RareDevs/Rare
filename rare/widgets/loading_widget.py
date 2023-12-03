from PyQt5.QtCore import QEvent, QObject, Qt
from PyQt5.QtGui import QShowEvent, QMovie
from PyQt5.QtWidgets import QLabel


class LoadingWidget(QLabel):
    def __init__(self, autostart=False, parent=None):
        super(LoadingWidget, self).__init__(parent=parent)
        self.setObjectName(type(self).__name__)
        self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.movie = QMovie(":/images/loader.webp", parent=self)
        # The animation's exact size is 94x94
        self.setFixedSize(96, 96)
        self.setMovie(self.movie)
        if self.parent() is not None:
            self.parent().installEventFilter(self)
        if autostart:
            self.movie.start()

    def __center_on_parent(self):
        rect = self.rect()
        rect.moveCenter(self.parent().contentsRect().center())
        self.setGeometry(rect)

    def event(self, e: QEvent) -> bool:
        if e.type() == QEvent.ParentAboutToChange:
            if self.parent() is not None:
                self.parent().removeEventFilter(self)
        if e.type() == QEvent.ParentChange:
            if self.parent() is not None:
                self.parent().installEventFilter(self)
        return super().event(e)

    def showEvent(self, a0: QShowEvent) -> None:
        if a0.spontaneous():
            return super().showEvent(a0)
        self.__center_on_parent()
        super().showEvent(a0)

    def eventFilter(self, a0: QObject, a1: QEvent) -> bool:
        if a0 is self.parent() and a1.type() == QEvent.Resize:
            self.__center_on_parent()
            return a0.event(a1)
        return False

    def start(self):
        self.setVisible(True)
        self.movie.start()

    def stop(self):
        self.setVisible(False)
        self.movie.stop()
