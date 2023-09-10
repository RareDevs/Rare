import os
import platform
from logging import getLogger
from typing import Optional

from PyQt5.QtCore import QRunnable, QObject, pyqtSignal, QThreadPool, Qt, pyqtSlot, QSize
from PyQt5.QtWidgets import (
    QGroupBox,
    QMessageBox,
    QFrame,
    QHBoxLayout,
    QSizePolicy,
    QLabel,
    QPushButton,
    QFormLayout,
    QComboBox,
)

from rare.lgndr.core import LegendaryCore
from rare.models.game import RareEosOverlay
from rare.shared import RareCore
from rare.ui.components.tabs.games.integrations.eos_widget import Ui_EosWidget
from rare.utils import config_helper
from rare.utils.misc import icon
from rare.widgets.elide_label import ElideLabel

logger = getLogger("EpicOverlay")


class CheckForUpdateWorker(QRunnable):
    class CheckForUpdateSignals(QObject):
        update_available = pyqtSignal(bool)

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
        self.setFrameShape(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.indicator = QLabel(parent=self)
        self.indicator.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)

        self.prefix_label = ElideLabel(prefix if prefix is not None else overlay.app_title, parent=self)
        self.overlay_label = ElideLabel(parent=self)
        self.overlay_label.setDisabled(True)

        self.path_select = QComboBox(self)
        self.path_select.setMaximumWidth(150)
        self.path_select.setMinimumWidth(150)

        self.button = QPushButton(parent=self)
        self.button.setMinimumWidth(150)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(-1, 0, 0, 0)
        layout.addWidget(self.indicator)
        layout.addWidget(self.prefix_label, stretch=2)
        layout.addWidget(self.overlay_label, stretch=3)
        layout.addWidget(self.path_select)
        layout.addWidget(self.button)

        self.overlay = overlay
        self.prefix = prefix

        self.path_select.currentIndexChanged.connect(self.path_changed)
        self.button.clicked.connect(self.action)
        self.overlay.signals.game.installed.connect(self.update_state)
        self.overlay.signals.game.uninstalled.connect(self.update_state)

        self.update_state()

    @pyqtSlot(int)
    def path_changed(self, index: int) -> None:
        path = self.path_select.itemData(index, Qt.UserRole)
        active_path = os.path.normpath(p) if (p := self.overlay.active_path(self.prefix)) else ""
        if self.overlay.is_enabled(self.prefix) and (path == active_path):
            self.button.setText(self.tr("Disable overlay"))
        else:
            self.button.setText(self.tr("Enable overlay"))

    @pyqtSlot()
    def update_state(self) -> None:
        active_path = os.path.normpath(p) if (p := self.overlay.active_path(self.prefix)) else ""

        self.overlay_label.setText(f"<i>{active_path}<\i>")
        self.path_select.clear()

        if not self.overlay.is_installed and not self.overlay.available_paths(self.prefix):
            self.setDisabled(True)
            self.indicator.setPixmap(icon("fa.circle-o", color="grey").pixmap(20, 20))
            self.overlay_label.setText(self.overlay.active_path(self.prefix))
            self.button.setText(self.tr("Unavailable"))
            return

        self.setDisabled(False)

        if self.overlay.is_enabled(self.prefix):
            self.indicator.setPixmap(icon("fa.check-circle-o", color="green").pixmap(QSize(20, 20)))
        else:
            self.indicator.setPixmap(icon("fa.times-circle-o", color="red").pixmap(QSize(20, 20)))

        install_path = os.path.normpath(p) if (p := self.overlay.install_path) else ""

        self.path_select.addItem("Auto-detect", "")
        self.path_select.setItemData(0, "Auto-detect", Qt.ToolTipRole)
        for path in self.overlay.available_paths(self.prefix):
            path = os.path.normpath(path)
            self.path_select.addItem("Legendary-managed" if path == install_path else "EGL-managed", path)
            self.path_select.setItemData(self.path_select.findData(path), path, Qt.ToolTipRole)
        self.path_select.setCurrentIndex(self.path_select.findData(active_path))

    @pyqtSlot()
    def action(self) -> None:
        path = self.path_select.currentData(Qt.UserRole)
        active_path = os.path.normpath(p) if (p := self.overlay.active_path(self.prefix)) else ""
        install_path = os.path.normpath(p) if (p := self.overlay.install_path) else ""
        if self.overlay.is_enabled(self.prefix) and (path == active_path):
            if not self.overlay.disable(prefix=self.prefix):
                QMessageBox.warning(
                    self, "Warning",
                    self.tr("Failed to completely disable the active EOS Overlay.{}").format(
                        self.tr(" Since the previous overlay was managed by EGL you can safely ignore this is.")
                        if active_path != install_path else ""
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
    def __init__(self, parent=None):
        super(EosGroup, self).__init__(parent=parent)
        self.ui = Ui_EosWidget()
        self.ui.setupUi(self)
        # lk: set object names for CSS properties
        self.ui.install_button.setObjectName("InstallButton")
        self.ui.uninstall_button.setObjectName("UninstallButton")

        self.ui.install_page_layout.setAlignment(Qt.AlignTop)
        self.ui.info_page_layout.setAlignment(Qt.AlignTop)

        self.ui.install_button.setIcon(icon("ri.install-line"))
        self.ui.uninstall_button.setIcon(icon("ri.uninstall-line"))

        self.installed_path_label = ElideLabel(parent=self)
        self.installed_version_label = ElideLabel(parent=self)

        self.ui.info_label_layout.setWidget(0, QFormLayout.FieldRole, self.installed_version_label)
        self.ui.info_label_layout.setWidget(1, QFormLayout.FieldRole, self.installed_path_label)

        self.rcore = RareCore.instance()
        self.core = self.rcore.core()
        self.signals = self.rcore.signals()
        self.overlay = self.rcore.get_overlay()

        self.overlay.signals.game.installed.connect(self.install_finished)
        self.overlay.signals.game.uninstalled.connect(self.uninstall_finished)

        self.ui.install_button.clicked.connect(self.install_overlay)
        self.ui.update_button.clicked.connect(self.install_overlay)
        self.ui.uninstall_button.clicked.connect(self.uninstall_overlay)

        if self.overlay.is_installed:  # installed
            self.installed_version_label.setText(f"<b>{self.overlay.version}</b>")
            self.installed_path_label.setText(os.path.normpath(self.overlay.install_path))
            self.ui.overlay_stack.setCurrentWidget(self.ui.info_page)
        else:
            self.ui.overlay_stack.setCurrentWidget(self.ui.install_page)
        self.ui.update_button.setEnabled(False)

        self.threadpool = QThreadPool.globalInstance()

    def showEvent(self, a0) -> None:
        self.check_for_update()
        self.update_prefixes()
        super().showEvent(a0)

    def update_prefixes(self):
        for widget in self.findChildren(EosPrefixWidget, options=Qt.FindDirectChildrenOnly):
            widget.deleteLater()

        if platform.system() != "Windows":
            prefixes = config_helper.get_wine_prefixes()
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

    def check_for_update(self):
        if not self.overlay.is_installed:
            return

        def worker_finished(update_available):
            self.ui.update_button.setEnabled(update_available)

        worker = CheckForUpdateWorker(self.core)
        worker.signals.update_available.connect(worker_finished)
        QThreadPool.globalInstance().start(worker)

    @pyqtSlot()
    def install_finished(self):
        if not self.overlay.is_installed:
            logger.error("Something went wrong while installing overlay")
            QMessageBox.warning(self, "Error", self.tr("Something went wrong while installing Overlay"))
            return
        self.ui.overlay_stack.setCurrentWidget(self.ui.info_page)
        self.installed_version_label.setText(f"<b>{self.overlay.version}</b>")
        self.installed_path_label.setText(self.overlay.install_path)
        self.ui.update_button.setEnabled(False)

    @pyqtSlot()
    def uninstall_finished(self):
        self.ui.overlay_stack.setCurrentWidget(self.ui.install_page)

    @pyqtSlot()
    def install_overlay(self):
        self.overlay.install()

    def uninstall_overlay(self):
        if not self.overlay.is_installed:
            logger.error("No Legendary-managed overlay installation found.")
            self.ui.overlay_stack.setCurrentWidget(self.ui.install_page)
            return
        self.overlay.uninstall()
