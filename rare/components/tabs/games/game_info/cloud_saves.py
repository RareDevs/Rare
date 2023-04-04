import os
import platform
from logging import getLogger
from typing import Tuple

from PyQt5.QtCore import QThreadPool, QSettings
from PyQt5.QtWidgets import (
    QWidget,
    QFileDialog,
    QLabel,
    QPushButton,
    QSizePolicy,
    QMessageBox,
    QGroupBox,
    QVBoxLayout,
    QSpacerItem,
)
from legendary.models.game import SaveGameStatus

from rare.models.game import RareGame
from rare.shared import RareCore
from rare.shared.workers.wine_resolver import WineResolver
from rare.ui.components.tabs.games.game_info.cloud_widget import Ui_CloudWidget
from rare.ui.components.tabs.games.game_info.sync_widget import Ui_SyncWidget
from rare.utils.misc import icon
from rare.widgets.indicator_edit import PathEdit, IndicatorReasonsCommon
from rare.widgets.loading_widget import LoadingWidget
from rare.widgets.side_tab import SideTabContents

logger = getLogger("CloudWidget")


class CloudSaves(QWidget, SideTabContents):
    def __init__(self, parent=None):
        super(CloudSaves, self).__init__(parent=parent)

        self.sync_widget = QWidget(self)
        self.sync_ui = Ui_SyncWidget()
        self.sync_ui.setupUi(self.sync_widget)

        self.info_label = QLabel(self.tr("<b>This game doesn't support cloud saves</b>"))

        self.rcore = RareCore.instance()
        self.core = RareCore.instance().core()
        self.settings = QSettings()

        self.sync_ui.icon_local.setPixmap(icon("mdi.harddisk", "fa.desktop").pixmap(128, 128))
        self.sync_ui.icon_remote.setPixmap(icon("mdi.cloud-outline", "ei.cloud").pixmap(128, 128))

        self.sync_ui.upload_button.clicked.connect(self.upload)
        self.sync_ui.download_button.clicked.connect(self.download)

        self.loading_widget = LoadingWidget(parent=self.sync_widget)
        self.loading_widget.setVisible(False)

        self.rgame: RareGame = None

        self.cloud_widget = QGroupBox(self)
        self.cloud_ui = Ui_CloudWidget()
        self.cloud_ui.setupUi(self.cloud_widget)

        self.cloud_save_path_edit = PathEdit(
            "",
            file_mode=QFileDialog.DirectoryOnly,
            placeholder=self.tr('Use "Calculate path" or "Browse" ...'),
            edit_func=self.edit_save_path,
            save_func=self.save_save_path,
        )
        self.cloud_ui.cloud_layout.addRow(QLabel(self.tr("Save path")), self.cloud_save_path_edit)

        self.compute_save_path_button = QPushButton(icon("fa.magic"), self.tr("Calculate path"))
        self.compute_save_path_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.compute_save_path_button.clicked.connect(self.compute_save_path)
        self.cloud_ui.cloud_layout.addRow(None, self.compute_save_path_button)

        self.cloud_ui.cloud_sync.stateChanged.connect(
            lambda: self.settings.setValue(
                f"{self.rgame.app_name}/auto_sync_cloud", self.cloud_ui.cloud_sync.isChecked()
            )
        )

        layout = QVBoxLayout(self)
        layout.addWidget(self.sync_widget)
        layout.addWidget(self.cloud_widget)
        layout.addWidget(self.info_label)
        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Fixed, QSizePolicy.Expanding))

    def edit_save_path(self, text: str) -> Tuple[bool, str, int]:
        if platform.system() != "Windows":
            if os.path.exists(text):
                return True, text, IndicatorReasonsCommon.VALID
            else:
                return False, text, IndicatorReasonsCommon.DIR_NOT_EXISTS
        return True, text, IndicatorReasonsCommon.VALID

    def save_save_path(self, text: str):
        if text != self.rgame.save_path:
            self.rgame.save_path = text

    def upload(self):
        self.sync_widget.setEnabled(False)
        self.loading_widget.setVisible(True)
        self.rgame.upload_saves()

    def download(self):
        self.sync_widget.setEnabled(False)
        self.loading_widget.setVisible(True)
        self.rgame.download_saves()

    def compute_save_path(self):
        if self.rgame.is_installed and self.rgame.game.supports_cloud_saves:
            try:
                new_path = self.core.get_save_path(self.rgame.app_name)
                if platform.system() != "Windows" and not os.path.exists(new_path):
                    raise ValueError(f'Path "{new_path}" does not exist.')
            except Exception as e:
                logger.warning(str(e))
                resolver = WineResolver(self.core, self.rgame.raw_save_path, self.rgame.app_name)
                if not resolver.wine_env.get("WINEPREFIX"):
                    self.cloud_save_path_edit.setText("")
                    QMessageBox.warning(self, "Warning", "No wine prefix selected. Please set it in settings")
                    return
                self.cloud_save_path_edit.setText(self.tr("Loading..."))
                self.cloud_save_path_edit.setDisabled(True)
                self.compute_save_path_button.setDisabled(True)

                app_name = self.rgame.app_name
                resolver.signals.result_ready.connect(lambda x: self.wine_resolver_finished(x, app_name))
                QThreadPool.globalInstance().start(resolver)
                return
            else:
                self.cloud_save_path_edit.setText(new_path)

    def wine_resolver_finished(self, path, app_name):
        logger.info(f"Wine resolver finished for {app_name}. Computed save path: {path}")
        if app_name == self.rgame.app_name:
            self.cloud_save_path_edit.setDisabled(False)
            self.compute_save_path_button.setDisabled(False)
            if path and not os.path.exists(path):
                try:
                    os.makedirs(path)
                except PermissionError:
                    self.cloud_save_path_edit.setText("")
                    QMessageBox.warning(
                        self,
                        self.tr("Error - {}").format(self.rgame.title),
                        self.tr(
                            "Error while calculating path for <b>{}</b>. Insufficient permisions to create <b>{}</b>"
                        ).format(self.rgame.title, path),
                    )
                    return
            if not path:
                self.cloud_save_path_edit.setText("")
                return
            self.cloud_save_path_edit.setText(path)
        elif path:
            self.rcore.get_game(app_name).save_path = path

    def __update_widget(self):
        supports_saves = self.rgame.igame is not None and (
                self.rgame.game.supports_cloud_saves or self.rgame.game.supports_mac_cloud_saves
        )

        self.sync_widget.setEnabled(
            bool(supports_saves and self.rgame.save_path))  # and not self.rgame.is_save_up_to_date))

        self.cloud_widget.setEnabled(supports_saves)
        self.info_label.setVisible(not supports_saves)
        if not supports_saves:
            self.sync_ui.date_info_local.setText("None")
            self.sync_ui.age_label_local.setText("None")
            self.sync_ui.date_info_remote.setText("None")
            self.sync_ui.age_label_remote.setText("None")
            self.cloud_ui.cloud_sync.setChecked(False)
            self.cloud_save_path_edit.setText("")
            return

        status, (dt_local, dt_remote) = self.rgame.save_game_state

        self.sync_ui.date_info_local.setText(
            dt_local.strftime("%A, %d. %B %Y %X") if dt_local and self.rgame.save_path else "None"
        )
        self.sync_ui.date_info_remote.setText(
            dt_remote.strftime("%A, %d. %B %Y %X") if dt_remote and self.rgame.save_path else "None"
        )

        newer = self.tr("Newer")
        self.sync_ui.age_label_local.setText(
            f"<b>{newer}</b>" if status == SaveGameStatus.LOCAL_NEWER else " "
        )
        self.sync_ui.age_label_remote.setText(
            f"<b>{newer}</b>" if status == SaveGameStatus.REMOTE_NEWER else " "
        )

        button_disabled = self.rgame.state in [RareGame.State.RUNNING, RareGame.State.SYNCING]
        self.sync_widget.setDisabled(button_disabled)
        if self.rgame.state == RareGame.State.SYNCING:
            self.loading_widget.start()
        else:
            self.loading_widget.stop()

        self.sync_ui.upload_button.setDisabled(not dt_local)
        self.sync_ui.download_button.setDisabled(not dt_remote)

        self.cloud_ui.cloud_sync.blockSignals(True)
        self.cloud_ui.cloud_sync.setChecked(self.rgame.auto_sync_saves)
        self.cloud_ui.cloud_sync.blockSignals(False)
        self.cloud_save_path_edit.setText(self.rgame.save_path if self.rgame.save_path else "")

    def update_game(self, rgame: RareGame):
        if self.rgame:
            self.rgame.signals.widget.update.disconnect(self.__update_widget)

        self.rgame = rgame

        self.set_title.emit(rgame.title)
        rgame.signals.widget.update.connect(self.__update_widget)

        self.__update_widget()
