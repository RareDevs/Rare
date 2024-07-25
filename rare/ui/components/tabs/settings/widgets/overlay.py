# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'overlay.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QFormLayout, QGridLayout,
    QGroupBox, QLabel, QSizePolicy, QSpacerItem,
    QWidget)

class Ui_OverlaySettings(object):
    def setupUi(self, OverlaySettings):
        if not OverlaySettings.objectName():
            OverlaySettings.setObjectName(u"OverlaySettings")
        OverlaySettings.resize(555, 188)
        OverlaySettings.setWindowTitle(u"OverlaySettings")
        OverlaySettings.setTitle(u"")
        self.main_layout = QGridLayout(OverlaySettings)
        self.main_layout.setObjectName(u"main_layout")
        self.show_overlay_label = QLabel(OverlaySettings)
        self.show_overlay_label.setObjectName(u"show_overlay_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.show_overlay_label.sizePolicy().hasHeightForWidth())
        self.show_overlay_label.setSizePolicy(sizePolicy)

        self.main_layout.addWidget(self.show_overlay_label, 0, 0, 1, 1)

        self.show_overlay_combo = QComboBox(OverlaySettings)
        self.show_overlay_combo.setObjectName(u"show_overlay_combo")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.show_overlay_combo.sizePolicy().hasHeightForWidth())
        self.show_overlay_combo.setSizePolicy(sizePolicy1)

        self.main_layout.addWidget(self.show_overlay_combo, 0, 1, 1, 2)

        self.options_group = QGroupBox(OverlaySettings)
        self.options_group.setObjectName(u"options_group")
        self.options_group.setTitle(u"")
        self.options_layout = QGridLayout(self.options_group)
        self.options_layout.setObjectName(u"options_layout")
        self.options_form = QFormLayout()
        self.options_form.setObjectName(u"options_form")
        self.options_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.options_layout.addLayout(self.options_form, 1, 0, 1, 1)

        self.options_grid = QGridLayout()
        self.options_grid.setObjectName(u"options_grid")

        self.options_layout.addLayout(self.options_grid, 0, 0, 1, 1)

        self.hspacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.options_layout.addItem(self.hspacer, 0, 1, 2, 1)


        self.main_layout.addWidget(self.options_group, 2, 0, 1, 3)


        self.retranslateUi(OverlaySettings)
    # setupUi

    def retranslateUi(self, OverlaySettings):
        self.show_overlay_label.setText(QCoreApplication.translate("OverlaySettings", u"Show HUD", None))
        pass
    # retranslateUi

