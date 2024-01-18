# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'rare/ui/components/tabs/settings/widgets/overlay.ui'
#
# Created by: PyQt5 UI code generator 5.15.10
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_OverlaySettings(object):
    def setupUi(self, OverlaySettings):
        OverlaySettings.setObjectName("OverlaySettings")
        OverlaySettings.resize(555, 188)
        OverlaySettings.setWindowTitle("OverlaySettings")
        OverlaySettings.setTitle("")
        self.main_layout = QtWidgets.QGridLayout(OverlaySettings)
        self.main_layout.setObjectName("main_layout")
        self.show_overlay_label = QtWidgets.QLabel(OverlaySettings)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.show_overlay_label.sizePolicy().hasHeightForWidth())
        self.show_overlay_label.setSizePolicy(sizePolicy)
        self.show_overlay_label.setObjectName("show_overlay_label")
        self.main_layout.addWidget(self.show_overlay_label, 0, 0, 1, 1)
        self.show_overlay_combo = QtWidgets.QComboBox(OverlaySettings)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.show_overlay_combo.sizePolicy().hasHeightForWidth())
        self.show_overlay_combo.setSizePolicy(sizePolicy)
        self.show_overlay_combo.setObjectName("show_overlay_combo")
        self.main_layout.addWidget(self.show_overlay_combo, 0, 1, 1, 2)
        self.options_group = QtWidgets.QGroupBox(OverlaySettings)
        self.options_group.setTitle("")
        self.options_group.setObjectName("options_group")
        self.options_layout = QtWidgets.QGridLayout(self.options_group)
        self.options_layout.setObjectName("options_layout")
        self.options_form = QtWidgets.QFormLayout()
        self.options_form.setLabelAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.options_form.setObjectName("options_form")
        self.options_layout.addLayout(self.options_form, 1, 0, 1, 1)
        self.options_grid = QtWidgets.QGridLayout()
        self.options_grid.setObjectName("options_grid")
        self.options_layout.addLayout(self.options_grid, 0, 0, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.options_layout.addItem(spacerItem, 0, 1, 2, 1)
        self.main_layout.addWidget(self.options_group, 2, 0, 1, 3)

        self.retranslateUi(OverlaySettings)

    def retranslateUi(self, OverlaySettings):
        _translate = QtCore.QCoreApplication.translate
        self.show_overlay_label.setText(_translate("OverlaySettings", "Show HUD"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    OverlaySettings = QtWidgets.QGroupBox()
    ui = Ui_OverlaySettings()
    ui.setupUi(OverlaySettings)
    OverlaySettings.show()
    sys.exit(app.exec_())
