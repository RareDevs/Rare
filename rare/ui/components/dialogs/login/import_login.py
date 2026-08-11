
################################################################################
## Form generated from reading UI file 'import_login.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QComboBox, QFormLayout, QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget


class Ui_ImportLogin:
    def setupUi(self, ImportLogin):
        if not ImportLogin.objectName():
            ImportLogin.setObjectName("ImportLogin")
        ImportLogin.resize(256, 128)
        ImportLogin.setWindowTitle("ImportLogin")
        self.main_layout = QVBoxLayout(ImportLogin)
        self.main_layout.setObjectName("main_layout")
        self.title_label = QLabel(ImportLogin)
        self.title_label.setObjectName("title_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.title_label.sizePolicy().hasHeightForWidth())
        self.title_label.setSizePolicy(sizePolicy)
        font = QFont()
        font.setBold(True)
        self.title_label.setFont(font)

        self.main_layout.addWidget(self.title_label)

        self.form_widget = QWidget(ImportLogin)
        self.form_widget.setObjectName("form_widget")
        self.form_layout = QFormLayout(self.form_widget)
        self.form_layout.setObjectName("form_layout")
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.form_layout.setContentsMargins(0, 0, 0, 0)
        self.prefix_label = QLabel(self.form_widget)
        self.prefix_label.setObjectName("prefix_label")

        self.form_layout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.prefix_label)

        self.prefix_layout = QHBoxLayout()
        self.prefix_layout.setObjectName("prefix_layout")
        self.prefix_combo = QComboBox(self.form_widget)
        self.prefix_combo.setObjectName("prefix_combo")
        self.prefix_combo.setEditable(True)
        self.prefix_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.prefix_combo.setFrame(True)

        self.prefix_layout.addWidget(self.prefix_combo)

        self.prefix_button = QPushButton(self.form_widget)
        self.prefix_button.setObjectName("prefix_button")

        self.prefix_layout.addWidget(self.prefix_button)

        self.prefix_layout.setStretch(0, 1)

        self.form_layout.setLayout(0, QFormLayout.ItemRole.FieldRole, self.prefix_layout)

        self.status_field = QLabel(self.form_widget)
        self.status_field.setObjectName("status_field")
        self.status_field.setFrameShape(QFrame.Shape.StyledPanel)
        self.status_field.setFrameShadow(QFrame.Shadow.Sunken)
        self.status_field.setText("")
        self.status_field.setWordWrap(True)

        self.form_layout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.status_field)

        self.status_label = QLabel(self.form_widget)
        self.status_label.setObjectName("status_label")

        self.form_layout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.status_label)


        self.main_layout.addWidget(self.form_widget, 0, Qt.AlignmentFlag.AlignTop)

        self.main_layout.setStretch(1, 1)

        self.retranslateUi(ImportLogin)
    # setupUi

    def retranslateUi(self, ImportLogin):
        self.title_label.setText(QCoreApplication.translate("ImportLogin", "Import existing session from EGL", None))
        self.prefix_label.setText(QCoreApplication.translate("ImportLogin", "Select prefix", None))
        self.prefix_button.setText(QCoreApplication.translate("ImportLogin", "Browse...", None))
        self.status_label.setText(QCoreApplication.translate("ImportLogin", "Status", None))
    # retranslateUi

