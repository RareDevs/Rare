from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QMovie, QShowEvent
from PySide6.QtWidgets import QLabel, QWidget


class LoadingWidget(QLabel):
    def __init__(self, autostart: bool = False, *, parent: QWidget | None = None):
        super(LoadingWidget, self).__init__(parent=parent)
        self.setObjectName(type(self).__name__)
        self.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        # The animation's exact size is 94x94
        self.setFixedSize(96, 96)
        self.setMovie(QMovie(':/images/loader.webp', parent=self))
        if self.parent() is not None:
            self.parent().installEventFilter(self)
        self.setVisible(autostart)

    def _center_on_parent(self):
        rect = self.rect()
        rect.moveCenter(self.parent().contentsRect().center())
        self.setGeometry(rect)

    def event(self, e: QEvent) -> bool:
        # FIXME: investigate why this happens
        if not isinstance(e, QEvent):
            return True
        if e.type() == QEvent.Type.ParentAboutToChange:
            if self.parent() is not None:
                self.parent().removeEventFilter(self)
        if e.type() == QEvent.Type.ParentChange:
            if self.parent() is not None:
                self.parent().installEventFilter(self)
        return super().event(e)

    def showEvent(self, a0: QShowEvent) -> None:
        if a0.spontaneous():
            super().showEvent(a0)
            return
        self._center_on_parent()
        super().showEvent(a0)

    def eventFilter(self, a0: QObject, a1: QEvent) -> bool:
        if not isinstance(a1, QEvent):
            return True
        if a0 is self.parent() and a1.type() == QEvent.Type.Resize:
            self._center_on_parent()
            return a0.event(a1)
        return False

    def setVisible(self, visible: bool) -> None:
        super().setVisible(visible)
        if visible:
            self.raise_()
            self.movie().start()
        else:
            self.lower()
            self.movie().stop()

    def start(self):
        self.setVisible(True)

    def stop(self):
        self.setVisible(False)
