import datetime
from logging import getLogger
from multiprocessing import Queue as MPQueue

from PyQt5.QtCore import QThread, pyqtSignal, Qt, QSettings
from PyQt5.QtWidgets import QWidget, QMessageBox, QVBoxLayout, QLabel, QGridLayout, QProgressBar, QPushButton, QDialog, \
    QListWidget, QHBoxLayout, QGroupBox

from custom_legendary.core import LegendaryCore
from custom_legendary.models.downloading import UIUpdate
from custom_legendary.models.game import Game, InstalledGame
from custom_legendary.utils.selective_dl import games
from rare.components.dialogs.install_dialog import InstallInfoDialog, InstallDialog
from rare.components.tabs.downloads.dl_queue_widget import DlQueueWidget
from rare.components.tabs.downloads.download_thread import DownloadThread
from rare.utils.models import InstallOptions
from rare.utils.utils import get_size

logger = getLogger("Download")


class DownloadTab(QWidget):
    finished = pyqtSignal(bool)
    thread: QThread
    dl_queue = []

    def __init__(self, core: LegendaryCore, updates: list, parent):
        super(DownloadTab, self).__init__(parent=parent)
        self.core = core
        self.layout = QVBoxLayout()
        self.active_game: Game = None

        self.info_layout = QGridLayout()

        self.installing_game = QLabel(self.tr("No active Download"))
        self.info_layout.addWidget(self.installing_game, 0, 0)
        self.dl_speed = QLabel()
        self.info_layout.addWidget(self.dl_speed, 0, 1)
        self.cache_used = QLabel()
        self.info_layout.addWidget(self.cache_used, 1, 0)
        self.downloaded = QLabel()
        self.info_layout.addWidget(self.downloaded, 1, 1)
        self.time_left = QLabel()
        self.info_layout.addWidget(self.time_left, 2, 0)

        self.layout.addLayout(self.info_layout)

        self.mini_layout = QHBoxLayout()
        self.prog_bar = QProgressBar()
        self.mini_layout.addWidget(self.prog_bar)
        self.prog_bar.setMaximum(100)

        self.kill_button = QPushButton(self.tr("Stop Download"))
        self.mini_layout.addWidget(self.kill_button)
        self.kill_button.setDisabled(True)
        self.kill_button.clicked.connect(self.stop_download)

        self.layout.addLayout(self.mini_layout)

        self.queue_widget = DlQueueWidget()
        self.layout.addWidget(self.queue_widget)
        self.queue_widget.update_list.connect(self.update_dl_queue)

        self.updates = QGroupBox(self.tr("Updates"))
        self.layout.addWidget(self.updates)
        self.update_layout = QVBoxLayout()
        self.updates.setLayout(self.update_layout)

        self.updates.setObjectName("group")

        self.update_widgets = {}

        self.update_text = QLabel(self.tr("No updates available"))
        self.update_layout.addWidget(self.update_text)
        self.update_text.setVisible(len(updates) == 0)

        for igame in updates:
            widget = UpdateWidget(core, igame, self)
            self.update_layout.addWidget(widget)
            self.update_widgets[igame.app_name] = widget
            widget.update.connect(self.update_game)
            if QSettings().value("auto_update", False, bool):
                self.update_game(igame.app_name, True)
                widget.update_button.setDisabled(True)

        self.layout.addStretch(1)

        self.setLayout(self.layout)

    def update_dl_queue(self, dl_queue):
        self.dl_queue = dl_queue

    def stop_download(self):
        self.thread.kill()

    def install_game(self, options: InstallOptions, from_update=False):

        status_queue = MPQueue()
        try:
            dlm, analysis, game, igame, repair, repair_file = self.core.prepare_download(
                app_name=options.app_name,
                base_path=options.path,
                force=options.force,
                no_install=options.download_only,
                status_q=status_queue,
                # max_shm=,
                max_workers=options.max_workers,
                # game_folder=,
                # disable_patching=,
                # override_manifest=,
                # override_old_manifest=,
                # override_base_url=,
                # platform_override=,
                # file_prefix_filter=,
                # file_exclude_filter=,
                # file_install_tag=,
                # dl_optimizations=,
                # dl_timeout=,
                repair=options.repair,
                # repair_use_latest=,
                ignore_space_req=options.ignore_free_space,
                # disable_delta=,
                # override_delta_manifest=,
                # reset_sdl=,
                sdl_prompt=self.sdl_prompt)
        except Exception as e:
            QMessageBox.warning(self, self.tr("Error preparing download"),
                                str(e))
            return

        if not analysis.dl_size:
            QMessageBox.information(self, "Warning", self.tr("Download size is 0. Game already exists"))
            return

        # Information
        if not from_update:
            if not InstallInfoDialog(dl_size=analysis.dl_size, install_size=analysis.install_size).get_accept():
                self.finished.emit(False)
                return

        if self.active_game is None:
            self.start_installation(dlm, game, status_queue, igame, repair_file, options, analysis)
        else:
            self.dl_queue.append((dlm, game, status_queue, igame, repair_file, options, analysis))
            self.queue_widget.update_queue(self.dl_queue)

    def start_installation(self, dlm, game, status_queue, igame, repair_file, options: InstallOptions, analysis):
        print("start installation", game.app_title)
        if self.dl_queue:
            self.dl_queue.pop(0)
            self.queue_widget.update_queue(self.dl_queue)
        self.active_game = game
        self.thread = DownloadThread(dlm, self.core, status_queue, igame, options.repair, repair_file)
        self.thread.status.connect(self.status)
        self.thread.statistics.connect(self.statistics)
        self.thread.start()
        self.kill_button.setDisabled(False)
        self.analysis = analysis
        self.installing_game.setText(self.tr("Installing Game: ") + self.active_game.app_title)

    def sdl_prompt(self, app_name: str = '', title: str = '') -> list:
        sdl = QDialog()
        sdl.setWindowTitle('Select Additional Downloads')

        layout = QVBoxLayout(sdl)
        sdl.setLayout(layout)

        pack_list = QListWidget()
        layout.addWidget(pack_list)

        done = QPushButton(text='Done')
        done.clicked.connect(sdl.accept)
        layout.addWidget(done)

        tags = ['']
        if '__required' in games[app_name]:
            tags.extend(games[app_name]['__required']['tags'])

        # add available additional downloads to list
        pack_list.addItems([tag + ': ' + info['name'] for tag, info in games[app_name].items() if tag != '__required'])

        # enable checkboxes
        for i in range(len(pack_list)):
            item = pack_list.item(i)
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setCheckState(Qt.Unchecked)

        sdl.exec_()

        # read checkboxes states
        for i in range(len(pack_list)):
            item = pack_list.item(i)
            if item.checkState() == Qt.Checked:
                tag = item.text().split(':')[0]
                tags.extend(games[app_name][tag]['tags'])

        return tags

    def status(self, text):
        if text == "dl_finished":
            pass
        elif text == "finish":
            self.installing_game.setText(self.tr("Download finished. Reload library"))
            if QSettings().value("notification", True, bool):
                try:
                    from notifypy import Notify
                except ModuleNotFoundError:
                    logger.warning("No Notification Module found")
                else:
                    notification = Notify()
                    notification.title = self.tr("Installation finished")
                    notification.message = self.tr("Finished Download of game {}").format(self.active_game.app_title)
                    notification.send()
            # QMessageBox.information(self, "Info", "Download finished")
            logger.info("Download finished: " + self.active_game.app_title)

            if self.dl_queue:
                if self.dl_queue[0][1] == self.active_game.app_name:
                    self.dl_queue.pop(0)
                    self.queue_widget.update_queue(self.dl_queue)

            if self.active_game.app_name in self.update_widgets.keys():
                self.update_widgets[self.active_game.app_name].setVisible(False)
                self.update_widgets.pop(self.active_game.app_name)
                if len(self.update_widgets) == 0:
                    self.update_text.setVisible(True)

            self.active_game = None

            for i in self.update_widgets.values():
                i.update_button.setDisabled(False)

            self.finished.emit(True)
            self.reset_infos()

            if len(self.dl_queue) != 0:
                self.start_installation(*self.dl_queue[0])
            else:
                self.queue_widget.update_queue(self.dl_queue)

        elif text[:5] == "error":
            QMessageBox.warning(self, "warn", "Download error: " + text[6:])

        elif text == "stop":
            self.reset_infos()
            self.active_game = None
            self.finished.emit(False)
            if self.dl_queue:
                self.start_installation(*self.dl_queue[0])

    def reset_infos(self):
        self.kill_button.setDisabled(True)
        self.installing_game.setText(self.tr("Installing Game: No active download"))
        self.prog_bar.setValue(0)
        self.dl_speed.setText("")
        self.time_left.setText("")
        self.cache_used.setText("")
        self.downloaded.setText("")
        self.analysis = None

    def statistics(self, ui_update: UIUpdate):
        self.prog_bar.setValue(ui_update.progress)
        self.dl_speed.setText(self.tr("Download speed") + f": {ui_update.download_speed / 1024 / 1024:.02f}MB/s")
        self.cache_used.setText(self.tr("Cache used") + f": {ui_update.cache_usage / 1024 / 1024:.02f}MB")
        self.downloaded.setText(
            self.tr("Downloaded") + f": {get_size(ui_update.total_downloaded)} / {get_size(self.analysis.dl_size)}")
        self.time_left.setText(self.tr("Time left: ") + self.get_time(ui_update.estimated_time_left))

    def get_time(self, seconds: int) -> str:
        return str(datetime.timedelta(seconds=seconds))

    def update_game(self, app_name: str, auto=False):
        logger.info("Update " + app_name)
        if not auto:
            infos = InstallDialog(app_name, self.core, True).get_information()
        else:
            self.install_game(InstallOptions(app_name=app_name), True)
            return
        if infos != 0:
            path, max_workers, force, ignore_free_space = infos
            self.install_game(InstallOptions(app_name=app_name, max_workers=max_workers, path=path,
                                             force=force, ignore_free_space=ignore_free_space), True)


class UpdateWidget(QWidget):
    update = pyqtSignal(str)

    def __init__(self, core: LegendaryCore, game: InstalledGame, parent):
        super(UpdateWidget, self).__init__(parent=parent)
        self.core = core
        self.game = game

        self.layout = QVBoxLayout()
        self.title = QLabel(self.game.title)
        self.layout.addWidget(self.title)

        self.update_button = QPushButton(self.tr("Update Game"))
        self.update_button.clicked.connect(self.update_game)
        self.layout.addWidget(self.update_button)

        self.setLayout(self.layout)

    def update_game(self):
        self.update_button.setDisabled(True)
        self.update.emit(self.game.app_name)
