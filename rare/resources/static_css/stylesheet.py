import os
from typing import Type, Union

import qstylizer.style
from PySide6.QtCore import QObject
from PySide6.QtGui import QColor
from PySide6.scripts.pyside_tool import qt_tool_wrapper
from shiboken6.Shiboken import Object as wrappertype

from rare.utils.misc import widget_object_name

verbose = True
compressLevel = 6
compressAlgo = "zlib"
compressThreshold = 0


def css_name(widget: Union[wrappertype, QObject, Type], subwidget: str = ""):
    return f"#{widget_object_name(widget, '')}{subwidget}"


style = qstylizer.style.StyleSheet()

# Common height for some broken elements
for elem in (
    style.QPushButton,
    style.QProgressBar,
    style.QSpinBox,
    style.QToolButton,
    style.QLineEdit,
    style.QComboBox,
):
    elem.setValues(minHeight="2.75ex")


# Generic flat button
style['QPushButton[flat="true"]'].setValues(
    border="0px",
    borderRadius="5px",
    backgroundColor="rgba(255, 255, 255, 5%)",
)


# InfoLabel
style.QLabel["#InfoLabel"].setValues(
    color="#999",
    fontStyle="italic",
    fontWeight="normal",
)


verify_color = QColor("#d6af57")
move_color = QColor("#41cad9")
cloud_sync_color = QColor("#dbd3d1")


# [Un]InstallButton
style.QPushButton["#InstallButton"].setValues(
    borderColor=QColor(0, 180, 0).name(), backgroundColor=QColor(0, 120, 0).name()
)
style.QPushButton["#InstallButton"].hover.setValues(
    borderColor=QColor(0, 135, 0).name(), backgroundColor=QColor(0, 90, 0).name()
)
style.QPushButton["#InstallButton"].disabled.setValues(
    borderColor=QColor(0, 60, 0).name(), backgroundColor=QColor(0, 40, 0).name()
)
style.QPushButton["#UninstallButton"].setValues(
    borderColor=QColor(180, 0, 0).name(), backgroundColor=QColor(120, 0, 0).name()
)
style.QPushButton["#UninstallButton"].hover.setValues(
    borderColor=QColor(135, 0, 0).name(), backgroundColor=QColor(90, 0, 0).name()
)
style.QPushButton["#UninstallButton"].disabled.setValues(
    borderColor=QColor(60, 0, 0).name(), backgroundColor=QColor(40, 0, 0).name()
)
# VerifyButton
style.QPushButton["#VerifyButton"].setValues(
    borderColor=verify_color.darker(200).name(), backgroundColor=verify_color.darker(400).name()
)
style.QPushButton["#VerifyButton"].hover.setValues(
    borderColor=verify_color.darker(300).name(), backgroundColor=verify_color.darker(500).name()
)
style.QPushButton["#VerifyButton"].disabled.setValues(
    borderColor=verify_color.darker(400).name(), backgroundColor=verify_color.darker(600).name()
)
# MoveButton
style.QPushButton["#MoveButton"].setValues(
    borderColor=move_color.darker(200).name(), backgroundColor=move_color.darker(400).name()
)
style.QPushButton["#MoveButton"].hover.setValues(
    borderColor=move_color.darker(300).name(), backgroundColor=move_color.darker(500).name()
)
style.QPushButton["#MoveButton"].disabled.setValues(
    borderColor=move_color.darker(400).name(), backgroundColor=move_color.darker(600).name()
)


# QueueWorkerLabel
style.QLabel["#QueueWorkerLabel"].setValues(
    borderWidth="1px",
    borderStyle="solid",
    borderRadius="3px",
)

from rare.shared.workers.verify import VerifyWorker  # noqa: E402

style.QLabel["#QueueWorkerLabel"][f'[workertype="{widget_object_name(VerifyWorker, "")}"]'].setValues(
    borderColor=verify_color.darker(200).name(),
    backgroundColor=verify_color.darker(400).name(),
)

from rare.shared.workers.move import MoveWorker  # noqa: E402

style.QLabel["#QueueWorkerLabel"][f'[workertype="{widget_object_name(MoveWorker, "")}"]'].setValues(
    borderColor=move_color.darker(200).name(),
    backgroundColor=move_color.darker(400).name(),
)

from rare.shared.workers.cloud_sync import CloudSyncWorker  # noqa: E402

style.QLabel["#QueueWorkerLabel"][f'[workertype="{widget_object_name(CloudSyncWorker, "")}"]'].setValues(
    borderColor=cloud_sync_color.darker(200).name(),
    backgroundColor=cloud_sync_color.darker(400).name(),
)

# ProgressLabel
from rare.components.tabs.library.widgets.library_widget import ProgressLabel  # noqa: E402

style.QLabel[css_name(ProgressLabel)].setValues(
    borderWidth="1px",
    borderRadius="5%",
    fontWeight="bold",
    fontSize="16pt",
)


# IconGameWidget
from rare.components.tabs.library.widgets.icon_widget import IconWidget  # noqa: E402

icon_background_props = {
    "backgroundColor": "rgba(0, 0, 0, 65%)",
}
style.QLabel[css_name(IconWidget, "StatusLabel")].setValues(
    fontWeight="bold",
    color="white",
    **icon_background_props,
    borderRadius="5%",
    borderTopLeftRadius="11%",
    borderTopRightRadius="11%",
)
style.QWidget[css_name(IconWidget, "MiniWidget")].setValues(
    color="rgb(238, 238, 238)",
    **icon_background_props,
    borderRadius="5%",
    borderBottomLeftRadius="9%",
    borderBottomRightRadius="9%",
)
icon_bottom_label_props = {
    "color": "white",
    "backgroundColor": "rgba(0, 0, 0, 0%)",
}
style.QLabel[css_name(IconWidget, "TitleLabel")].setValues(
    fontWeight="bold",
    **icon_bottom_label_props,
)
style.QLabel[css_name(IconWidget, "TooltipLabel")].setValues(
    **icon_bottom_label_props,
)
icon_square_button_props = {
    "border": "1px solid black",
    "borderRadius": "10%",
}
icon_square_button_props.update(icon_background_props)
style.QPushButton[css_name(IconWidget, "Button")].setValues(**icon_square_button_props)
style.QPushButton[css_name(IconWidget, "Button")].hover.borderColor.setValue("gray")


# ListGameWidget
from rare.components.tabs.library.widgets.list_widget import ListWidget  # noqa: E402

style.QLabel[css_name(ListWidget, "TitleLabel")].fontWeight.setValue("bold")
list_status_label_props = {
    "color": "white",
    "backgroundColor": "rgba(0, 0, 0, 75%)",
    "border": "0px solid black",
    "borderRadius": "3px",
    "paddingLeft": "0.3em",
    "paddingRight": "0.3em",
}
style.QLabel[css_name(ListWidget, "StatusLabel")].setValues(
    fontWeight="bold",
    **list_status_label_props,
)
style.QLabel[css_name(ListWidget, "TooltipLabel")].setValues(
    **list_status_label_props,
)
style.QPushButton[css_name(ListWidget, "Button")].textAlign.setValue("left")
style.QLabel[css_name(ListWidget, "InfoLabel")].color.setValue("#999")


# MainTabBar
from rare.components.tabs.tab_widgets import MainTabBar  # noqa: E402

style.QTabBar[css_name(MainTabBar, "")].tab.disabled.setValues(
    border="0px",
    backgroundColor="transparent",
)


# SelectViewWidget
from rare.components.tabs.library.head_bar import SelectViewWidget  # noqa: E402

style.QPushButton[css_name(SelectViewWidget, "Button")].setValues(
    border="none",
    backgroundColor="transparent",
)


# ButtonLineEdit
from rare.widgets.button_edit import ButtonLineEdit  # noqa: E402

style.QPushButton[css_name(ButtonLineEdit, "Button")].setValues(
    backgroundColor="transparent",
    border="0px",
    padding="0px",
)


# GameTagCheckBox
from rare.components.tabs.library.details.details import GameTagCheckBox  # noqa: E402

style.QCheckBox[css_name(GameTagCheckBox, "")].setValues(
    margin="1px",
    borderWidth="1px",
    borderStyle="solid",
    borderColor="black",
    borderRadius="3px",
    padding="3px",
)


if __name__ == "__main__":
    with open(os.path.join(os.path.dirname(__file__), "stylesheet.qss"), "w", encoding="utf-8") as stylesheet:
        stylesheet.write(f'/* This file is auto-generated from "{os.path.basename(__file__)}". DO NOT EDIT!!! */\n\n')
        stylesheet.write(style.toString(recursive=True))

    qt_tool_wrapper(
        "rcc",
        [
            "-g",
            "python",
            "--compress",
            str(compressLevel),
            "--compress-algo",
            compressAlgo,
            "--threshold",
            str(compressThreshold),
            "--verbose" if verbose else "",
            os.path.join(os.path.dirname(__file__), "stylesheet.qrc"),
            "-o",
            os.path.join(os.path.dirname(__file__), "__init__.py"),
        ],
        True,
    )
