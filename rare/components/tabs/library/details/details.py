import os
import platform
from hashlib import sha1
from logging import getLogger
from typing import Dict, Optional, Tuple

from PySide6.QtCore import (
    QCoreApplication,
    Qt,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import QFontMetrics, QHideEvent, QShowEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from rare.components.dialogs.move import MoveDialog
from rare.components.dialogs.selective import SelectiveDialog
from rare.models.game import RareGame
from rare.models.install import MoveGameModel, SelectiveDownloadsModel
from rare.shared import RareCore
from rare.shared.workers import MoveInfoWorker, MoveWorker, VerifyWorker
from rare.ui.components.tabs.library.details.details import Ui_GameDetails
from rare.utils.misc import format_size, qta_icon, relative_date, style_hyperlink
from rare.utils.paths import cache_dir
from rare.utils.qt_requests import QtRequests
from rare.widgets.dialogs import ButtonDialog, game_title
from rare.widgets.image_widget import ImageSize, ImageWidget, LoadingImageWidget
from rare.widgets.side_tab import SideTabContents

logger = getLogger("GameInfo")


class GameDetails(QWidget, SideTabContents):
    # str: app_name
    import_clicked = Signal(str)

    def __init__(self, rcore: RareCore, parent=None):
        super(GameDetails, self).__init__(parent=parent)
        self.implements_scrollarea = True
        self.ui = Ui_GameDetails()
        self.ui.setupUi(self)
        # lk: set object names for CSS properties
        self.ui.install_path.setObjectName("LinkLabel")
        self.ui.install_button.setObjectName("InstallButton")
        self.ui.modify_button.setObjectName("InstallButton")
        self.ui.verify_button.setObjectName("VerifyButton")
        self.ui.move_button.setObjectName("MoveButton")
        self.ui.uninstall_button.setObjectName("UninstallButton")

        self.ui.install_button.setIcon(qta_icon("ri.install-line"))
        self.ui.import_button.setIcon(qta_icon("mdi.application-import"))

        self.ui.modify_button.setIcon(qta_icon("mdi.content-save-edit-outline"))
        self.ui.verify_button.setIcon(qta_icon("mdi.check-underline"))
        self.ui.repair_button.setIcon(qta_icon("mdi.progress-wrench"))
        self.ui.move_button.setIcon(qta_icon("mdi.folder-move-outline"))
        self.ui.uninstall_button.setIcon(qta_icon("ri.uninstall-line"))

        self.ui.grade.setOpenExternalLinks(True)
        self.ui.install_path.setOpenExternalLinks(True)

        self.rcore = rcore
        self.core = rcore.core()
        self.args = rcore.args()
        self.net_manager = QtRequests(cache=str(cache_dir().joinpath("achievements")), parent=self)

        self.rgame: Optional[RareGame] = None

        self.image = ImageWidget(self)
        self.image.setFixedSize(ImageSize.DisplayTall)
        self.ui.left_layout.insertWidget(0, self.image, alignment=Qt.AlignmentFlag.AlignTop)
        self.ui.left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

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

        self.ui.add_tag_button.setIcon(qta_icon("mdi.plus"))
        self.ui.add_tag_button.clicked.connect(self.__on_tag_add)

        ach_progress_layout = QVBoxLayout(self.ui.ach_progress_page)
        ach_progress_layout.setContentsMargins(0, 0, 0, 0)
        ach_progress_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        ach_completed_layout = QVBoxLayout(self.ui.ach_completed_page)
        ach_completed_layout.setContentsMargins(0, 0, 0, 0)
        ach_completed_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        ach_uninitiated_layout = QVBoxLayout(self.ui.ach_uninitiated_page)
        ach_uninitiated_layout.setContentsMargins(0, 0, 0, 0)
        ach_uninitiated_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        ach_hidden_layout = QVBoxLayout(self.ui.ach_hidden_page)
        ach_hidden_layout.setContentsMargins(0, 0, 0, 0)
        ach_hidden_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # lk: hide unfinished things
        self.ui.description_field.setVisible(False)
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
        """This method is to be called from the button only"""
        self.rgame.uninstall()

    @Slot()
    def __on_modify(self):
        """This method is to be called from the button only"""
        self.rgame.modify()

    @Slot()
    def __on_repair(self):
        """This method is to be called from the button only"""
        repair_file = os.path.join(self.core.lgd.get_tmp_path(), f"{self.rgame.app_name}.repair")
        if not os.path.exists(repair_file):
            QMessageBox.warning(
                self,
                self.tr("Error - {}").format(self.rgame.app_title),
                self.tr("Repair file does not exist or game does not need a repair. Please verify game first"),
            )
            return
        self.repair_game(self.rgame)

    def repair_game(self, rgame: RareGame):
        rgame.update_game()
        ans = False
        if rgame.has_update:
            mbox = QMessageBox.question(
                self,
                self.tr("Repair and update? - {}").format(self.rgame.app_title),
                self.tr(
                    "There is an update for <b>{}</b> from <b>{}</b> to <b>{}</b>. Do you want to update the game while repairing it?"
                ).format(rgame.app_title, rgame.version, rgame.remote_version),
            )
            ans = (mbox == QMessageBox.StandardButton.Yes)
        rgame.repair(repair_and_update=ans)

    @Slot(RareGame, str)
    def __on_worker_error(self, rgame: RareGame, message: str):
        QMessageBox.warning(self, self.tr("Error - {}").format(rgame.app_title), message)

    @Slot()
    def __on_verify(self):
        """This method is to be called from the button only"""
        if not os.path.exists(self.rgame.igame.install_path):
            logger.error(f"Installation path {self.rgame.igame.install_path} for {self.rgame.app_title} does not exist")
            QMessageBox.warning(
                self,
                self.tr("Error - {}").format(self.rgame.app_title),
                self.tr("Installation path for <b>{}</b> does not exist. Cannot continue.").format(self.rgame.app_title),
            )
            return
        if self.rgame.sdl_name is not None:
            selective_dialog = SelectiveDialog(self.rgame, parent=self)
            selective_dialog.result_ready.connect(self.verify_game)
            selective_dialog.open()
        else:
            self.verify_game(self.rgame)

    @Slot(RareGame, SelectiveDownloadsModel)
    def verify_game(self, rgame: RareGame, sdl_model: SelectiveDownloadsModel = None):
        if sdl_model is not None:
            if not sdl_model.accepted or sdl_model.install_tag is None:
                return
            self.core.lgd.config.set(rgame.app_name, "install_tags", ",".join(sdl_model.install_tag))
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
                self.tr("<b>{}</b> has been verified successfully. No missing or corrupt files found").format(rgame.app_title),
            )
        else:
            ans = QMessageBox.question(
                self,
                self.tr("Summary - {}").format(rgame.app_title),
                self.tr(
                    "<b>{}</b> failed verification, <b>{}</b> file(s) corrupted, <b>{}</b> file(s) are missing. Do you want to repair them?"
                ).format(rgame.app_title, failed, missing),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if ans == QMessageBox.StandardButton.Yes:
                self.repair_game(rgame)

    @Slot()
    def __on_move(self):
        """This method is to be called from the button only"""
        move_dialog = MoveDialog(self.rcore, self.rgame, parent=self)
        move_dialog.result_ready.connect(self.move_game)
        move_dialog.open()

    def move_game(self, rgame: RareGame, options: MoveGameModel):
        if not options.accepted:
            return

        new_install_path = options.full_path
        if os.path.isdir(new_install_path):
            options.dst_exists = MoveInfoWorker.is_game_dir(self.rgame.install_path, new_install_path)

        if not options.dst_exists and options.target_name in os.listdir(options.target_path):
            ans = QMessageBox.question(
                self,
                self.tr("Move game? - {}").format(self.rgame.app_title),
                self.tr("Destination <b>{}</b> already exists. Are you sure you want to overwrite it?").format(
                    new_install_path
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )

            if ans == QMessageBox.StandardButton.Yes:
                options.dst_delete = True
            else:
                return

        worker = MoveWorker(self.core, rgame=rgame, options=options)
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

    @Slot(Qt.CheckState, str)
    def __on_tag_changed(self, state: Qt.CheckState, tag: str):
        tags = set(self.rgame.tags)
        tags.add(tag) if state == Qt.CheckState.Checked else tags.remove(tag)
        self.rgame.tags = tuple(tags)

    @Slot()
    def __on_tag_add(self):
        dialog = GameTagAddDialog(self.rgame, self.rcore.game_tags, self)
        dialog.result_ready.connect(self.__on_tag_add_result)
        dialog.show()

    @Slot(bool, str)
    def __on_tag_add_result(self, accepted: bool, tag: str):
        if accepted and tag:
            new_tag = GameTagCheckBox(tag, parent=self.ui.tags_group)
            new_tag.checkStateChangedData.connect(self.__on_tag_changed)
            # check tag after signal to invoke the save procedure
            new_tag.setChecked(True)
            self.ui.tags_vlayout.addWidget(new_tag)

    def showEvent(self, event: QShowEvent):
        if event.spontaneous():
            super().showEvent(event)
            return
        self.__update_widget()
        super().showEvent(event)

    def hideEvent(self, event: QHideEvent):
        if event.spontaneous():
            super().hideEvent(event)
            return
        self.rcore.signals().application.update_game_tags.emit()
        super().hideEvent(event)

    @Slot()
    def __update_widget(self):
        """React to state updates from RareGame"""
        self.image.setPixmap(self.rgame.get_pixmap(ImageSize.DisplayTall, True))

        self.ui.version_label.setDisabled(self.rgame.is_non_asset)
        self.ui.version.setDisabled(self.rgame.is_non_asset)
        self.ui.version.setText(self.rgame.version if not self.rgame.is_non_asset else "N/A")

        self.ui.install_size_label.setEnabled(bool(self.rgame.install_size))
        self.ui.install_size.setEnabled(bool(self.rgame.install_size))
        self.ui.install_size.setText(format_size(self.rgame.install_size) if self.rgame.install_size else "N/A")

        self.ui.install_path_label.setEnabled(bool(self.rgame.install_path))
        self.ui.install_path.setEnabled(bool(self.rgame.install_path))
        self.ui.install_path.setText(
            style_hyperlink(
                QUrl.fromLocalFile(self.rgame.install_path).toString(),
                self.rgame.install_path,
            )
            if self.rgame.install_path
            else "N/A"
        )

        self.ui.platform.setText(
            self.rgame.igame.platform if self.rgame.is_installed and not self.rgame.is_non_asset else self.rgame.default_platform
        )

        self.ui.grade_label.setDisabled(self.rgame.is_unreal or platform.system() == "Windows")
        self.ui.grade.setDisabled(self.rgame.is_unreal or platform.system() == "Windows")
        self.ui.grade.setText(
            style_hyperlink(
                f"https://www.protondb.com/app/{self.rgame.steam_appid}",
                f"{self.steam_grade_ratings[self.rgame.get_steam_grade()]} ({self.rgame.steam_appid})",
            )
        )

        self.ui.install_button.setEnabled((not self.rgame.is_installed or self.rgame.is_non_asset) and self.rgame.is_idle)

        self.ui.import_button.setEnabled((not self.rgame.is_installed or self.rgame.is_non_asset) and self.rgame.is_idle)

        self.ui.modify_button.setEnabled(
            self.rgame.is_installed and (not self.rgame.is_non_asset) and self.rgame.is_idle and self.rgame.sdl_name is not None
        )

        self.ui.verify_button.setEnabled(self.rgame.is_installed and (not self.rgame.is_non_asset) and self.rgame.is_idle)
        self.ui.verify_progress.setValue(self.rgame.progress if self.rgame.state == RareGame.State.VERIFYING else 0)
        if self.rgame.state == RareGame.State.VERIFYING:
            self.ui.verify_stack.setCurrentWidget(self.ui.verify_progress_page)
        else:
            self.ui.verify_stack.setCurrentWidget(self.ui.verify_button_page)

        self.ui.repair_button.setEnabled(
            self.rgame.is_installed
            and (not self.rgame.is_non_asset)
            and self.rgame.is_idle
            and self.rgame.needs_repair
            and not self.args.offline
        )

        self.ui.move_button.setEnabled(self.rgame.is_installed and (not self.rgame.is_non_asset) and self.rgame.is_idle)
        self.ui.move_progress.setValue(self.rgame.progress if self.rgame.state == RareGame.State.MOVING else 0)
        if self.rgame.state == RareGame.State.MOVING:
            self.ui.move_stack.setCurrentWidget(self.ui.move_progress_page)
        else:
            self.ui.move_stack.setCurrentWidget(self.ui.move_button_page)

        self.ui.uninstall_button.setEnabled(self.rgame.is_installed and (not self.rgame.is_non_asset) and self.rgame.is_idle)

        if self.rgame.is_installed and not self.rgame.is_non_asset:
            self.ui.actions_stack.setCurrentWidget(self.ui.installed_page)
        else:
            self.ui.actions_stack.setCurrentWidget(self.ui.uninstalled_page)

        for w in self.ui.tags_group.findChildren(GameTagCheckBox, options=Qt.FindChildOption.FindDirectChildrenOnly):
            w.deleteLater()

        for tag in self.rcore.game_tags:
            tag_check = GameTagCheckBox(tag, parent=self.ui.tags_group)
            tag_check.setChecked(tag in self.rgame.tags)
            tag_check.checkStateChangedData.connect(self.__on_tag_changed)
            self.ui.tags_vlayout.addWidget(tag_check)

    @Slot(RareGame)
    def update_game(self, rgame: RareGame):
        if self.rgame is not None:
            if (worker := self.rgame.get_worker()) is not None:
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
        if (worker := rgame.get_worker()) is not None:
            if isinstance(worker, VerifyWorker):
                worker.signals.progress.connect(self.__on_verify_progress)
            if isinstance(worker, MoveWorker):
                worker.signals.progress.connect(self.__on_move_progress)

        self.set_title.emit(rgame.app_title)
        self.ui.app_name.setText(rgame.app_name)
        self.ui.dev.setText(rgame.developer)

        if rgame.is_non_asset:
            self.ui.install_button.setText(self.tr("Link/Launch"))
            self.ui.actions_stack.setCurrentWidget(self.ui.uninstalled_page)
        else:
            self.ui.install_button.setText(self.tr("Install"))

        for page in (
            self.ui.ach_progress_page, self.ui.ach_completed_page, self.ui.ach_uninitiated_page, self.ui.ach_hidden_page,
        ):
            for w in page.findChildren(AchievementWidget, options=Qt.FindChildOption.FindDirectChildrenOnly):
                page.layout().removeWidget(w)
                w.deleteLater()

        if ach := rgame.achievements:
            self.ui.progress_field.setText(f"{ach.user_unlocked}/<b>{ach.total_achievements}</b>")
            self.ui.exp_field.setText(f"{ach.user_xp}/<b>{ach.total_product_xp}</b>")

            for group, page in zip(
                (ach.hidden, ach.uninitiated, ach.completed, ach.in_progress, ),
                (self.ui.ach_hidden_page, self.ui.ach_uninitiated_page, self.ui.ach_completed_page, self.ui.ach_progress_page, )
            ):
                self.ui.achievements_toolbox.setItemEnabled(self.ui.achievements_toolbox.indexOf(page), bool(group))
                if bool(group):
                    self.ui.achievements_toolbox.setCurrentWidget(page)
                for item in group:
                    page.layout().addWidget(AchievementWidget(self.net_manager, item), alignment=Qt.AlignmentFlag.AlignTop)
        else:
            self.ui.progress_field.setText(self.tr("No data"))
            self.ui.exp_field.setText(self.tr("No data"))
        self.ui.achievements_group.setVisible(bool(ach))

        self.rgame = rgame


class AchievementWidget(QFrame):
    def __init__(self, manager: QtRequests, achievement: Dict, parent=None):
        super().__init__(parent=parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Sunken)

        image = LoadingImageWidget(manager, parent=self)
        image.setFixedSize(ImageSize.LibraryIcon)
        image.fetchPixmap(achievement['icon_link'])

        title = QLabel(
            f"<b><font color={achievement['tier']['hexColor']}>{achievement['display_name']}</font></b>"
            f" ({achievement['xp']} XP)",
            parent=self
        )
        title.setWordWrap(True)
        description = QLabel(achievement['description'], parent=self)
        description.setWordWrap(True)
        unlock_date = achievement['unlock_date'].astimezone() if achievement['unlock_date'] else None
        unlock_date_str = f" ( On: {relative_date(unlock_date)} )" if unlock_date else ""
        progress = QLabel(f"Progress: <b>{achievement['progress'] * 100:,.2f}%</b> {unlock_date_str}", parent=self)
        if unlock_date:
            progress.setToolTip(str(unlock_date))

        right_layout = QVBoxLayout()
        right_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignTop)
        right_layout.addWidget(description, alignment=Qt.AlignmentFlag.AlignTop, stretch=1)
        right_layout.addWidget(progress, alignment=Qt.AlignmentFlag.AlignBottom)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(3, 3, 3, 3)
        main_layout.addWidget(image)
        main_layout.addLayout(right_layout, stretch=1)


class GameTagCheckBox(QCheckBox):
    checkStateChangedData = Signal(Qt.CheckState, str)

    tag_translations = {
        "backlog": QCoreApplication.translate("GameTagCheckBox", "Backlog", None),
        "completed": QCoreApplication.translate("GameTagCheckBox", "Completed", None),
        "favorite": QCoreApplication.translate("GameTagCheckBox", "Favorite", None),
        "hidden": QCoreApplication.translate("GameTagCheckBox", "Hidden", None),
    }

    def __init__(self, tag: str, parent=None):
        super(GameTagCheckBox, self).__init__(tag, parent)
        self.setObjectName(type(self).__name__)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setText(self.tag_translations.get(tag, tag))
        self.tag = tag
        base_color = (int(sha1(tag.encode("utf-8")).hexdigest()[0:6], base=16) & 0x707070) | 0x0C0C0C
        border_color = base_color | 0x3F3F3F
        luminance = (
            ((base_color & 0xFF0000) >> 16) * 0.2126 + ((base_color & 0x00FF00) >> 8) * 0.7152 + (base_color & 0x0000FF) * 0.0722
        )
        font_color = "white" if luminance < 140 else "black"
        style = ("QCheckBox#{0}{{color: {1};border-color: #{2:x};background-color: #{3:x};}}").format(
            self.objectName(), font_color, border_color, base_color
        )
        self.setStyleSheet(style)
        self.checkStateChanged.connect(lambda state: self.checkStateChangedData.emit(state, self.tag))

    def setText(self, text, /):
        fm = QFontMetrics(self.font())
        elide_text = fm.elidedText(
            text,
            Qt.TextElideMode.ElideRight,
            self.width(),
            Qt.TextFlag.TextShowMnemonic,
        )
        super().setText(elide_text)


class GameTagAddDialog(ButtonDialog):
    result_ready = Signal(bool, str)

    def __init__(self, rgame: RareGame, tags: Tuple[str, ...], parent=None):
        super(GameTagAddDialog, self).__init__(parent=parent)
        header = self.tr("Add tag")
        self.setWindowTitle(header)
        self.setSubtitle(game_title(header, rgame.app_title))

        self.line_edit = QLineEdit(self)
        self.line_edit.textChanged.connect(self.__on_text_changed)

        self.widget_layout = QVBoxLayout()
        self.widget_layout.addWidget(self.line_edit)

        self.setCentralLayout(self.widget_layout)

        self.accept_button.setText(self.tr("Save"))
        self.accept_button.setIcon(qta_icon("fa.edit", "fa5s.edit"))
        self.accept_button.setEnabled(False)

        self.tags = tags
        self.result: Tuple = (False, "")

    @Slot(str)
    def __on_text_changed(self, text: str):
        enabled = all((bool(text), len(text) > 4, text not in self.tags))
        self.accept_button.setEnabled(enabled)

    def done_handler(self):
        self.result_ready.emit(*self.result)

    def accept_handler(self):
        self.result = (True, self.line_edit.text())

    def reject_handler(self):
        self.result = (False, self.line_edit.text())
