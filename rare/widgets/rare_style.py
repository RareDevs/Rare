from PySide6.QtCore import QSize
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QProxyStyle, QTabBar, QStyle, QStyleOption, QWidget, QStyleOptionTab


# NOTE: possible styling conflicts
#
#       SideTabBar
#


class RareStyle(QProxyStyle):

    def sizeFromContents(self, types: QStyle.ContentsType, option: QStyleOption, size: QSize, widget: QWidget) -> QSize:
        size = super(RareStyle, self).sizeFromContents(types, option, size, widget)
        if types == QStyle.ContentsType.CT_TabBarTab:
            if option.shape in {QTabBar.Shape.RoundedEast, QTabBar.Shape.RoundedWest}:
                size.transpose()
        return size

    def drawControl(self, element: QStyle.ControlElement, option: QStyleOption, painter: QPainter, widget: QWidget) -> None:
        if element == QStyle.ControlElement.CE_TabBarTabLabel:
            if option.shape in {QTabBar.Shape.RoundedEast, QTabBar.Shape.RoundedWest}:
                opt = QStyleOptionTab(option)
                opt.shape = QTabBar.Shape.RoundedNorth
                super(RareStyle, self).drawControl(element, opt, painter, widget)
                return
        super(RareStyle, self).drawControl(element, option, painter, widget)
