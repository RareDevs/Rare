from typing import Union

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics, QResizeEvent
from PyQt5.QtWidgets import QLabel, QWIDGETSIZE_MAX


class ElideLabel(QLabel):

    def __init__(self, text="", parent=None):
        super(ElideLabel, self).__init__(parent=parent)
        self.__text = text
        self.__fm = QFontMetrics(self.font())
        self.__tooltip = ""
        self.setFixedHeight(True)
        self.setWordWrap(True)
        self.setText(text)

    def setText(self, a0: str) -> None:
        self.__text = a0
        self.__setElideText(a0)

    def __setElideText(self, a0: str):
        elided_text = self.__fm.elidedText(
            a0, Qt.ElideRight,
            self.width() - (self.contentsMargins().left() + self.contentsMargins().right())
        )
        if not self.__tooltip:
            if self.__fm.boundingRect(elided_text).width() < self.__fm.boundingRect(self.__text).width():
                super(ElideLabel, self).setToolTip(self.__text)
            else:
                super(ElideLabel, self).setToolTip("")
        super(ElideLabel, self).setText(elided_text)

    def setToolTip(self, a0: str) -> None:
        self.__tooltip = a0
        super(ElideLabel, self).setToolTip(a0)

    def resizeEvent(self, a0: QResizeEvent) -> None:
        self.__setElideText(self.__text)
        super(ElideLabel, self).resizeEvent(a0)

    def setFixedHeight(self, h: Union[int, bool]) -> None:
        if isinstance(h, bool):
            super(ElideLabel, self).setFixedHeight(self.__fm.height() if h else QWIDGETSIZE_MAX)
        elif isinstance(h, int):
            super(ElideLabel, self).setFixedHeight(h)
