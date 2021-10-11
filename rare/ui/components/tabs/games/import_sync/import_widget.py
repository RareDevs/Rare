# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'rare/ui/components/tabs/games/import_sync/import_widget.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ImportGroup(object):
    def setupUi(self, ImportGroup):
        ImportGroup.setObjectName("ImportGroup")
        ImportGroup.resize(223, 128)
        self.import_layout = QtWidgets.QFormLayout(ImportGroup)
        self.import_layout.setLabelAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.import_layout.setObjectName("import_layout")
        self.path_edit_label = QtWidgets.QLabel(ImportGroup)
        self.path_edit_label.setObjectName("path_edit_label")
        self.import_layout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.path_edit_label)
        self.app_name_label = QtWidgets.QLabel(ImportGroup)
        self.app_name_label.setObjectName("app_name_label")
        self.import_layout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.app_name_label)
        self.path_edit_layout = QtWidgets.QHBoxLayout()
        self.path_edit_layout.setObjectName("path_edit_layout")
        self.import_layout.setLayout(0, QtWidgets.QFormLayout.FieldRole, self.path_edit_layout)
        self.app_name_layout = QtWidgets.QHBoxLayout()
        self.app_name_layout.setObjectName("app_name_layout")
        self.import_layout.setLayout(1, QtWidgets.QFormLayout.FieldRole, self.app_name_layout)
        self.import_button = QtWidgets.QPushButton(ImportGroup)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.import_button.sizePolicy().hasHeightForWidth())
        self.import_button.setSizePolicy(sizePolicy)
        self.import_button.setObjectName("import_button")
        self.import_layout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.import_button)
        self.info_label = QtWidgets.QLabel(ImportGroup)
        self.info_label.setText("")
        self.info_label.setObjectName("info_label")
        self.import_layout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.info_label)

        self.retranslateUi(ImportGroup)
        QtCore.QMetaObject.connectSlotsByName(ImportGroup)

    def retranslateUi(self, ImportGroup):
        _translate = QtCore.QCoreApplication.translate
        ImportGroup.setWindowTitle(_translate("ImportGroup", "ImportGroup"))
        ImportGroup.setTitle(_translate("ImportGroup", "Import EGL game from directory"))
        self.path_edit_label.setText(_translate("ImportGroup", "Select path"))
        self.app_name_label.setText(_translate("ImportGroup", "Override app name"))
        self.import_button.setText(_translate("ImportGroup", "Import Game"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ImportGroup = QtWidgets.QGroupBox()
    ui = Ui_ImportGroup()
    ui.setupUi(ImportGroup)
    ImportGroup.show()
    sys.exit(app.exec_())
