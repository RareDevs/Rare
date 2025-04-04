import os
import platform
from datetime import datetime
from logging import getLogger
from typing import Tuple

from PySide6.QtCore import QThreadPool, QSettings, Slot
from PySide6.QtWidgets import (
    QWidget,
    QFileDialog,
    QLabel,
    QPushButton,
    QSizePolicy,
    QMessageBox,
    QGroupBox,
    QVBoxLayout,
    QSpacerItem, QFormLayout,
)
from legendary.models.game import SaveGameStatus

from rare.models.game import RareGame
from rare.models.options import options
from rare.shared import RareCore
from rare.shared.workers.wine_resolver import WineSavePathResolver
from rare.ui.components.tabs.library.details.cloud_settings_widget import Ui_CloudSettingsWidget
from rare.ui.components.tabs.library.details.cloud_sync_widget import Ui_CloudSyncWidget
from rare.utils.metrics import timelogger
from rare.utils.misc import qta_icon
from rare.widgets.indicator_edit import PathEdit, IndicatorReasonsCommon
from rare.widgets.loading_widget import LoadingWidget
from rare.widgets.side_tab import SideTabContents

logger = getLogger("CloudSaves")


class CloudSaves(QWidget, SideTabContents):
    def __init__(self, parent=None):
        super(CloudSaves, self).__init__(parent=parent)

        self.sync_widget = QWidget(self)
        self.sync_ui = Ui_CloudSyncWidget()
        self.sync_ui.setupUi(self.sync_widget)

        self.rcore = RareCore.instance()
        self.core = RareCore.instance().core()
        self.settings = QSettings()

        self.sync_ui.icon_local.setPixmap(qta_icon("mdi.harddisk", "fa5s.desktop").pixmap(128, 128))
        self.sync_ui.icon_remote.setPixmap(qta_icon("mdi.cloud-outline", "fa5s.cloud").pixmap(128, 128))

        self.sync_ui.upload_button.clicked.connect(self.upload)
        self.sync_ui.download_button.clicked.connect(self.download)

        self.loading_widget = LoadingWidget(parent=self.sync_widget)
        self.loading_widget.setVisible(False)

        self.rgame: RareGame = None

        self.cloud_widget = QGroupBox(self)
        self.cloud_ui = Ui_CloudSettingsWidget()
        self.cloud_ui.setupUi(self.cloud_widget)

        self.cloud_save_path_edit = PathEdit(
            path="",
            file_mode=QFileDialog.FileMode.Directory,
            placeholder=self.tr('Use "Calculate path" or "Browse" ...'),
            edit_func=self.edit_save_path,
            save_func=self.save_save_path,
        )
        self.cloud_ui.main_layout.setWidget(
            self.cloud_ui.main_layout.getWidgetPosition(self.cloud_ui.path_label)[0],
            QFormLayout.ItemRole.FieldRole,
            self.cloud_save_path_edit
        )

        self.compute_save_path_button = QPushButton(qta_icon("fa.magic", "fa5s.magic"), self.tr("Resolve path"))
        self.compute_save_path_button.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.compute_save_path_button.clicked.connect(self.compute_save_path)
        self.cloud_ui.main_layout.addRow(None, self.compute_save_path_button)

        self.cloud_ui.sync_check.stateChanged.connect(self.__on_sync_check_changed)

        self.info_label = QLabel(parent=self)

        layout = QVBoxLayout(self)
        layout.addWidget(self.sync_widget)
        layout.addWidget(self.cloud_widget)
        layout.addWidget(self.info_label)
        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding))

    @staticmethod
    def edit_save_path(text: str) -> Tuple[bool, str, int]:
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
                with timelogger(logger, "Detecting save path"):
                    new_path = self.core.get_save_path(self.rgame.app_name)
                if platform.system() != "Windows" and not os.path.exists(new_path):
                    raise ValueError(f'Path "{new_path}" does not exist.')
            except Exception as e:
                logger.warning(str(e))
                resolver = WineSavePathResolver(self.core, self.rgame)
                # if not resolver.environ.get("WINEPREFIX"):
                #     del resolver
                #     self.cloud_save_path_edit.setText("")
                #     QMessageBox.warning(self, "Warning", "No wine prefix selected. Please set it in settings")
                #     return
                self.cloud_save_path_edit.setText(self.tr("Loading..."))
                self.cloud_save_path_edit.setDisabled(True)
                self.compute_save_path_button.setDisabled(True)

                resolver.signals.result_ready.connect(self.__on_wine_resolver_result)
                QThreadPool.globalInstance().start(resolver)
                return
            else:
                self.cloud_save_path_edit.setText(new_path)

    @Slot()
    def __on_sync_check_changed(self):
        if self.settings.value(*options.auto_sync_cloud) == self.cloud_ui.sync_check.isChecked():
            self.settings.remove(f"{self.rgame.app_name}/{options.auto_sync_cloud.key}")
        else:
            self.settings.setValue(f"{self.rgame.app_name}/auto_sync_cloud", self.cloud_ui.sync_check.isChecked())

    @Slot(str, str)
    def __on_wine_resolver_result(self, path, app_name):
        logger.info("Wine resolver finished for %s", app_name)
        logger.info("Computed save path: %s", path)
        if app_name == self.rgame.app_name:
            self.cloud_save_path_edit.setDisabled(False)
            self.compute_save_path_button.setDisabled(False)
            if path and not os.path.exists(path):
                try:
                    os.makedirs(path, exist_ok=True)
                except PermissionError:
                    self.cloud_save_path_edit.setText("")
                    QMessageBox.warning(
                        self,
                        self.tr("Error - {}").format(self.rgame.app_title),
                        self.tr(
                            "Error while calculating path for <b>{}</b>. Insufficient permissions to create <b>{}</b>"
                        ).format(self.rgame.app_title, path),
                    )
                    return
            if not path:
                self.cloud_save_path_edit.setText("")
                return
            self.cloud_save_path_edit.setText(path)

    def __update_widget(self):
        supports_saves = self.rgame.game.supports_cloud_saves or self.rgame.game.supports_mac_cloud_saves
        saves_ready = self.rgame.igame is not None and supports_saves

        self.sync_widget.setEnabled(
            bool(saves_ready and self.rgame.save_path))  # and not self.rgame.is_save_up_to_date))

        self.cloud_widget.setEnabled(saves_ready)
        info_text = (
            self.tr("<b>This game doesn't support cloud saves</b>") if not supports_saves else (
                self.tr("<b>This game supports cloud saves, but it's not installed</b>")
                if self.rgame.igame is None else ""
            )
        )
        self.info_label.setText(info_text)
        self.info_label.setVisible(bool(info_text))
        if not saves_ready:
            self.sync_ui.date_info_local.setText("None")
            self.sync_ui.age_label_local.setText("None")
            self.sync_ui.date_info_remote.setText("None")
            self.sync_ui.age_label_remote.setText("None")
            self.cloud_ui.sync_check.setChecked(False)
            self.cloud_save_path_edit.setText("")
            return

        status, (dt_local, dt_remote) = self.rgame.save_game_state

        local_tz = datetime.now().astimezone().tzinfo
        self.sync_ui.date_info_local.setText(
            dt_local.astimezone(local_tz).strftime("%A, %d %B %Y %X") if dt_local else "None")
        self.sync_ui.date_info_remote.setText(
            dt_remote.astimezone(local_tz).strftime("%A, %d %B %Y %X") if dt_remote else "None")

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

        self.cloud_ui.sync_check.blockSignals(True)
        self.cloud_ui.sync_check.setChecked(self.rgame.auto_sync_saves)
        self.cloud_ui.sync_check.blockSignals(False)

        self.cloud_save_path_edit.setText(self.rgame.save_path if self.rgame.save_path else "")
        if platform.system() == "Windows" and not self.rgame.save_path:
            self.compute_save_path()

    def update_game(self, rgame: RareGame):
        if self.rgame:
            self.rgame.signals.widget.update.disconnect(self.__update_widget)

        self.rgame = rgame

        self.set_title.emit(rgame.app_title)
        rgame.signals.widget.update.connect(self.__update_widget)

        self.__update_widget()
