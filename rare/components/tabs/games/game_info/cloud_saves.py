import os
from logging import getLogger

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
from rare.shared import LegendaryCoreSingleton
from rare.shared.workers.wine_resolver import WineResolver
from rare.ui.components.tabs.games.game_info.cloud_widget import Ui_CloudWidget
from rare.ui.components.tabs.games.game_info.sync_widget import Ui_SyncWidget
from rare.utils.misc import icon
from rare.widgets.indicator_edit import PathEdit, IndicatorReasonsCommon
from rare.widgets.side_tab import SideTabContents

logger = getLogger("CloudWidget")


class CloudSaves(QWidget, SideTabContents):
    def __init__(self, parent=None):
        super(CloudSaves, self).__init__(parent=parent)

        self.sync_widget = QWidget(self)
        self.sync_ui = Ui_SyncWidget()
        self.sync_ui.setupUi(self.sync_widget)

        self.info_label = QLabel(self.tr("<b>This game doesn't support cloud saves</b>"))

        self.core = LegendaryCoreSingleton()
        self.settings = QSettings()

        self.sync_ui.icon_local.setPixmap(icon("mdi.harddisk", "fa.desktop").pixmap(128, 128))
        self.sync_ui.icon_remote.setPixmap(icon("mdi.cloud-outline", "ei.cloud").pixmap(128, 128))

        self.sync_ui.upload_button.clicked.connect(self.upload)
        self.sync_ui.download_button.clicked.connect(self.download)
        self.rgame: RareGame = None

        self.cloud_widget = QGroupBox(self)
        self.cloud_ui = Ui_CloudWidget()
        self.cloud_ui.setupUi(self.cloud_widget)

        self.cloud_save_path_edit = PathEdit(
            "",
            file_type=QFileDialog.DirectoryOnly,
            placeholder=self.tr('Use "Calculate path" or "Browse" ...'),
            edit_func=lambda text: (True, text, None)
            if os.path.exists(text)
            else (False, text, IndicatorReasonsCommon.DIR_NOT_EXISTS),
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

    def upload(self):
        self.sync_ui.upload_button.setDisabled(True)
        self.sync_ui.download_button.setDisabled(True)
        self.rgame.upload_saves()

    def download(self):
        self.sync_ui.upload_button.setDisabled(True)
        self.sync_ui.download_button.setDisabled(True)
        self.rgame.download_saves()

    def compute_save_path(self):
        if self.rgame.is_installed and self.rgame.game.supports_cloud_saves:
            try:
                new_path = self.core.get_save_path(self.rgame.app_name)
                if not os.path.exists(new_path):
                    raise ValueError(f'Path "{new_path}" does not exist.')
            except Exception as e:
                logger.warning(str(e))
                resolver = WineResolver(self.core, self.rgame.raw_save_path, self.rgame.app_name)
                if not resolver.wine_env.get("WINEPREFIX"):
                    self.cloud_save_path_edit.setText("")
                    QMessageBox.warning(self, "Warning", "No wine prefix selected. Please set it in settings")
                    return
                self.cloud_save_path_edit.setText(self.tr("Loading"))
                self.cloud_save_path_edit.setDisabled(True)
                self.compute_save_path_button.setDisabled(True)

                app_name = self.rgame.app_name[:]
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
                        None,
                        "Error",
                        self.tr("Error while launching {}. No permission to create {}").format(
                            self.rgame.title, path
                        ),
                    )
                    return
            if not path:
                self.cloud_save_path_edit.setText("")
                return
            self.cloud_save_path_edit.setText(path)
        elif path:
            igame = self.core.get_installed_game(app_name)
            igame.save_path = path
            self.core.lgd.set_installed_game(app_name, igame)

    def save_save_path(self, text):
        self.rgame.save_path = text

    def __update_widget(self):
        supports_saves = self.rgame.igame is not None and (
                self.rgame.game.supports_cloud_saves or self.rgame.game.supports_mac_cloud_saves
        )
        self.sync_widget.setEnabled(bool(supports_saves and self.rgame.save_path )) # and not self.rgame.is_save_up_to_date))
        self.cloud_widget.setEnabled(supports_saves)
        self.info_label.setVisible(not supports_saves)
        if not supports_saves:
            self.sync_ui.date_info_local.setText("None")
            self.sync_ui.date_info_remote.setText("None")
            self.cloud_ui.cloud_sync.setChecked(False)
            self.cloud_save_path_edit.setText("")
            return

        button_disabled = self.rgame.state in [RareGame.State.RUNNING, RareGame.State.SYNCING]
        self.sync_ui.download_button.setDisabled(button_disabled)
        self.sync_ui.upload_button.setDisabled(button_disabled)

        status, (dt_local, dt_remote) = self.rgame.save_game_state

        newer = self.tr("Newer")
        self.sync_ui.age_label_local.setText(
            f"<b>{newer}</b>" if status == SaveGameStatus.LOCAL_NEWER else " "
        )
        self.sync_ui.age_label_remote.setText(
            f"<b>{newer}</b>" if status == SaveGameStatus.REMOTE_NEWER else " "
        )

        self.cloud_ui.cloud_sync.setChecked(
            self.settings.value(f"{self.rgame.app_name}/auto_sync_cloud", False, bool)
        )
        if self.rgame.save_path:
            self.cloud_save_path_edit.setText(self.rgame.save_path)
            self.sync_ui.date_info_local.setText(dt_local.strftime("%A, %d. %B %Y %X") if dt_local else "None")
            self.sync_ui.date_info_remote.setText(dt_remote.strftime("%A, %d. %B %Y %X") if dt_remote else "None")
        else:
            self.cloud_save_path_edit.setText("")

    def update_game(self, rgame: RareGame):
        if self.rgame:
            self.rgame.signals.widget.update.disconnect(self.__update_widget)

        self.rgame = rgame

        self.set_title.emit(rgame.title)
        rgame.signals.widget.update.connect(self.__update_widget)

        self.__update_widget()

