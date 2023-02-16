from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics, QResizeEvent
from PyQt5.QtWidgets import QLabel


class ElideLabel(QLabel):
    __text: str = ""

    def __init__(self, text="", parent=None, flags=Qt.WindowFlags()):
        super(ElideLabel, self).__init__(parent=parent, flags=flags)
        if text:
            self.setText(text)

    def setText(self, a0: str) -> None:
        self.__text = a0
        self.__setElideText(a0)

    def __setElideText(self, a0: str):
        metrics = QFontMetrics(self.font())
        elided_text = metrics.elidedText(
            a0, Qt.ElideRight,
            self.width() - self.contentsMargins().left() - self.contentsMargins().right()
        )
        super(ElideLabel, self).setText(elided_text)

    def resizeEvent(self, a0: QResizeEvent) -> None:
        self.__setElideText(self.__text)
        super(ElideLabel, self).resizeEvent(a0)
