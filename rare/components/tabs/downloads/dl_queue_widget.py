from logging import getLogger

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QWidget
from qtawesome import icon

from rare.utils.models import InstallQueueItemModel

logger = getLogger("QueueWidget")


class DlWidget(QWidget):
    move_up = pyqtSignal(str)  # app_name
    move_down = pyqtSignal(str)  # app_name
    remove = pyqtSignal(str)  # app_name

    def __init__(self, index, queue_item: InstallQueueItemModel):
        super(DlWidget, self).__init__()
        self.app_name = queue_item.download.game.app_name
        self.layout = QHBoxLayout()

        self.left_layout = QVBoxLayout()
        self.move_up_button = QPushButton(icon("fa.arrow-up"), "")
        if index == 0:
            self.move_up_button.setDisabled(True)
        self.move_up_button.clicked.connect(lambda: self.move_up.emit(self.app_name))
        self.move_up_button.setFixedWidth(20)
        self.left_layout.addWidget(self.move_up_button)

        self.move_down_buttton = QPushButton(icon("fa.arrow-down"), "")
        self.move_down_buttton.clicked.connect(lambda: self.move_down.emit(self.app_name))
        self.left_layout.addWidget(self.move_down_buttton)
        self.move_down_buttton.setFixedWidth(20)

        self.layout.addLayout(self.left_layout)

        self.right_layout = QVBoxLayout()
        self.title = QLabel(queue_item.download.game.app_title)
        self.right_layout.addWidget(self.title)

        dl_size = queue_item.download.analysis.dl_size
        install_size = queue_item.download.analysis.install_size

        self.size = QHBoxLayout()

        self.size.addWidget(QLabel(self.tr("Download size: {} GB").format(round(dl_size / 1024 ** 3, 2))))
        self.size.addWidget(QLabel(self.tr("Install size: {} GB").format(round(install_size / 1024 ** 3, 2))))
        self.right_layout.addLayout(self.size)

        self.delete = QPushButton(self.tr("Remove Download"))
        self.delete.clicked.connect(lambda: self.remove.emit(self.app_name))
        self.right_layout.addWidget(self.delete)

        self.layout.addLayout(self.right_layout)
        self.setLayout(self.layout)


class DlQueueWidget(QGroupBox):
    update_list = pyqtSignal(list)
    item_removed = pyqtSignal(str)
    dl_queue = []

    def __init__(self):

        super(DlQueueWidget, self).__init__()
        self.setTitle(self.tr("Download Queue"))
        self.setLayout(QVBoxLayout())
        self.setObjectName("group")
        self.text = QLabel(self.tr("No downloads in queue"))
        self.layout().addWidget(self.text)

    def update_queue(self, dl_queue: list):
        logger.debug("Update Queue " + ", ".join(i.download.game.app_title for i in dl_queue))
        self.dl_queue = dl_queue

        for item in (self.layout().itemAt(i) for i in range(self.layout().count())):
            item.widget().deleteLater()

        if len(dl_queue) == 0:
            self.layout().addWidget(QLabel(self.tr("No downloads in queue")))
            self.setLayout(self.layout())
            return

        for index, item in enumerate(dl_queue):
            widget = DlWidget(index, item)
            widget.remove.connect(self.remove)
            widget.move_up.connect(self.move_up)
            widget.move_down.connect(self.move_down)
            self.layout().addWidget(widget)
            if index + 1 == len(dl_queue):
                widget.move_down_buttton.setDisabled(True)

    def remove(self, app_name):
        for index, i in enumerate(self.dl_queue):
            if i.download.game.app_name == app_name:
                self.dl_queue.pop(index)
                self.item_removed.emit(app_name)
                break
        else:
            logger.warning("BUG! " + app_name)
            return
        self.update_list.emit(self.dl_queue)
        self.update_queue(self.dl_queue)

    def move_up(self, app_name):
        index: int

        for i, item in enumerate(self.dl_queue):
            if item.download.game.app_name == app_name:
                index = i
                break
        else:
            logger.warning("Could not find appname" + app_name)
            return
        self.dl_queue.insert(index - 1, self.dl_queue.pop(index))
        self.update_list.emit(self.dl_queue)
        self.update_queue(self.dl_queue)

    def move_down(self, app_name):
        index: int

        for i, item in enumerate(self.dl_queue):
            if item.download.game.app_name == app_name:
                index = i
                break
        else:
            logger.warning("infoCould not find appname" + app_name)
            return
        self.dl_queue.insert(index + 1, self.dl_queue.pop(index))
        self.update_list.emit(self.dl_queue)
        self.update_queue(self.dl_queue)
