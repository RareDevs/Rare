# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'rare/ui/components/tabs/games/import_sync/egl_sync_group.ui'
#
# Created by: PyQt5 UI code generator 5.15.6
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_EGLSyncGroup(object):
    def setupUi(self, EGLSyncGroup):
        EGLSyncGroup.setObjectName("EGLSyncGroup")
        EGLSyncGroup.resize(478, 106)
        EGLSyncGroup.setWindowTitle("EGLSyncGroup")
        EGLSyncGroup.setCheckable(False)
        EGLSyncGroup.setChecked(False)
        self.egl_sync_layout = QtWidgets.QFormLayout(EGLSyncGroup)
        self.egl_sync_layout.setLabelAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter
        )
        self.egl_sync_layout.setObjectName("egl_sync_layout")
        self.egl_path_edit_label = QtWidgets.QLabel(EGLSyncGroup)
        self.egl_path_edit_label.setObjectName("egl_path_edit_label")
        self.egl_sync_layout.setWidget(
            0, QtWidgets.QFormLayout.LabelRole, self.egl_path_edit_label
        )
        self.egl_path_edit_layout = QtWidgets.QHBoxLayout()
        self.egl_path_edit_layout.setObjectName("egl_path_edit_layout")
        self.egl_sync_layout.setLayout(
            0, QtWidgets.QFormLayout.FieldRole, self.egl_path_edit_layout
        )
        self.egl_path_info_label = QtWidgets.QLabel(EGLSyncGroup)
        self.egl_path_info_label.setObjectName("egl_path_info_label")
        self.egl_sync_layout.setWidget(
            1, QtWidgets.QFormLayout.LabelRole, self.egl_path_info_label
        )
        self.egl_path_info = QtWidgets.QLabel(EGLSyncGroup)
        self.egl_path_info.setText("error")
        self.egl_path_info.setTextInteractionFlags(
            QtCore.Qt.LinksAccessibleByMouse | QtCore.Qt.TextSelectableByMouse
        )
        self.egl_path_info.setObjectName("egl_path_info")
        self.egl_sync_layout.setWidget(
            1, QtWidgets.QFormLayout.FieldRole, self.egl_path_info
        )
        self.egl_sync_check = QtWidgets.QCheckBox(EGLSyncGroup)
        self.egl_sync_check.setText("")
        self.egl_sync_check.setObjectName("egl_sync_check")
        self.egl_sync_layout.setWidget(
            2, QtWidgets.QFormLayout.FieldRole, self.egl_sync_check
        )
        self.import_export_layout = QtWidgets.QVBoxLayout()
        self.import_export_layout.setObjectName("import_export_layout")
        self.egl_sync_layout.setLayout(
            3, QtWidgets.QFormLayout.SpanningRole, self.import_export_layout
        )
        self.egl_sync_check_label = QtWidgets.QLabel(EGLSyncGroup)
        self.egl_sync_check_label.setObjectName("egl_sync_check_label")
        self.egl_sync_layout.setWidget(
            2, QtWidgets.QFormLayout.LabelRole, self.egl_sync_check_label
        )

        self.retranslateUi(EGLSyncGroup)
        QtCore.QMetaObject.connectSlotsByName(EGLSyncGroup)

    def retranslateUi(self, EGLSyncGroup):
        _translate = QtCore.QCoreApplication.translate
        EGLSyncGroup.setTitle(
            _translate("EGLSyncGroup", "Sync with Epic Games Launcher")
        )
        self.egl_path_edit_label.setText(
            _translate("EGLSyncGroup", "Prefix/Manifest path")
        )
        self.egl_path_info_label.setText(_translate("EGLSyncGroup", "Estimated path"))
        self.egl_sync_check_label.setText(
            _translate("EGLSyncGroup", "Enable automatic sync")
        )


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    EGLSyncGroup = QtWidgets.QGroupBox()
    ui = Ui_EGLSyncGroup()
    ui.setupUi(EGLSyncGroup)
    EGLSyncGroup.show()
    sys.exit(app.exec_())
