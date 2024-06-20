# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'console_env.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QApplication, QDialog,
    QDialogButtonBox, QHeaderView, QSizePolicy, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_ConsoleEnv(object):
    def setupUi(self, ConsoleEnv):
        if not ConsoleEnv.objectName():
            ConsoleEnv.setObjectName(u"ConsoleEnv")
        ConsoleEnv.resize(600, 400)
        ConsoleEnv.setWindowTitle(u"ConsoleEnv")
        self.layout = QVBoxLayout(ConsoleEnv)
        self.layout.setObjectName(u"layout")
        self.table = QTableWidget(ConsoleEnv)
        if (self.table.columnCount() < 2):
            self.table.setColumnCount(2)
        __qtablewidgetitem = QTableWidgetItem()
        self.table.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.table.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        self.table.setObjectName(u"table")
        font = QFont()
        font.setFamilies([u"Monospace"])
        self.table.setFont(font)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSortingEnabled(True)
        self.table.setCornerButtonEnabled(True)
        self.table.setColumnCount(2)
        self.table.horizontalHeader().setVisible(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)

        self.layout.addWidget(self.table)

        self.buttons = QDialogButtonBox(ConsoleEnv)
        self.buttons.setObjectName(u"buttons")
        self.buttons.setOrientation(Qt.Orientation.Horizontal)
        self.buttons.setStandardButtons(QDialogButtonBox.Close)

        self.layout.addWidget(self.buttons)


        self.retranslateUi(ConsoleEnv)
        self.buttons.accepted.connect(ConsoleEnv.accept)
        self.buttons.rejected.connect(ConsoleEnv.reject)
    # setupUi

    def retranslateUi(self, ConsoleEnv):
        ___qtablewidgetitem = self.table.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("ConsoleEnv", u"Variable", None));
        ___qtablewidgetitem1 = self.table.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("ConsoleEnv", u"Value", None));
        pass
    # retranslateUi

