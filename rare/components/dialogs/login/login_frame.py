from abc import abstractmethod
from logging import getLogger

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QFrame

from rare.lgndr.core import LegendaryCore


class LoginFrame(QFrame):
    success = Signal()
    validated = Signal(bool)

    def __init__(self, core: LegendaryCore, parent=None):
        super(LoginFrame, self).__init__(parent=parent)

        self.logger = getLogger(type(self).__name__)
        self.core = core

        self.setFrameStyle(QFrame.Shape.StyledPanel)

    @abstractmethod
    def is_valid(self) -> bool:
        pass

    @Slot()
    def _on_input_changed(self):
        self.validated.emit(self.is_valid())

    @abstractmethod
    def do_login(self) -> None:
        pass

