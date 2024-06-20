import os
import platform
import shutil
from logging import getLogger
from typing import Optional

from PySide6.QtCore import (
    Qt,
    Slot,
    Signal,
)
from PySide6.QtWidgets import (
    QWidget,
    QMessageBox,
)

from rare.models.install import SelectiveDownloadsModel, MoveGameModel
from rare.components.dialogs.selective_dialog import SelectiveDialog
from rare.models.game import RareGame
from rare.shared import RareCore
from rare.shared.workers import VerifyWorker, MoveWorker
from rare.ui.components.tabs.games.game_info.details import Ui_GameDetails
from rare.utils.misc import format_size, qta_icon, style_hyperlink
from rare.widgets.image_widget import ImageWidget, ImageSize
from rare.widgets.side_tab import SideTabContents
from rare.components.dialogs.move_dialog import MoveDialog, is_game_dir

logger = getLogger("GameInfo")


class GameDetails(QWidget, SideTabContents):
    # str: app_name
    import_clicked = Signal(str)

    def __init__(self, parent=None):
        super(GameDetails, self).__init__(parent=parent)
        self.ui = Ui_GameDetails()
        self.ui.setupUi(self)
        # lk: set object names for CSS properties
        self.ui.install_button.setObjectName("InstallButton")
        self.ui.modify_button.setObjectName("InstallButton")
        self.ui.uninstall_button.setObjectName("UninstallButton")

        self.ui.install_button.setIcon(qta_icon("ri.install-line"))
        self.ui.import_button.setIcon(qta_icon("mdi.application-import"))

        self.ui.modify_button.setIcon(qta_icon("fa.gear"))
        self.ui.verify_button.setIcon(qta_icon("fa.check"))
        self.ui.repair_button.setIcon(qta_icon("fa.wrench"))
        self.ui.move_button.setIcon(qta_icon("mdi.folder-move-outline"))
        self.ui.uninstall_button.setIcon(qta_icon("ri.uninstall-line"))

        self.rcore = RareCore.instance()
        self.core = RareCore.instance().core()
        self.args = RareCore.instance().args()
        # self.image_manager = RareCore.instance().image_manager()

        self.rgame: Optional[RareGame] = None

        self.image = ImageWidget(self)
        self.image.setFixedSize(ImageSize.DisplayTall)
        self.ui.left_layout.insertWidget(0, self.image, alignment=Qt.AlignmentFlag.AlignTop)

        self.ui.install_button.clicked.connect(self.__on_install)
        self.ui.import_button.clicked.connect(self.__on_import)
        self.ui.modify_button.clicked.connect(self.__on_modify)
        self.ui.verify_button.clicked.connect(self.__on_verify)
        self.ui.repair_button.clicked.connect(self.__on_repair)
        self.ui.move_button.clicked.connect(self.__on_move)
        self.ui.uninstall_button.clicked.connect(self.__on_uninstall)

        self.steam_grade_ratings = {
            "platinum": self.tr("Platinum"),
            "gold": self.tr("Gold"),
            "silver": self.tr("Silver"),
            "bronze": self.tr("Bronze"),
            "borked": self.tr("Borked"),
            "fail": self.tr("Failed to get rating"),
            "pending": self.tr("Loading..."),
            "na": self.tr("Not applicable"),
        }

        # lk: hide unfinished things
        self.ui.tags_group.setVisible(False)
        self.ui.requirements_group.setVisible(False)

    @Slot()
    def __on_install(self):
        if self.rgame.is_non_asset:
            self.rgame.launch()
        else:
            self.rgame.install()

    @Slot()
    def __on_import(self):
        self.import_clicked.emit(self.rgame.app_name)

    @Slot()
    def __on_uninstall(self):
        """ This method is to be called from the button only """
        self.rgame.uninstall()

    @Slot()
    def __on_modify(self):
        """ This method is to be called from the button only """
        self.rgame.modify()

    @Slot()
    def __on_repair(self):
        """ This method is to be called from the button only """
        repair_file = os.path.join(self.core.lgd.get_tmp_path(), f"{self.rgame.app_name}.repair")
        if not os.path.exists(repair_file):
            QMessageBox.warning(
                self,
                self.tr("Error - {}").format(self.rgame.app_title),
                self.tr(
                    "Repair file does not exist or game does not need a repair. Please verify game first"
                ),
            )
            return
        self.repair_game(self.rgame)

    def repair_game(self, rgame: RareGame):
        rgame.update_game()
        ans = False
        if rgame.has_update:
            ans = QMessageBox.question(
                self,
                self.tr("Repair and update? - {}").format(self.rgame.app_title),
                self.tr(
                    "There is an update for <b>{}</b> from <b>{}</b> to <b>{}</b>. "
                    "Do you want to update the game while repairing it?"
                ).format(rgame.app_title, rgame.version, rgame.remote_version),
            ) == QMessageBox.StandardButton.Yes
        rgame.repair(repair_and_update=ans)

    @Slot(RareGame, str)
    def __on_worker_error(self, rgame: RareGame, message: str):
        QMessageBox.warning(
            self,
            self.tr("Error - {}").format(rgame.app_title),
            message
        )

    @Slot()
    def __on_verify(self):
        """ This method is to be called from the button only """
        if not os.path.exists(self.rgame.igame.install_path):
            logger.error(f"Installation path {self.rgame.igame.install_path} for {self.rgame.app_title} does not exist")
            QMessageBox.warning(
                self,
                self.tr("Error - {}").format(self.rgame.app_title),
                self.tr("Installation path for <b>{}</b> does not exist. Cannot continue.").format(self.rgame.app_title),
            )
            return
        if self.rgame.sdl_name is not None:
            selective_dialog = SelectiveDialog(
                self.rgame, parent=self
            )
            selective_dialog.result_ready.connect(self.verify_game)
            selective_dialog.open()
        else:
            self.verify_game(self.rgame)

    @Slot(RareGame, SelectiveDownloadsModel)
    def verify_game(self, rgame: RareGame, sdl_model: SelectiveDownloadsModel = None):
        if sdl_model is not None:
            if not sdl_model.accepted or sdl_model.install_tag is None:
                return
            self.core.lgd.config.set(rgame.app_name, "install_tags", ','.join(sdl_model.install_tag))
            self.core.lgd.save_config()
        worker = VerifyWorker(self.core, self.args, rgame)
        worker.signals.progress.connect(self.__on_verify_progress)
        worker.signals.result.connect(self.__on_verify_result)
        worker.signals.error.connect(self.__on_worker_error)
        self.rcore.enqueue_worker(rgame, worker)

    @Slot(RareGame, int, int, float, float)
    def __on_verify_progress(self, rgame: RareGame, num, total, percentage, speed):
        # lk: the check is NOT REQUIRED because signals are disconnected but protect against it anyway
        if rgame is not self.rgame:
            return
        self.ui.verify_progress.setValue(num * 100 // total)

    @Slot(RareGame, bool, int, int)
    def __on_verify_result(self, rgame: RareGame, success, failed, missing):
        self.ui.repair_button.setDisabled(success)
        if success:
            QMessageBox.information(
                self,
                self.tr("Summary - {}").format(rgame.app_title),
                self.tr("<b>{}</b> has been verified successfully. "
                        "No missing or corrupt files found").format(rgame.app_title),
            )
        else:
            ans = QMessageBox.question(
                self,
                self.tr("Summary - {}").format(rgame.app_title),
                self.tr(
                    "<b>{}</b> failed verification, <b>{}</b> file(s) corrupted, <b>{}</b> file(s) are missing. "
                    "Do you want to repair them?"
                ).format(rgame.app_title, failed, missing),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if ans == QMessageBox.StandardButton.Yes:
                self.repair_game(rgame)

    @Slot()
    def __on_move(self):
        """ This method is to be called from the button only """
        move_dialog = MoveDialog(self.rgame, parent=self)
        move_dialog.result_ready.connect(self.move_game)
        move_dialog.open()

    def move_game(self, rgame: RareGame, model: MoveGameModel):
        if not model.accepted:
            return

        new_install_path = os.path.join(model.target_path, os.path.basename(self.rgame.install_path))
        dir_exists = False
        if os.path.isdir(new_install_path):
            dir_exists = is_game_dir(self.rgame.install_path, new_install_path)

        if not dir_exists:
            for item in os.listdir(model.target_path):
                if os.path.basename(self.rgame.install_path) in os.path.basename(item):
                    ans = QMessageBox.question(
                        self,
                        self.tr("Move game? - {}").format(self.rgame.app_title),
                        self.tr(
                            "Destination <b>{}</b> already exists. "
                            "Are you sure you want to overwrite it?"
                        ).format(new_install_path),
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.Yes,
                    )

                    if ans == QMessageBox.StandardButton.Yes:
                        if os.path.isdir(new_install_path):
                            shutil.rmtree(new_install_path)
                        else:
                            os.remove(new_install_path)
                    else:
                        return

        worker = MoveWorker(
            self.core, rgame=rgame, dst_path=model.target_path, dst_exists=dir_exists
        )
        worker.signals.progress.connect(self.__on_move_progress)
        worker.signals.result.connect(self.__on_move_result)
        worker.signals.error.connect(self.__on_worker_error)
        self.rcore.enqueue_worker(self.rgame, worker)

    @Slot(RareGame, int, object, object)
    def __on_move_progress(self, rgame: RareGame, progress: int, total_size: int, copied_size: int):
        # lk: the check is NOT REQUIRED because signals are disconnected but protect against it anyway
        if rgame is not self.rgame:
            return
        self.ui.move_progress.setValue(progress)

    @Slot(RareGame, str)
    def __on_move_result(self, rgame: RareGame, dst_path: str):
        QMessageBox.information(
            self,
            self.tr("Summary - {}").format(rgame.app_title),
            self.tr("<b>{}</b> successfully moved to <b>{}<b>.").format(rgame.app_title, dst_path),
        )

    @Slot()
    def __update_widget(self):
        """ React to state updates from RareGame """
        self.image.setPixmap(self.rgame.get_pixmap(ImageSize.DisplayTall, True))

        self.ui.lbl_version.setDisabled(self.rgame.is_non_asset)
        self.ui.version.setDisabled(self.rgame.is_non_asset)
        self.ui.version.setText(
            self.rgame.version if not self.rgame.is_non_asset else "N/A"
        )

        self.ui.lbl_install_size.setEnabled(bool(self.rgame.install_size))
        self.ui.install_size.setEnabled(bool(self.rgame.install_size))
        self.ui.install_size.setText(
            format_size(self.rgame.install_size) if self.rgame.install_size else "N/A"
        )

        self.ui.lbl_install_path.setEnabled(bool(self.rgame.install_path))
        self.ui.install_path.setEnabled(bool(self.rgame.install_path))
        self.ui.install_path.setText(
            self.rgame.install_path if self.rgame.install_path else "N/A"
        )

        self.ui.platform.setText(
            self.rgame.igame.platform
            if self.rgame.is_installed and not self.rgame.is_non_asset
            else self.rgame.default_platform
        )

        self.ui.lbl_grade.setDisabled(
            self.rgame.is_unreal or platform.system() == "Windows"
        )
        self.ui.grade.setDisabled(
            self.rgame.is_unreal or platform.system() == "Windows"
        )
        self.ui.grade.setText(
            style_hyperlink(
                f"https://www.protondb.com/app/{self.rgame.steam_appid}",
                self.steam_grade_ratings[self.rgame.steam_grade()]
            )
        )

        self.ui.install_button.setEnabled(
            (not self.rgame.is_installed or self.rgame.is_non_asset) and self.rgame.is_idle
        )

        self.ui.import_button.setEnabled(
            (not self.rgame.is_installed or self.rgame.is_non_asset) and self.rgame.is_idle
        )

        self.ui.modify_button.setEnabled(
            self.rgame.is_installed
            and (not self.rgame.is_non_asset)
            and self.rgame.is_idle
            and self.rgame.sdl_name is not None
        )

        self.ui.verify_button.setEnabled(
            self.rgame.is_installed and (not self.rgame.is_non_asset) and self.rgame.is_idle
        )
        self.ui.verify_progress.setValue(self.rgame.progress if self.rgame.state == RareGame.State.VERIFYING else 0)
        if self.rgame.state == RareGame.State.VERIFYING:
            self.ui.verify_stack.setCurrentWidget(self.ui.verify_progress_page)
        else:
            self.ui.verify_stack.setCurrentWidget(self.ui.verify_button_page)

        self.ui.repair_button.setEnabled(
            self.rgame.is_installed and (not self.rgame.is_non_asset) and self.rgame.is_idle
            and self.rgame.needs_repair
            and not self.args.offline
        )

        self.ui.move_button.setEnabled(
            self.rgame.is_installed and (not self.rgame.is_non_asset) and self.rgame.is_idle
        )
        self.ui.move_progress.setValue(self.rgame.progress if self.rgame.state == RareGame.State.MOVING else 0)
        if self.rgame.state == RareGame.State.MOVING:
            self.ui.move_stack.setCurrentWidget(self.ui.move_progress_page)
        else:
            self.ui.move_stack.setCurrentWidget(self.ui.move_button_page)

        self.ui.uninstall_button.setEnabled(
            self.rgame.is_installed and (not self.rgame.is_non_asset) and self.rgame.is_idle
        )

        if self.rgame.is_installed and not self.rgame.is_non_asset:
            self.ui.game_actions_stack.setCurrentWidget(self.ui.installed_page)
        else:
            self.ui.game_actions_stack.setCurrentWidget(self.ui.uninstalled_page)

    @Slot(RareGame)
    def update_game(self, rgame: RareGame):
        if self.rgame is not None:
            if (worker := self.rgame.worker()) is not None:
                if isinstance(worker, VerifyWorker):
                    try:
                        worker.signals.progress.disconnect(self.__on_verify_progress)
                    except TypeError as e:
                        logger.warning(f"{self.rgame.app_name} verify worker: {e}")
                if isinstance(worker, MoveWorker):
                    try:
                        worker.signals.progress.disconnect(self.__on_move_progress)
                    except TypeError as e:
                        logger.warning(f"{self.rgame.app_name} move worker: {e}")
            self.rgame.signals.widget.update.disconnect(self.__update_widget)

        self.rgame = None

        rgame.signals.widget.update.connect(self.__update_widget)
        if (worker := rgame.worker()) is not None:
            if isinstance(worker, VerifyWorker):
                worker.signals.progress.connect(self.__on_verify_progress)
            if isinstance(worker, MoveWorker):
                worker.signals.progress.connect(self.__on_move_progress)

        self.set_title.emit(rgame.app_title)
        self.ui.app_name.setText(rgame.app_name)
        self.ui.dev.setText(rgame.developer)

        if rgame.is_non_asset:
            self.ui.install_button.setText(self.tr("Link/Launch"))
            self.ui.game_actions_stack.setCurrentWidget(self.ui.uninstalled_page)
        else:
            self.ui.install_button.setText(self.tr("Install"))

        self.rgame = rgame
        self.__update_widget()
