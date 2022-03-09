# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'rare/ui/components/tabs/settings/overlay.ui'
#
# Created by: PyQt5 UI code generator 5.15.6
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_OverlaySettings(object):
    def setupUi(self, OverlaySettings):
        OverlaySettings.setObjectName("OverlaySettings")
        OverlaySettings.resize(555, 188)
        OverlaySettings.setWindowTitle("Overlay Settings")
        OverlaySettings.setTitle("")
        self.dxvk_layout = QtWidgets.QGridLayout(OverlaySettings)
        self.dxvk_layout.setObjectName("dxvk_layout")
        self.lbl_show_overlay = QtWidgets.QLabel(OverlaySettings)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lbl_show_overlay.sizePolicy().hasHeightForWidth())
        self.lbl_show_overlay.setSizePolicy(sizePolicy)
        self.lbl_show_overlay.setObjectName("lbl_show_overlay")
        self.dxvk_layout.addWidget(self.lbl_show_overlay, 0, 0, 1, 1)
        self.show_overlay_combo = QtWidgets.QComboBox(OverlaySettings)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.show_overlay_combo.sizePolicy().hasHeightForWidth())
        self.show_overlay_combo.setSizePolicy(sizePolicy)
        self.show_overlay_combo.setObjectName("show_overlay_combo")
        self.show_overlay_combo.addItem("")
        self.show_overlay_combo.addItem("")
        self.show_overlay_combo.addItem("")
        self.dxvk_layout.addWidget(self.show_overlay_combo, 0, 1, 1, 2)
        self.gb_options = QtWidgets.QGroupBox(OverlaySettings)
        self.gb_options.setTitle("")
        self.gb_options.setObjectName("gb_options")
        self.gridLayout = QtWidgets.QGridLayout(self.gb_options)
        self.gridLayout.setObjectName("gridLayout")
        self.options_form = QtWidgets.QFormLayout()
        self.options_form.setObjectName("options_form")
        self.gridLayout.addLayout(self.options_form, 1, 0, 1, 1)
        self.options_grid = QtWidgets.QGridLayout()
        self.options_grid.setObjectName("options_grid")
        self.gridLayout.addLayout(self.options_grid, 0, 0, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 0, 1, 2, 1)
        self.dxvk_layout.addWidget(self.gb_options, 2, 0, 1, 3)

        self.retranslateUi(OverlaySettings)
        QtCore.QMetaObject.connectSlotsByName(OverlaySettings)

    def retranslateUi(self, OverlaySettings):
        _translate = QtCore.QCoreApplication.translate
        self.lbl_show_overlay.setText(_translate("OverlaySettings", "Show HUD"))
        self.show_overlay_combo.setItemText(0, _translate("OverlaySettings", "System Default"))
        self.show_overlay_combo.setItemText(1, _translate("OverlaySettings", "Hidden"))
        self.show_overlay_combo.setItemText(2, _translate("OverlaySettings", "Visible"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    OverlaySettings = QtWidgets.QGroupBox()
    ui = Ui_OverlaySettings()
    ui.setupUi(OverlaySettings)
    OverlaySettings.show()
    sys.exit(app.exec_())