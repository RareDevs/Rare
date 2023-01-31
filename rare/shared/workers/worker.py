import sys
from abc import abstractmethod
from enum import IntEnum
from typing import Optional

from PyQt5.QtCore import QRunnable, QObject, pyqtSlot, pyqtSignal


class Worker(QRunnable):
    """
    Base QRunnable class.

    This class provides a base for QRunnables with signals that are automatically deleted.

    To use this class you have to assign the signals object of your concrete implementation
    to the `Worker.signals` attribute and implement `Worker.run_real()`
    """

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


class QueueWorker(Worker):
    """
    Base queueable worker class

    This class is a specialization of the `Worker` class. It provides feedback signals to know
    if a worker has started or finished.

    To use this class you have to assign the signals object of your concrete implementation
    to the `QueueWorker.signals` attribute, implement `QueueWorker.run_real()` and `QueueWorker.worker_info()`
    """

    class State(IntEnum):
        UNDEFINED = 0
        QUEUED = 1
        ACTIVE = 2

    class Signals(QObject):
        started = pyqtSignal()
        finished = pyqtSignal()

    def __init__(self):
        super(QueueWorker, self).__init__()
        self.feedback = QueueWorker.Signals()
        self.state = QueueWorker.State.QUEUED

    @pyqtSlot()
    def run(self):
        self.state = QueueWorker.State.ACTIVE
        self.feedback.started.emit()
        super(QueueWorker, self).run()
        self.feedback.finished.emit()
        self.feedback.deleteLater()

    @abstractmethod
    def worker_info(self):
        pass