import os
from logging import getLogger

from PyQt5.QtCore import Qt, QSettings, QTimer, QSize, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QCloseEvent, QCursor, QShowEvent
from PyQt5.QtWidgets import (
    QMainWindow,
    QApplication,
    QStatusBar,
    QScrollArea,
    QScroller,
    QComboBox,
    QMessageBox,
    QLabel,
    QWidget,
    QHBoxLayout,
)

from rare.components.tabs import MainTabWidget
from rare.components.tray_icon import TrayIcon
from rare.shared import RareCore
from rare.shared.workers.worker import QueueWorkerState
from rare.utils.paths import lock_file
from rare.widgets.elide_label import ElideLabel

logger = getLogger("MainWindow")


class MainWindow(QMainWindow):
    # int: exit code
    exit_app: pyqtSignal = pyqtSignal(int)

    def __init__(self, parent=None):
        self.__exit_code = 0
        self.__accept_close = False
        self._window_launched = False
        super(MainWindow, self).__init__(parent=parent)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.rcore = RareCore.instance()
        self.core = RareCore.instance().core()
        self.signals = RareCore.instance().signals()
        self.args = RareCore.instance().args()
        self.settings = QSettings()

        self.setWindowTitle("Rare - GUI for legendary")
        self.tab_widget = MainTabWidget(self)
        self.tab_widget.exit_app.connect(self.on_exit_app)
        self.setCentralWidget(self.tab_widget)

        # Set up status bar stuff (jumping through a lot of hoops)
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        self.active_label = QLabel(self.tr("Active:"), self.status_bar)
        # lk: set top and botton margins to accommodate border for scroll area labels
        self.active_label.setContentsMargins(5, 1, 0, 1)
        self.status_bar.addWidget(self.active_label)

        self.active_container = QWidget(self.status_bar)
        active_layout = QHBoxLayout(self.active_container)
        active_layout.setContentsMargins(0, 0, 0, 0)
        active_layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        self.status_bar.addWidget(self.active_container, stretch=0)

        self.queued_label = QLabel(self.tr("Queued:"), self.status_bar)
        # lk: set top and botton margins to accommodate border for scroll area labels
        self.queued_label.setContentsMargins(5, 1, 0, 1)
        self.status_bar.addPermanentWidget(self.queued_label)

        self.queued_scroll = QScrollArea(self.status_bar)
        self.queued_scroll.setFrameStyle(QScrollArea.NoFrame)
        self.queued_scroll.setWidgetResizable(True)
        self.queued_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.queued_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.queued_scroll.setFixedHeight(self.queued_label.sizeHint().height())
        self.status_bar.addPermanentWidget(self.queued_scroll, stretch=1)

        self.queued_container = QWidget(self.queued_scroll)
        queued_layout = QHBoxLayout(self.queued_container)
        queued_layout.setContentsMargins(0, 0, 0, 0)
        queued_layout.setSizeConstraint(QHBoxLayout.SetFixedSize)

        self.active_label.setVisible(False)
        self.active_container.setVisible(False)
        self.queued_label.setVisible(False)
        self.queued_scroll.setVisible(False)

        self.signals.application.update_statusbar.connect(self.update_statusbar)

        # self.status_timer = QTimer(self)
        # self.status_timer.timeout.connect(self.update_statusbar)
        # self.status_timer.setInterval(5000)
        # self.status_timer.start()

        width, height = 1280, 720
        if self.settings.value("save_size", False, bool):
            width, height = self.settings.value("window_size", (width, height), tuple)

        self.resize(width, height)

        if not self.args.offline:
            try:
                from rare.utils.rpc import DiscordRPC

                self.rpc = DiscordRPC()
            except ModuleNotFoundError:
                logger.warning("Discord RPC module not found")

        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.timer_finished)
        self.timer.start()

        self.tray_icon: TrayIcon = TrayIcon(self)
        self.tray_icon.exit_app.connect(self.on_exit_app)
        self.tray_icon.show_app.connect(self.show)
        self.tray_icon.activated.connect(lambda r: self.toggle() if r == self.tray_icon.DoubleClick else None)

        # enable kinetic scrolling
        for scroll_area in self.findChildren(QScrollArea):
            if not scroll_area.property("no_kinetic_scroll"):
                QScroller.grabGesture(scroll_area.viewport(), QScroller.LeftMouseButtonGesture)

            # fix scrolling
            for combo_box in scroll_area.findChildren(QComboBox):
                combo_box.wheelEvent = lambda e: e.ignore()

    def center_window(self):
        # get the margins of the decorated window
        margins = self.windowHandle().frameMargins()
        # get the screen the cursor is on
        current_screen = QApplication.screenAt(QCursor.pos())
        if not current_screen:
            current_screen = QApplication.primaryScreen()
        # get the available screen geometry (excludes panels/docks)
        screen_rect = current_screen.availableGeometry()
        decor_width = margins.left() + margins.right()
        decor_height = margins.top() + margins.bottom()
        window_size = QSize(self.width(), self.height()).boundedTo(
            screen_rect.size() - QSize(decor_width, decor_height)
        )

        self.resize(window_size)
        self.move(screen_rect.center() - self.rect().adjusted(0, 0, decor_width, decor_height).center())

    # lk: For the gritty details see `RareCore.load_pixmaps()` method
    # Just before the window is shown, fire a timer to load game icons
    # This is by nature a little iffy because we don't really know if the
    # has been shown, and it might make the window delay as widgets being are updated.
    # Still better than showing a hanged window frame for a few seconds.
    def showEvent(self, a0: QShowEvent) -> None:
        if not self._window_launched:
            QTimer.singleShot(100, self.rcore.load_pixmaps)

    @pyqtSlot()
    def show(self) -> None:
        super(MainWindow, self).show()
        if not self._window_launched:
            self.center_window()
        self._window_launched = True

    def hide(self) -> None:
        if self.settings.value("save_size", False, bool):
            size = self.size().width(), self.size().height()
            self.settings.setValue("window_size", size)
        super(MainWindow, self).hide()

    def toggle(self):
        if self.isHidden():
            self.show()
        else:
            self.hide()

    @pyqtSlot()
    def update_statusbar(self):
        self.active_label.setVisible(False)
        self.active_container.setVisible(False)
        self.queued_label.setVisible(False)
        self.queued_scroll.setVisible(False)
        for label in self.active_container.findChildren(QLabel, options=Qt.FindDirectChildrenOnly):
            self.active_container.layout().removeWidget(label)
            label.deleteLater()
        for label in self.queued_container.findChildren(QLabel, options=Qt.FindDirectChildrenOnly):
            self.queued_container.layout().removeWidget(label)
            label.deleteLater()
        for info in self.rcore.queue_info():
            label = ElideLabel(info.app_title)
            label.setObjectName("QueueWorkerLabel")
            label.setToolTip(f"<b>{info.worker_type}</b>: {info.app_title}")
            label.setProperty("workerType", info.worker_type)
            label.setFixedWidth(150)
            label.setContentsMargins(3, 0, 3, 0)
            if info.state == QueueWorkerState.ACTIVE:
                self.active_container.layout().addWidget(label)
                self.active_label.setVisible(True)
                self.active_container.setVisible(True)
            elif info.state == QueueWorkerState.QUEUED:
                self.queued_container.layout().addWidget(label)
                self.queued_label.setVisible(True)
                self.queued_scroll.setVisible(True)

    def timer_finished(self):
        file_path = lock_file()
        if os.path.exists(file_path):
            file = open(file_path, "r")
            action = file.read()
            file.close()
            if action.startswith("show"):
                self.show()
            os.remove(file_path)
        self.timer.start()

    @pyqtSlot()
    @pyqtSlot(int)
    def on_exit_app(self, exit_code=0) -> None:
        self.__exit_code = exit_code
        self.close()

    def close(self) -> bool:
        self.__accept_close = True
        return super(MainWindow, self).close()

    def closeEvent(self, e: QCloseEvent) -> None:
        # lk: `accept_close` is set to `True` by the `close()` method, overrides exiting to tray in `closeEvent()`
        # lk: ensures exiting instead of hiding when `close()` is called programmatically
        if not self.__accept_close:
            if self.settings.value("sys_tray", False, bool):
                self.hide()
                e.ignore()
                return

        # FIXME: Move this to RareCore once the download manager is implemented
        if not self.args.offline:
            if self.rcore.queue_threadpool.activeThreadCount():
                reply = QMessageBox.question(
                    self,
                    self.tr("Quit {}?").format(QApplication.applicationName()),
                    self.tr(
                        "There are currently running operations. "
                        "Rare cannot exit until they are completed.\n\n"
                        "Do you want to clear the queue?"
                    ),
                    buttons=(QMessageBox.Yes | QMessageBox.No),
                    defaultButton=QMessageBox.No,
                )
                if reply == QMessageBox.Yes:
                    self.rcore.queue_threadpool.clear()
                    for qw in self.rcore.queued_workers():
                        self.rcore.dequeue_worker(qw)
                    self.update_statusbar()
                e.ignore()
                return
            elif self.tab_widget.downloads_tab.is_download_active:
                reply = QMessageBox.question(
                    self,
                    self.tr("Quit {}?").format(QApplication.applicationName()),
                    self.tr(
                        "There is an active download. "
                        "Quitting Rare now will stop the download.\n\n"
                        "Are you sure you want to quit?"
                    ),
                    buttons=(QMessageBox.Yes | QMessageBox.No),
                    defaultButton=QMessageBox.No,
                )
                if reply == QMessageBox.Yes:
                    self.tab_widget.downloads_tab.stop_download(omit_queue=True)
                else:
                    e.ignore()
                    return
        # FIXME: End of FIXME
        self.timer.stop()
        self.tray_icon.deleteLater()
        self.hide()
        self.exit_app.emit(self.__exit_code)
        super(MainWindow, self).closeEvent(e)

