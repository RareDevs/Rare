from abc import abstractmethod
from typing import Optional

from PyQt5.QtCore import QParallelAnimationGroup, Qt, QPropertyAnimation, QAbstractAnimation, QSize
from PyQt5.QtWidgets import (
    QWidget,
    QFrame,
    QToolButton,
    QVBoxLayout,
    QGridLayout,
    QSizePolicy,
    QGroupBox,
    QLabel,
)

from rare.utils.misc import icon


class CollapsibleBase(object):
    """
    References:
        # Adapted from c++ version
        https://stackoverflow.com/questions/32476006/how-to-make-an-expandable-collapsable-section-widget-in-qt
        # Adapted from python version
        https://newbedev.com/how-to-make-an-expandable-collapsable-section-widget-in-qt
    """
    def __init__(self):
        self.animation_duration = None
        self.toggle_animation = None
        self.content_area = None
        self.content_toggle_animation = None

    def setup(self, animation_duration: int = 200):
        self.animation_duration = animation_duration
        self.content_area: Optional[QWidget] = None
        self.content_toggle_animation: Optional[QPropertyAnimation] = None

        # let the entire widget grow and shrink with its content
        self.toggle_animation = QParallelAnimationGroup(self)
        self.toggle_animation.addAnimation(QPropertyAnimation(self, b"minimumHeight"))
        self.toggle_animation.addAnimation(QPropertyAnimation(self, b"maximumHeight"))

    @abstractmethod
    def isChecked(self) -> bool:
        pass

    @abstractmethod
    def click(self) -> None:
        pass

    @abstractmethod
    def addToLayout(self, widget: QWidget) -> None:
        pass

    @abstractmethod
    def sizeHint(self) -> QSize:
        pass

    def animationStart(self, checked):
        direction = QAbstractAnimation.Forward if checked else QAbstractAnimation.Backward
        self.toggle_animation.setDirection(direction)
        self.toggle_animation.start()

    def setWidget(self, widget: QWidget):
        if widget is None or widget is self.content_area:
            return
        is_checked = self.isChecked()
        if self.content_area is not None:
            # Collapse the parent before replacing the child
            if is_checked:
                self.click()
            self.toggle_animation.removeAnimation(self.content_toggle_animation)
            self.content_area.setParent(None)
            self.content_area.deleteLater()

        self.content_area = widget
        self.content_area.setParent(self)
        self.content_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # start out collapsed
        if not is_checked:
            self.content_area.setMaximumHeight(0)
            self.content_area.setMinimumHeight(0)

        self.content_toggle_animation = QPropertyAnimation(self.content_area, b"maximumHeight")
        self.toggle_animation.addAnimation(self.content_toggle_animation)
        self.addToLayout(self.content_area)
        collapsed_height = self.sizeHint().height()
        content_height = self.content_area.sizeHint().height()
        for i in range(self.toggle_animation.animationCount() - 1):
            spoiler_animation = self.toggle_animation.animationAt(i)
            spoiler_animation.setDuration(self.animation_duration)
            spoiler_animation.setStartValue(collapsed_height)
            spoiler_animation.setEndValue(collapsed_height + content_height)
        content_animation = self.toggle_animation.animationAt(self.toggle_animation.animationCount() - 1)
        content_animation.setDuration(self.animation_duration)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)
        if is_checked:
            self.click()


class CollapsibleFrame(QFrame, CollapsibleBase):
    def __init__(
        self, widget: QWidget = None, title: str = "", button_text: str = "", animation_duration: int = 200, parent=None
    ):
        super(CollapsibleFrame, self).__init__(parent=parent)
        self.setup(animation_duration)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)

        self.toggle_button = QToolButton(self)
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle_button.setIcon(icon("fa.arrow-right"))
        self.toggle_button.setText(button_text)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)

        self.title_label = QLabel(title)
        font = self.title_label.font()
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # don't waste space
        self.main_layout = QGridLayout(self)
        self.main_layout.setVerticalSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.toggle_button, 0, 0, 1, 1, Qt.AlignLeft)
        self.main_layout.addWidget(self.title_label, 0, 1, 1, 1)
        self.main_layout.setColumnStretch(1, 1)
        self.main_layout.setRowStretch(0, 0)
        self.main_layout.setRowStretch(1, 1)
        self.setLayout(self.main_layout)

        self.toggle_button.clicked.connect(self.animationStart)

        if widget is not None:
            self.setWidget(widget)

    def isChecked(self) -> bool:
        return self.toggle_button.isChecked()

    def click(self) -> None:
        self.toggle_button.click()

    def addToLayout(self, widget: QWidget) -> None:
        self.main_layout.addWidget(widget, 1, 0, 1, 2)

    def sizeHint(self) -> QSize:
        return super(CollapsibleFrame, self).sizeHint()

    def animationStart(self, checked):
        arrow_type = icon("fa.arrow-down") if checked else icon("fa.arrow-right")
        self.toggle_button.setIcon(arrow_type)
        super(CollapsibleFrame, self).animationStart(checked)


class CollapsibleGroupBox(QGroupBox, CollapsibleBase):
    def __init__(
        self, widget: QWidget = None, title: str = "", animation_duration: int = 200, parent=None
    ):
        super(CollapsibleGroupBox, self).__init__(parent=parent)
        self.setup(animation_duration)
        self.setTitle(title)
        self.setCheckable(True)
        self.setChecked(False)

        # don't waste space
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, -1)
        self.setLayout(self.main_layout)

        self.toggled.connect(self.animationStart)

        if widget is not None:
            self.setWidget(widget)

    def isChecked(self) -> bool:
        return super(CollapsibleGroupBox, self).isChecked()

    def click(self) -> None:
        self.setChecked(not self.isChecked())

    def addToLayout(self, widget: QWidget) -> None:
        self.main_layout.addWidget(widget)

    def sizeHint(self) -> QSize:
        return super(CollapsibleGroupBox, self).sizeHint()


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QDialog
    from rare.ui.components.dialogs.install_dialog_advanced import Ui_InstallDialogAdvanced
    from rare.utils.misc import set_style_sheet
    from rare.resources.stylesheets import RareStyle
    app = QApplication(sys.argv)

    set_style_sheet("RareStyle")

    ui_frame = Ui_InstallDialogAdvanced()
    widget_frame = QWidget()
    ui_frame.setupUi(widget_frame)
    collapsible_frame = CollapsibleFrame(widget_frame, title="Frame me!")
    collapsible_frame.setDisabled(False)

    def replace_func_frame(state):
        widget2_frame = QWidget()
        ui2_frame = Ui_InstallDialogAdvanced()
        ui2_frame.setupUi(widget2_frame)
        if state:
            ui2_frame.install_dialog_advanced_layout.removeRow(3)
            ui2_frame.install_dialog_advanced_layout.removeRow(4)
        collapsible_frame.setWidget(widget2_frame)

    ui_group = Ui_InstallDialogAdvanced()
    widget_group = QWidget()
    ui_group.setupUi(widget_group)
    collapsible_group = CollapsibleGroupBox(widget_group, title="Group me!")
    collapsible_group.setDisabled(False)

    def replace_func_group(state):
        widget2_group = QWidget()
        ui2_group = Ui_InstallDialogAdvanced()
        ui2_group.setupUi(widget2_group)
        if state:
            ui2_group.install_dialog_advanced_layout.removeRow(3)
            ui2_group.install_dialog_advanced_layout.removeRow(4)
        collapsible_group.setWidget(widget2_group)

    replace_button = QToolButton()
    replace_button.setText("Replace me!")
    replace_button.setCheckable(True)
    replace_button.setChecked(False)
    replace_button.clicked.connect(replace_func_frame)
    replace_button.clicked.connect(replace_func_group)

    dialog = QDialog()
    dialog.setLayout(QVBoxLayout())
    dialog.layout().addWidget(replace_button)
    dialog.layout().addWidget(collapsible_frame)
    dialog.layout().addWidget(collapsible_group)
    dialog.layout().setSizeConstraint(QVBoxLayout.SetFixedSize)
    dialog.show()
    sys.exit(app.exec_())

