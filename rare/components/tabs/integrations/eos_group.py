import os
import platform
from logging import getLogger
from typing import Optional

from PySide6.QtCore import (
    QObject,
    QRunnable,
    QSize,
    Qt,
    QThreadPool,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
)

from rare.lgndr.core import LegendaryCore
from rare.models.game import RareEosOverlay
from rare.shared import RareCore
from rare.ui.components.tabs.integrations.eos_widget import Ui_EosWidget
from rare.utils import config_helper as config
from rare.utils.misc import qta_icon, style_hyperlink
from rare.widgets.elide_label import ElideLabel

logger = getLogger("EpicOverlay")


class CheckForUpdateWorker(QRunnable):
    class CheckForUpdateSignals(QObject):
        update_available = Signal(bool)

    def __init__(self, core: LegendaryCore):
        super(CheckForUpdateWorker, self).__init__()
        self.signals = self.CheckForUpdateSignals()
        self.setAutoDelete(True)
        self.core = core

    def run(self) -> None:
        self.core.check_for_overlay_updates()
        self.signals.update_available.emit(self.core.overlay_update_available)


class EosPrefixWidget(QFrame):
    def __init__(self, overlay: RareEosOverlay, prefix: Optional[str], parent=None):
        super(EosPrefixWidget, self).__init__(parent=parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.indicator = QLabel(parent=self)
        self.indicator.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)

        self.prefix_label = ElideLabel(
            prefix.replace(os.path.expanduser("~"), "~") if prefix is not None else overlay.app_title,
            parent=self,
        )
        self.prefix_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.overlay_label = ElideLabel(parent=self)
        self.overlay_label.setDisabled(True)
        self.overlay_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.path_select = QComboBox(self)
        self.path_select.setMaximumWidth(150)
        self.path_select.setMinimumWidth(150)

        self.button = QPushButton(parent=self)
        self.button.setMinimumWidth(150)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(-1, 0, 0, 0)
        layout.addWidget(self.indicator, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.prefix_label, stretch=2)
        layout.addWidget(self.overlay_label, stretch=1)
        layout.addWidget(self.path_select, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.button, alignment=Qt.AlignmentFlag.AlignRight)

        self.overlay = overlay
        self.prefix = prefix

        self.path_select.currentIndexChanged.connect(self.path_changed)
        self.button.clicked.connect(self.action)
        self.overlay.signals.game.installed.connect(self.update_state)
        self.overlay.signals.game.uninstalled.connect(self.update_state)

        self.update_state()

    @Slot(int)
    def path_changed(self, index: int) -> None:
        path = self.path_select.itemData(index, Qt.ItemDataRole.UserRole)
        active_path = os.path.normpath(p) if (p := self.overlay.active_path(self.prefix)) else ""
        if self.overlay.is_enabled(self.prefix) and (path == active_path):
            self.button.setText(self.tr("Disable overlay"))
        else:
            self.button.setText(self.tr("Enable overlay"))

    @Slot()
    def update_state(self) -> None:
        active_path = os.path.normpath(p) if (p := self.overlay.active_path(self.prefix)) else ""

        self.overlay_label.setText(f"<i>{active_path}</i>")
        self.overlay_label.setVisible(bool(active_path))
        self.path_select.clear()

        if not self.overlay.is_installed and not self.overlay.available_paths(self.prefix):
            self.setDisabled(True)
            self.indicator.setPixmap(qta_icon("fa.circle-o", "fa5.circle", color="grey").pixmap(20, 20))
            active_path = self.overlay.active_path(self.prefix)
            self.overlay_label.setText(f"<i>{active_path}</i>")
            self.overlay_label.setVisible(bool(active_path))
            self.button.setText(self.tr("Unavailable"))
            return

        if self.overlay.is_enabled(self.prefix):
            self.indicator.setPixmap(qta_icon("fa.check-circle-o", "fa5.check-circle", color="green").pixmap(QSize(20, 20)))
        else:
            self.indicator.setPixmap(qta_icon("fa.times-circle-o", "fa5.times-circle", color="red").pixmap(QSize(20, 20)))

        install_path = os.path.normpath(p) if (p := self.overlay.install_path) else ""

        self.path_select.addItem("Auto-detect", "")
        self.path_select.setItemData(0, "Auto-detect", Qt.ItemDataRole.ToolTipRole)
        for path in self.overlay.available_paths(self.prefix):
            path = os.path.normpath(path)
            self.path_select.addItem("Legendary-managed" if path == install_path else "EGL-managed", path)
            self.path_select.setItemData(self.path_select.findData(path), path, Qt.ItemDataRole.ToolTipRole)
        self.path_select.setCurrentIndex(self.path_select.findData(active_path))

        self.setEnabled(self.overlay.state == RareEosOverlay.State.IDLE)

    @Slot()
    def action(self) -> None:
        path = self.path_select.currentData(Qt.ItemDataRole.UserRole)
        active_path = os.path.normpath(p) if (p := self.overlay.active_path(self.prefix)) else ""
        install_path = os.path.normpath(p) if (p := self.overlay.install_path) else ""
        if self.overlay.is_enabled(self.prefix) and (path == active_path):
            if not self.overlay.disable(prefix=self.prefix):
                QMessageBox.warning(
                    self,
                    "Warning",
                    self.tr("Failed to completely disable the active EOS Overlay.{}").format(
                        self.tr(" Since the previous overlay was managed by EGL you can safely ignore this is.")
                        if active_path != install_path
                        else ""
                    ),
                )
        else:
            self.overlay.disable(prefix=self.prefix)
            if not self.overlay.enable(prefix=self.prefix, path=path):
                QMessageBox.warning(
                    self,
                    "Warning",
                    self.tr("Failed to completely enable EOS overlay.{}").format(
                        self.tr(" Since the previous overlay was managed by EGL you can safely ignore this is.")
                        if active_path != install_path
                        else ""
                    ),
                )
        self.update_state()


class EosGroup(QGroupBox):
    def __init__(self, rcore: RareCore, parent=None):
        super(EosGroup, self).__init__(parent=parent)
        self.rcore = rcore
        self.core = rcore.core()
        self.signals = rcore.signals()
        self.overlay = rcore.get_overlay()

        self.ui = Ui_EosWidget()
        self.ui.setupUi(self)
        # lk: set object names for CSS properties
        self.ui.install_button.setObjectName("InstallButton")
        self.ui.uninstall_button.setObjectName("UninstallButton")

        self.ui.install_page_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.ui.update_page_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.ui.install_button.setIcon(qta_icon("ri.install-line"))
        self.ui.update_button.setIcon(qta_icon("ri.arrow-up-circle-line"))
        self.ui.uninstall_button.setIcon(qta_icon("ri.uninstall-line"))

        self.version = ElideLabel(parent=self)
        self.install_path = QLabel(parent=self)
        self.install_path.setObjectName("LinkLabel")
        self.install_path.setOpenExternalLinks(True)

        self.ui.info_layout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.version)
        self.ui.info_layout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.install_path)

        self.overlay.signals.widget.update.connect(self.update_state)
        self.overlay.signals.game.installed.connect(self.install_finished)
        self.overlay.signals.game.uninstalled.connect(self.uninstall_finished)

        self.ui.install_button.clicked.connect(self.install_overlay)
        self.ui.update_button.clicked.connect(self.install_overlay)
        self.ui.uninstall_button.clicked.connect(self.uninstall_overlay)

        self.threadpool = QThreadPool.globalInstance()
        self.worker: Optional[CheckForUpdateWorker] = None

    def showEvent(self, a0: QShowEvent) -> None:
        if a0.spontaneous():
            return super().showEvent(a0)
        self.update_state()
        self.update_prefixes()
        self.check_for_update()
        super().showEvent(a0)

    @Slot()
    def update_state(self):
        if self.overlay.is_installed:  # installed
            self.version.setText(f"<b>{self.overlay.version}</b>")
            self.ui.button_stack.setCurrentWidget(self.ui.update_page)
        else:
            self.version.setText(self.tr("<b>Epic Online Services Overlay is not installed</b>"))
            self.ui.button_stack.setCurrentWidget(self.ui.install_page)
        self.install_path.setEnabled(self.overlay.is_installed)
        self.install_path.setText(
            style_hyperlink(
                QUrl.fromLocalFile(self.overlay.install_path).toString(),
                self.overlay.install_path,
            )
            if self.overlay.is_installed
            else "N/A"
        )

        self.ui.install_button.setEnabled(self.overlay.state == RareEosOverlay.State.IDLE)
        self.ui.update_button.setEnabled(self.overlay.state == RareEosOverlay.State.IDLE and self.overlay.has_update)
        self.ui.uninstall_button.setEnabled(self.overlay.state == RareEosOverlay.State.IDLE)

    def update_prefixes(self):
        for widget in self.findChildren(EosPrefixWidget, options=Qt.FindChildOption.FindDirectChildrenOnly):
            widget.deleteLater()

        if platform.system() != "Windows":
            prefixes = config.get_prefixes()
            prefixes = sorted({prefix for prefix, _ in prefixes})
            if platform.system() == "Darwin":
                # TODO: add crossover support
                pass
            for prefix in prefixes:
                widget = EosPrefixWidget(self.overlay, prefix)
                self.ui.eos_layout.addWidget(widget)
            logger.debug("Updated prefixes")
        else:
            widget = EosPrefixWidget(self.overlay, None)
            self.ui.eos_layout.addWidget(widget)

    @Slot(bool)
    def check_for_update_finished(self, update_available: bool):
        self.worker = None
        self.ui.update_button.setEnabled(self.overlay.state == RareEosOverlay.State.IDLE and update_available)

    def check_for_update(self):
        self.ui.update_button.setEnabled(False)
        if not self.overlay.is_installed:
            return

        if self.worker is not None:
            return

        self.worker = CheckForUpdateWorker(self.core)
        self.worker.signals.update_available.connect(self.check_for_update_finished)
        QThreadPool.globalInstance().start(self.worker)

    @Slot()
    def install_finished(self):
        if not self.overlay.is_installed:
            logger.error("Something went wrong while installing EOS Overlay")
            QMessageBox.warning(
                self,
                "Error",
                self.tr("Something went wrong while installing EOS Overlay"),
            )
            return
        self.update_state()

    @Slot()
    def uninstall_finished(self):
        self.update_state()

    @Slot()
    def install_overlay(self):
        self.overlay.install()

    def uninstall_overlay(self):
        if not self.overlay.is_installed:
            logger.error("No Legendary-managed EOS Overlay installation found.")
            self.ui.button_stack.setCurrentWidget(self.ui.install_page)
            return
        self.overlay.uninstall()
