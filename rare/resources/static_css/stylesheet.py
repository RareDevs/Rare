import os
import sys
from typing import Union, Type

import qstylizer.style
from PySide6.QtCore import QDir, QObject
from PySide6.QtGui import QColor
from PySide6.scripts.pyside_tool import qt_tool_wrapper
from shiboken6.Shiboken import Object as wrappertype

from rare.utils.misc import widget_object_name

verbose = True
compressLevel = 6
compressThreshold = 0


def css_name(widget: Union[wrappertype, QObject, Type], subwidget: str = ""):
    return f"#{widget_object_name(widget, '')}{subwidget}"


css = qstylizer.style.StyleSheet()


# Generic flat button
css['QPushButton[flat="true"]'].setValues(
    border="0px",
    borderRadius="5px",
    backgroundColor="rgba(255, 255, 255, 5%)",
)


# InfoLabel
css.QLabel["#InfoLabel"].setValues(
    color="#999",
    fontStyle="italic",
    fontWeight="normal",
)

# [Un]InstallButton
css.QPushButton["#InstallButton"].setValues(
    borderColor=QColor(0, 180, 0).name(),
    backgroundColor=QColor(0, 120, 0).name()
)
css.QPushButton["#InstallButton"].hover.setValues(
    borderColor=QColor(0, 135, 0).name(),
    backgroundColor=QColor(0, 90, 0).name()
)
css.QPushButton["#InstallButton"].disabled.setValues(
    borderColor=QColor(0, 60, 0).name(),
    backgroundColor=QColor(0, 40, 0).name()
)
css.QPushButton["#UninstallButton"].setValues(
    borderColor=QColor(180, 0, 0).name(),
    backgroundColor=QColor(120, 0, 0).name()
)
css.QPushButton["#UninstallButton"].hover.setValues(
    borderColor=QColor(135, 0, 0).name(),
    backgroundColor=QColor(90, 0, 0).name()
)
css.QPushButton["#UninstallButton"].disabled.setValues(
    borderColor=QColor(60, 0, 0).name(),
    backgroundColor=QColor(40, 0, 0).name()
)


# QueueWorkerLabel
css.QLabel["#QueueWorkerLabel"].setValues(
    borderWidth="1px",
    borderStyle="solid",
    borderRadius="3px",
)
verify_color = QColor("#d6af57")
css.QLabel["#QueueWorkerLabel"]['[workerType="Verify"]'].setValues(
    borderColor=verify_color.darker(200).name(),
    backgroundColor=verify_color.darker(400).name()
)
move_color = QColor("#41cad9")
css.QLabel["#QueueWorkerLabel"]['[workerType="Move"]'].setValues(
    borderColor=move_color.darker(200).name(),
    backgroundColor=move_color.darker(400).name()
)


# ProgressLabel
from rare.components.tabs.library.widgets.library_widget import ProgressLabel
css.QLabel[css_name(ProgressLabel)].setValues(
    borderWidth="1px",
    borderRadius="5%",
    fontWeight="bold",
    fontSize="16pt",
)


# IconGameWidget
from rare.components.tabs.library.widgets.icon_widget import IconWidget
icon_background_props = {
    "backgroundColor": "rgba(0, 0, 0, 65%)",
}
css.QLabel[css_name(IconWidget, "StatusLabel")].setValues(
    fontWeight="bold",
    color="white",
    **icon_background_props,
    borderRadius="5%",
    borderTopLeftRadius="11%",
    borderTopRightRadius="11%",
)
css.QWidget[css_name(IconWidget, "MiniWidget")].setValues(
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
css.QLabel[css_name(IconWidget, "TitleLabel")].setValues(
    fontWeight="bold",
    **icon_bottom_label_props,
)
css.QLabel[css_name(IconWidget, "TooltipLabel")].setValues(
    **icon_bottom_label_props,
)
icon_square_button_props = {
    "border": "1px solid black",
    "borderRadius": "10%",
}
icon_square_button_props.update(icon_background_props)
css.QPushButton[css_name(IconWidget, "Button")].setValues(
    **icon_square_button_props
)
css.QPushButton[css_name(IconWidget, "Button")].hover.borderColor.setValue("gray")


# ListGameWidget
from rare.components.tabs.library.widgets.list_widget import ListWidget
css.QLabel[css_name(ListWidget, "TitleLabel")].fontWeight.setValue("bold")
list_status_label_props = {
    "color": "white",
    "backgroundColor": "rgba(0, 0, 0, 75%)",
    "border": "1px solid black",
    "borderRadius": "5px",
}
css.QLabel[css_name(ListWidget, "StatusLabel")].setValues(
    fontWeight="bold",
    **list_status_label_props,
)
css.QLabel[css_name(ListWidget, "TooltipLabel")].setValues(
    **list_status_label_props,
)
css.QPushButton[css_name(ListWidget, "Button")].textAlign.setValue("left")
css.QLabel[css_name(ListWidget, "InfoLabel")].color.setValue("#999")


# SelectViewWidget
from rare.components.tabs.library.head_bar import SelectViewWidget
css.QPushButton[css_name(SelectViewWidget, "Button")].setValues(
    border="none",
    backgroundColor="transparent",
)


# ButtonLineEdit
from rare.widgets.button_edit import ButtonLineEdit
css.QPushButton[css_name(ButtonLineEdit, "Button")].setValues(
    backgroundColor="transparent",
    border="0px",
    padding="0px",
)


if __name__ == "__main__":
    with open("stylesheet.qss", "w", encoding="utf-8") as qss:
        qss.write(f'\n/* This file is auto-generated from "{os.path.basename(__file__)}". DO NOT EDIT!!! */\n\n')
        qss.write(css.toString())

    qt_tool_wrapper(
        "rcc",
        [
            "-g", "python",
            "--compress", str(compressLevel),
            "--threshold", str(compressThreshold),
            "--verbose" if verbose else "",
            "stylesheet.qrc",
            "-o", "__init__.py",
        ],
        True
    )
