from argparse import Namespace
from collections import deque
from enum import IntEnum
from logging import getLogger
from typing import Optional

from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt5.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QLabel, QSizePolicy, QWidget,
)
from legendary.models.game import Game, InstalledGame

from rare.components.tabs.downloads.widgets import QueueWidget, UpdateWidget
from rare.models.install import InstallOptionsModel, InstallQueueItemModel

logger = getLogger("QueueGroup")


class UpdateGroup(QGroupBox):
    enqueue = pyqtSignal(InstallOptionsModel)

    def __init__(self, parent=None):
        super(UpdateGroup, self).__init__(parent=parent)
        self.setObjectName(type(self).__name__)
        self.setTitle(self.tr("Updates"))
        self.text = QLabel(self.tr("No updates available"))
        self.text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # lk: For findChildren to work, the upates's layout has to be in a widget
        self.container = QWidget(self)
        self.container.setLayout(QVBoxLayout())
        self.container.layout().setContentsMargins(0, 0, 0, 0)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.text)
        self.layout().addWidget(self.container)

    @staticmethod
    def __widget_name(app_name: str) -> str:
        return f"UpdateWidget_{app_name}"

    def __find_widget(self, app_name: str) -> Optional[UpdateWidget]:
        return self.container.findChild(UpdateWidget, name=self.__widget_name(app_name))

    def count(self) -> int:
        return len(self.container.findChildren(UpdateWidget, options=Qt.FindDirectChildrenOnly))

    def contains(self, app_name: str) -> bool:
        return  self.__find_widget(app_name) is not None

    def append(self, game: Game, igame: InstalledGame):
        self.text.setVisible(False)
        self.container.setVisible(True)
        widget: UpdateWidget = self.__find_widget(game.app_name)
        if widget is not None:
            self.container.layout().removeWidget(widget)
            widget.deleteLater()
        widget = UpdateWidget(game, igame, parent=self.container)
        widget.enqueue.connect(self.enqueue)
        self.container.layout().addWidget(widget)

    def remove(self, app_name: str):
        widget: UpdateWidget = self.__find_widget(app_name)
        self.container.layout().removeWidget(widget)
        widget.deleteLater()
        self.text.setVisible(not bool(self.count()))
        self.container.setVisible(bool(self.count()))

    def set_widget_enabled(self, app_name: str, enabled: bool):
        widget: UpdateWidget = self.__find_widget(app_name)
        widget.set_enabled(enabled)

    def get_update_version(self, app_name: str) -> str:
        widget: UpdateWidget = self.__find_widget(app_name)
        return widget.version()


class QueueGroup(QGroupBox):
    removed = pyqtSignal(str)
    force = pyqtSignal(InstallQueueItemModel)

    def __init__(self, parent=None):
        super(QueueGroup, self).__init__(parent=parent)
        self.setObjectName(type(self).__name__)
        self.setTitle(self.tr("Queue"))
        self.text = QLabel(self.tr("No downloads in queue"), self)
        self.text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # lk: For findChildren to work, the queue's layout has to be in a widget
        self.container = QWidget(self)
        self.container.setLayout(QVBoxLayout())
        self.container.layout().setContentsMargins(0, 0, 0, 0)
        self.container.setVisible(False)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.text)
        self.layout().addWidget(self.container)

        self.queue = deque()

    @staticmethod
    def __widget_name(app_name:str) -> str:
        return f"QueueWidget_{app_name}"

    def __find_widget(self, app_name: str) -> Optional[QueueWidget]:
        return self.container.findChild(QueueWidget, name=self.__widget_name(app_name))

    def contains(self, app_name: str) -> bool:
        return  self.__find_widget(app_name) is not None

    def count(self) -> int:
        return len(self.queue)

    def __create_widget(self, item: InstallQueueItemModel, old_igame: InstalledGame) -> QueueWidget:
        widget: QueueWidget = QueueWidget(item, old_igame, parent=self.container)
        widget.toggle_arrows(self.queue.index(item.download.game.app_name), len(self.queue))
        widget.remove.connect(self.remove)
        widget.force.connect(self.__on_force)
        widget.move_up.connect(self.__on_move_up)
        widget.move_down.connect(self.__on_move_down)
        return widget

    def push_front(self, item: InstallQueueItemModel, old_igame: InstalledGame):
        self.text.setVisible(False)
        self.container.setVisible(True)
        self.queue.appendleft(item.download.game.app_name)
        widget = self.__create_widget(item, old_igame)
        self.container.layout().insertWidget(0, widget)
        if self.count() > 1:
            app_name = self.queue[1]
            other: QueueWidget =  self.__find_widget(app_name)
            other.toggle_arrows(1, len(self.queue))

    def push_back(self, item: InstallQueueItemModel, old_igame: InstalledGame):
        self.text.setVisible(False)
        self.container.setVisible(True)
        self.queue.append(item.download.game.app_name)
        widget = self.__create_widget(item, old_igame)
        self.container.layout().addWidget(widget)
        if self.count() > 1:
            app_name = self.queue[-2]
            other: QueueWidget =  self.__find_widget(app_name)
            other.toggle_arrows(len(self.queue) - 2, len(self.queue))

    def pop_front(self) -> InstallQueueItemModel:
        app_name = self.queue.popleft()
        widget: QueueWidget = self.__find_widget(app_name)
        item = widget.item
        widget.deleteLater()
        self.text.setVisible(not bool(self.count()))
        self.container.setVisible(bool(self.count()))
        return item

    def __update_queue(self):
        """
        check the first, second, last and second to last widgets in the list
        and update their arrows
        :return: None
        """
        for idx in [0, 1]:
            if self.count() > idx:
                app_name = self.queue[idx]
                widget: QueueWidget =  self.__find_widget(app_name)
                widget.toggle_arrows(idx, len(self.queue))
        for idx in [1, 2]:
            if self.count() > idx:
                app_name = self.queue[-idx]
                widget: QueueWidget =  self.__find_widget(app_name)
                widget.toggle_arrows(len(self.queue) - idx, len(self.queue))

    def __remove(self, app_name: str):
        self.queue.remove(app_name)
        widget: QueueWidget = self.__find_widget(app_name)
        self.container.layout().removeWidget(widget)
        widget.deleteLater()
        self.__update_queue()
        self.text.setVisible(not bool(self.count()))
        self.container.setVisible(bool(self.count()))

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
        index = self.queue.index(app_name)
        self.queue.remove(app_name)
        self.queue.insert(index + int(direction), app_name)
        widget: QueueWidget = self.__find_widget(app_name)
        self.container.layout().insertWidget(index + int(direction), widget)
        self.__update_queue()

    @pyqtSlot(str)
    def __on_move_up(self, app_name: str):
        self.__move(app_name, QueueGroup.MoveDirection.UP)

    @pyqtSlot(str)
    def __on_move_down(self, app_name: str):
        self.__move(app_name, QueueGroup.MoveDirection.DOWN)


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QDialog
    from rare.utils.misc import set_style_sheet

    app = QApplication(sys.argv)

    set_style_sheet("RareStyle")

    queue_group = QueueGroup()

    dialog = QDialog()
    dialog.setLayout(QVBoxLayout())
    dialog.layout().addWidget(queue_group)
    for i in range(5):
        rgame = Namespace(app_name=i, title=f"{i}", remote_version=f"{i}", version=f"{i}")
        analysis = Namespace(dl_size=i*1024, install_size=i*2048)
        game = Namespace(app_name=f"{i}")
        download = Namespace(analysis=analysis, game=game)
        model = InstallQueueItemModel(rgame=rgame, download=download, options=True)
        queue_group.push_back(model)
    dialog.layout().setSizeConstraint(QVBoxLayout.SetFixedSize)
    dialog.show()
    sys.exit(app.exec_())