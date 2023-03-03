import os
import sys
from typing import Union, Type

import qstylizer.style
from PyQt5.QtCore import QDir, QObject
from PyQt5.QtGui import QColor
from PyQt5.pyrcc import RCCResourceLibrary, CONSTANT_COMPRESSLEVEL_DEFAULT, CONSTANT_COMPRESSTHRESHOLD_DEFAULT
from PyQt5.sip import wrappertype

from rare.utils.misc import widget_object_name

verbose = True
compressLevel = 6
compressThreshold = CONSTANT_COMPRESSTHRESHOLD_DEFAULT
resourceRoot = ''


def processResourceFile(filenamesIn, filenameOut, listFiles):
    if verbose:
        sys.stderr.write("PyQt5 resource compiler\n")

    # Setup.
    library = RCCResourceLibrary()
    library.setInputFiles(filenamesIn)
    library.setVerbose(verbose)
    library.setCompressLevel(compressLevel)
    library.setCompressThreshold(compressThreshold)
    library.setResourceRoot(resourceRoot)

    if not library.readFiles():
        return False

    if filenameOut == '-':
        filenameOut = ''

    if listFiles:
        # Open the output file or use stdout if not specified.
        if filenameOut:
            try:
                out_fd = open(filenameOut, 'w')
            except Exception:
                sys.stderr.write(
                        "Unable to open %s for writing\n" % filenameOut)
                return False
        else:
            out_fd = sys.stdout

        for df in library.dataFiles():
            out_fd.write("%s\n" % QDir.cleanPath(df))

        if out_fd is not sys.stdout:
            out_fd.close()

        return True

    return library.output(filenameOut)


def css_name(widget: Union[wrappertype,QObject,Type], subwidget: str = ""):
    return f"#{widget_object_name(widget, '')}{subwidget}"


css = qstylizer.style.StyleSheet()


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
from rare.components.tabs.games.game_widgets.library_widget import ProgressLabel
css.QLabel[css_name(ProgressLabel)].setValues(
    borderWidth="1px",
    borderRadius="5%",
    fontWeight="bold",
    fontSize="16pt",
)


# IconGameWidget
from rare.components.tabs.games.game_widgets.icon_widget import IconWidget
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
from rare.components.tabs.games.game_widgets.list_widget import ListWidget
css.QLabel[css_name(ListWidget,"TitleLabel")].fontWeight.setValue("bold")
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


# WaitingSpinner
from rare.utils.extra_widgets import WaitingSpinner
css.QLabel[css_name(WaitingSpinner)].setValues(
    marginLeft="auto",
    marginRight="auto",
)


# SelectViewWidget
from rare.utils.extra_widgets import SelectViewWidget
css.QPushButton[css_name(SelectViewWidget, "Button")].setValues(
    border="none",
    backgroundColor="transparent",
)


if __name__ == "__main__":
    with open("stylesheet.qss", "w") as qss:
        qss.write(f'\n/* This file is auto-generated from "{os.path.basename(__file__)}". DO NOT EDIT!!! */\n\n')
        qss.write(css.toString())

    if not processResourceFile(["stylesheet.qrc"], "__init__.py", False):
        print("Error while creating compiled resources")
        sys.exit(1)

    sys.exit(0)
