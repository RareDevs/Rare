from collections import deque
from enum import IntEnum
from logging import getLogger
from typing import Optional, Deque

from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt5.QtWidgets import (
    QWidget,
    QGroupBox,
    QVBoxLayout,
    QLabel,
    QSizePolicy,
)
from legendary.models.game import Game, InstalledGame

from rare.components.tabs.downloads.widgets import QueueWidget, UpdateWidget
from rare.models.install import InstallOptionsModel, InstallQueueItemModel
from rare.utils.misc import widget_object_name

logger = getLogger("QueueGroup")


class UpdateGroup(QGroupBox):
    update_count = pyqtSignal(int)
    enqueue = pyqtSignal(InstallOptionsModel)

    def __init__(self, parent=None):
        super(UpdateGroup, self).__init__(parent=parent)
        self.setObjectName(type(self).__name__)
        self.setTitle(self.tr("Updates"))
        self.__text = QLabel(self.tr("No updates available"))
        self.__text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # lk: For findChildren to work, the update's layout has to be in a widget
        self.__container = QWidget(self)
        self.__container.setVisible(False)
        container_layout = QVBoxLayout(self.__container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        layout = QVBoxLayout(self)
        layout.addWidget(self.__text)
        layout.addWidget(self.__container)

    def __find_widget(self, app_name: str) -> Optional[UpdateWidget]:
        return self.__container.findChild(UpdateWidget, name=widget_object_name(UpdateWidget, app_name))

    def count(self) -> int:
        return len(self.__container.findChildren(UpdateWidget, options=Qt.FindDirectChildrenOnly))

    def contains(self, app_name: str) -> bool:
        return self.__find_widget(app_name) is not None

    def __update_group(self):
        count = self.count()
        self.__text.setVisible(not count)
        self.__container.setVisible(bool(count))
        self.update_count.emit(count)

    def append(self, game: Game, igame: InstalledGame):
        self.__text.setVisible(False)
        self.__container.setVisible(True)
        widget: UpdateWidget = self.__find_widget(game.app_name)
        if widget is not None:
            self.__container.layout().removeWidget(widget)
            widget.deleteLater()
        widget = UpdateWidget(game, igame, parent=self.__container)
        widget.destroyed.connect(self.__update_group)
        widget.enqueue.connect(self.enqueue)
        self.__container.layout().addWidget(widget)

    def remove(self, app_name: str):
        widget: UpdateWidget = self.__find_widget(app_name)
        self.__container.layout().removeWidget(widget)
        widget.deleteLater()

    def set_widget_enabled(self, app_name: str, enabled: bool):
        widget: UpdateWidget = self.__find_widget(app_name)
        widget.set_enabled(enabled)

    def get_widget_version(self, app_name: str) -> str:
        widget: UpdateWidget = self.__find_widget(app_name)
        return widget.version()


class QueueGroup(QGroupBox):
    update_count = pyqtSignal(int)
    removed = pyqtSignal(str)
    force = pyqtSignal(InstallQueueItemModel)

    def __init__(self, parent=None):
        super(QueueGroup, self).__init__(parent=parent)
        self.setObjectName(type(self).__name__)
        self.setTitle(self.tr("Queue"))
        self.__text = QLabel(self.tr("No downloads in queue"), self)
        self.__text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # lk: For findChildren to work, the queue's layout has to be in a widget
        self.__container = QWidget(self)
        self.__container.setVisible(False)
        container_layout = QVBoxLayout(self.__container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        layout = QVBoxLayout(self)
        layout.addWidget(self.__text)
        layout.addWidget(self.__container)

        self.__queue: Deque[str] = deque()

    def __find_widget(self, app_name: str) -> Optional[QueueWidget]:
        return self.__container.findChild(QueueWidget, name=widget_object_name(QueueWidget, app_name))

    def count(self) -> int:
        return len(self.__queue)

    def contains(self, app_name: str) -> bool:
        if app_name in self.__queue:
            return self.__find_widget(app_name) is not None
        else:
            return False

    def __update_group(self):
        count = self.count()
        self.__text.setVisible(not count)
        self.__container.setVisible(bool(count))
        self.update_count.emit(count)

    def __create_widget(self, item: InstallQueueItemModel, old_igame: InstalledGame) -> QueueWidget:
        widget: QueueWidget = QueueWidget(item, old_igame, parent=self.__container)
        widget.toggle_arrows(self.__queue.index(item.options.app_name), len(self.__queue))
        widget.destroyed.connect(self.__update_group)
        widget.destroyed.connect(self.__update_arrows)
        widget.remove.connect(self.remove)
        widget.force.connect(self.__on_force)
        widget.move_up.connect(self.__on_move_up)
        widget.move_down.connect(self.__on_move_down)
        return widget

    def push_front(self, item: InstallQueueItemModel, old_igame: InstalledGame):
        self.__text.setVisible(False)
        self.__container.setVisible(True)
        self.__queue.appendleft(item.options.app_name)
        widget = self.__create_widget(item, old_igame)
        self.__container.layout().insertWidget(0, widget)
        if self.count() > 1:
            app_name = self.__queue[1]
            other: QueueWidget = self.__find_widget(app_name)
            other.toggle_arrows(1, len(self.__queue))

    def push_back(self, item: InstallQueueItemModel, old_igame: InstalledGame):
        self.__text.setVisible(False)
        self.__container.setVisible(True)
        self.__queue.append(item.download.game.app_name)
        widget = self.__create_widget(item, old_igame)
        self.__container.layout().addWidget(widget)
        if self.count() > 1:
            app_name = self.__queue[-2]
            other: QueueWidget = self.__find_widget(app_name)
            other.toggle_arrows(len(self.__queue) - 2, len(self.__queue))

    def pop_front(self) -> InstallQueueItemModel:
        app_name = self.__queue.popleft()
        widget: QueueWidget = self.__find_widget(app_name)
        item = widget.item
        widget.deleteLater()
        return item

    def __update_arrows(self):
        """
        Check the first, second, last and second to last widgets in the list
        and update their arrows
        :return: None
        """
        for idx in [0, 1]:
            if self.count() > idx:
                app_name = self.__queue[idx]
                widget: QueueWidget = self.__find_widget(app_name)
                widget.toggle_arrows(idx, len(self.__queue))
        for idx in [1, 2]:
            if self.count() > idx:
                app_name = self.__queue[-idx]
                widget: QueueWidget = self.__find_widget(app_name)
                widget.toggle_arrows(len(self.__queue) - idx, len(self.__queue))

    def __remove(self, app_name: str):
        self.__queue.remove(app_name)
        widget: QueueWidget = self.__find_widget(app_name)
        self.__container.layout().removeWidget(widget)
        widget.deleteLater()

    @pyqtSlot(str)
    def remove(self, app_name: str):
        self.__remove(app_name)
        self.removed.emit(app_name)

    @pyqtSlot(InstallQueueItemModel)
    def __on_force(self, item: InstallQueueItemModel):
        self.__remove(item.options.app_name)
        self.force.emit(item)

    class MoveDirection(IntEnum):
        UP = -1
        DOWN = 1

    def __move(self, app_name: str, direction: MoveDirection):
        """
        Moved the widget for `app_name` up or down in the queue and the container
        :param app_name: The app_name associated with the widget
        :param direction: -1 to move up, +1 to move down
        :return: None
        """
        index = self.__queue.index(app_name)
        self.__queue.remove(app_name)
        self.__queue.insert(index + int(direction), app_name)
        widget: QueueWidget = self.__find_widget(app_name)
        self.__container.layout().insertWidget(index + int(direction), widget)
        self.__update_arrows()

    @pyqtSlot(str)
    def __on_move_up(self, app_name: str):
        self.__move(app_name, QueueGroup.MoveDirection.UP)

    @pyqtSlot(str)
    def __on_move_down(self, app_name: str):
        self.__move(app_name, QueueGroup.MoveDirection.DOWN)
