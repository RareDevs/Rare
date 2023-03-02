# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'rare/ui/components/tabs/games/game_info/sync_widget.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_SyncWidget(object):
    def setupUi(self, SyncWidget):
        SyncWidget.setObjectName("SyncWidget")
        SyncWidget.resize(208, 109)
        self.main_layout = QtWidgets.QVBoxLayout(SyncWidget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setObjectName("main_layout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.local_gb = QtWidgets.QGroupBox(SyncWidget)
        self.local_gb.setObjectName("local_gb")
        self.local_layout = QtWidgets.QVBoxLayout(self.local_gb)
        self.local_layout.setObjectName("local_layout")
        self.date_info_local = QtWidgets.QLabel(self.local_gb)
        self.date_info_local.setText("TextLabel")
        self.date_info_local.setAlignment(QtCore.Qt.AlignCenter)
        self.date_info_local.setObjectName("date_info_local")
        self.local_layout.addWidget(self.date_info_local)
        self.icon_local = QtWidgets.QLabel(self.local_gb)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.icon_local.sizePolicy().hasHeightForWidth())
        self.icon_local.setSizePolicy(sizePolicy)
        self.icon_local.setText("")
        self.icon_local.setAlignment(QtCore.Qt.AlignCenter)
        self.icon_local.setObjectName("icon_local")
        self.local_layout.addWidget(self.icon_local)
        self.local_new_label = QtWidgets.QLabel(self.local_gb)
        self.local_new_label.setObjectName("local_new_label")
        self.local_layout.addWidget(self.local_new_label)
        self.upload_button = QtWidgets.QPushButton(self.local_gb)
        self.upload_button.setObjectName("upload_button")
        self.local_layout.addWidget(self.upload_button)
        self.horizontalLayout.addWidget(self.local_gb)
        self.cloud_gb = QtWidgets.QGroupBox(SyncWidget)
        self.cloud_gb.setObjectName("cloud_gb")
        self.cloud_layout = QtWidgets.QVBoxLayout(self.cloud_gb)
        self.cloud_layout.setObjectName("cloud_layout")
        self.date_info_remote = QtWidgets.QLabel(self.cloud_gb)
        self.date_info_remote.setText("TextLabel")
        self.date_info_remote.setAlignment(QtCore.Qt.AlignCenter)
        self.date_info_remote.setObjectName("date_info_remote")
        self.cloud_layout.addWidget(self.date_info_remote)
        self.icon_remote = QtWidgets.QLabel(self.cloud_gb)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.icon_remote.sizePolicy().hasHeightForWidth())
        self.icon_remote.setSizePolicy(sizePolicy)
        self.icon_remote.setText("")
        self.icon_remote.setAlignment(QtCore.Qt.AlignCenter)
        self.icon_remote.setObjectName("icon_remote")
        self.cloud_layout.addWidget(self.icon_remote)
        self.cloud_new_label = QtWidgets.QLabel(self.cloud_gb)
        self.cloud_new_label.setObjectName("cloud_new_label")
        self.cloud_layout.addWidget(self.cloud_new_label)
        self.download_button = QtWidgets.QPushButton(self.cloud_gb)
        self.download_button.setObjectName("download_button")
        self.cloud_layout.addWidget(self.download_button)
        self.horizontalLayout.addWidget(self.cloud_gb)
        self.main_layout.addLayout(self.horizontalLayout)

        self.retranslateUi(SyncWidget)

    def retranslateUi(self, SyncWidget):
        _translate = QtCore.QCoreApplication.translate
        SyncWidget.setWindowTitle(_translate("SyncWidget", "Form"))
        self.local_gb.setTitle(_translate("SyncWidget", "Local"))
        self.local_new_label.setText(_translate("SyncWidget", "Newer"))
        self.upload_button.setText(_translate("SyncWidget", "Upload"))
        self.cloud_gb.setTitle(_translate("SyncWidget", "Cloud"))
        self.cloud_new_label.setText(_translate("SyncWidget", "Newer"))
        self.download_button.setText(_translate("SyncWidget", "Download"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    SyncWidget = QtWidgets.QWidget()
    ui = Ui_SyncWidget()
    ui.setupUi(SyncWidget)
    SyncWidget.show()
    sys.exit(app.exec_())