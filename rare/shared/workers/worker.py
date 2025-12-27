from abc import abstractmethod
from dataclasses import dataclass
from enum import IntEnum
from logging import Logger, getLogger

from PySide6.QtCore import QObject, QRunnable, Signal, Slot


class Worker(QRunnable):
    """
    Base QRunnable class.

    This class provides a base for QRunnables with signals that are automatically deleted.

    To use this class you have to assign the signals object of your concrete implementation
    to the `Worker.signals` attribute and implement `Worker.run_real()`
    """

    def __init__(self):
        super(Worker, self).__init__()
        self.setAutoDelete(True)
        self.__logger = getLogger(type(self).__name__)
        self.__signals: QObject = None

    def __str__(self):
        return type(self).__name__

    @property
    def logger(self) -> Logger:
        return self.__logger

    @property
    def signals(self) -> QObject:
        if self.__signals is None:
            raise RuntimeError(f"Subclasses must assign '{type(self).__name__}.signals' QObject attribute")
        return self.__signals

    @signals.setter
    def signals(self, obj: QObject):
        self.__signals = obj

    @abstractmethod
    def run_real(self):
        pass

    @Slot()
    def run(self):
        self.run_real()
        self.signals.disconnect(self.signals)
        self.signals.deleteLater()


class QueueWorkerState(IntEnum):
    UNDEFINED = 0
    QUEUED = 1
    ACTIVE = 2


@dataclass
class QueueWorkerInfo:
    app_name: str
    app_title: str
    type: str
    prefix: str
    state: QueueWorkerState
    progress: int = 0


class QueueWorkerSignals(QObject):
    # object: worker object
    started = Signal(object)
    # object: worker object
    finished = Signal(object)


class QueueWorker(Worker):
    """
    Base queueable worker class

    This class is a specialization of the `Worker` class. It provides feedback signals to know
    if a worker has started or finished.

    To use this class you have to assign the signals object of your concrete implementation
    to the `QueueWorker.signals` attribute, implement `QueueWorker.run_real()` and `QueueWorker.worker_info()`
    """

    def __init__(self):
        super(QueueWorker, self).__init__()
        self.feedback = QueueWorkerSignals()
        self.state = QueueWorkerState.QUEUED
        self._kill = False

    @Slot()
    def run(self):
        self.state = QueueWorkerState.ACTIVE
        self.feedback.started.emit(self)
        super(QueueWorker, self).run()
        self.feedback.finished.emit(self)
        self.feedback.started.disconnect()
        self.feedback.finished.disconnect()
        self.feedback.deleteLater()

    @abstractmethod
    def worker_info(self) -> QueueWorkerInfo:
        pass

    def kill(self):
        raise NotImplementedError
        self._kill = True
