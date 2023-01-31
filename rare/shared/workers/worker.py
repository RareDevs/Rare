import sys
from abc import abstractmethod
from typing import Optional

from PyQt5.QtCore import QRunnable, QObject, pyqtSlot


class Worker(QRunnable):
    def __init__(self):
        sys.excepthook = sys.__excepthook__
        super(Worker, self).__init__()
        self.setAutoDelete(True)
        self.__signals: Optional[QObject] = None

    @property
    def signals(self) -> QObject:
        if self.__signals is None:
            raise NotImplementedError
        return self.__signals

    @signals.setter
    def signals(self, obj: QObject):
        self.__signals = obj

    @abstractmethod
    def run_real(self):
        pass

    @pyqtSlot()
    def run(self):
        self.run_real()
        self.signals.deleteLater()
