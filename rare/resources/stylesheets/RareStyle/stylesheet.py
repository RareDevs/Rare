import os
from typing import Union, Type

import qstylizer.style
import qstylizer.parser
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


# style = qstylizer.style.StyleSheet()
with open(os.path.join(os.path.dirname(__file__), "template.qss"), "r", encoding="utf-8") as template:
    style = qstylizer.parser.parse(template.read())

background_color_base = QColor(32, 34, 37)
background_color_control = QColor( 51, 54, 59)
background_color_editable = QColor(38, 38, 51)
background_color_selection = QColor(39, 66, 66)

border_color_editable = QColor(47, 79, 79)

common_attributes = {
    "borderWidth": "1px",
    "borderStyle": "solid",
    "borderRadius": "2px",
    "padding": "1px",
}
common_attributes_editable = {
    "borderColor": border_color_editable.name(),
    "backgroundColor": background_color_editable.name(),
    "selectionBackgroundColor": background_color_selection.name(),
}

style.QPushButton.paddingTop.setValue("2px")
style.QPushButton.paddingBottom.setValue("2px")
style.QToolButton.paddingTop.setValue("2px")
style.QToolButton.paddingBottom.setValue("2px")

style["QTableView QTableCornerButton::section"].setValues(**common_attributes, **common_attributes_editable)

style.QComboBox.comboboxPopup.setValue(0)
style["QComboBox QAbstractItemView"].setValues(**common_attributes, **common_attributes_editable)

for selector in (
    "QListView QLineEdit",
    "QTreeView QLineEdit",
    "QTableView QLineEdit",
):
    style[selector].padding.setValue("0px")


if __name__ == "__main__":
    with open(os.path.join(os.path.dirname(__file__), "stylesheet.qss"), "w", encoding="utf-8") as stylesheet:
        stylesheet.write(f'/* This file is auto-generated from "{os.path.basename(__file__)}". DO NOT EDIT!!! */\n\n')
        stylesheet.write(style.toString(recursive=True))

    qt_tool_wrapper(
        "rcc",
        [
            "-g", "python",
            "--compress", str(compressLevel),
            "--compress-algo", compressAlgo,
            "--threshold", str(compressThreshold),
            "--verbose" if verbose else "",
            os.path.join(os.path.dirname(__file__), "stylesheet.qrc"),
            "-o", os.path.join(os.path.dirname(__file__), "__init__.py"),
        ],
        True
    )
