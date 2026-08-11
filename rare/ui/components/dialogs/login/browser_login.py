
################################################################################
## Form generated from reading UI file 'browser_login.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class Ui_BrowserLogin:
    def setupUi(self, BrowserLogin):
        if not BrowserLogin.objectName():
            BrowserLogin.setObjectName("BrowserLogin")
        BrowserLogin.resize(310, 237)
        BrowserLogin.setWindowTitle("BrowserLogin")
        self.main_layout = QVBoxLayout(BrowserLogin)
        self.main_layout.setObjectName("main_layout")
        self.title_label = QLabel(BrowserLogin)
        self.title_label.setObjectName("title_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.title_label.sizePolicy().hasHeightForWidth())
        self.title_label.setSizePolicy(sizePolicy)
        font = QFont()
        font.setBold(True)
        self.title_label.setFont(font)

        self.main_layout.addWidget(self.title_label, 0, Qt.AlignmentFlag.AlignTop)

        self.form_widget = QWidget(BrowserLogin)
        self.form_widget.setObjectName("form_widget")
        self.form_layout = QFormLayout(self.form_widget)
        self.form_layout.setObjectName("form_layout")
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.form_layout.setContentsMargins(0, 0, 0, 0)
        self.open_button = QPushButton(self.form_widget)
        self.open_button.setObjectName("open_button")

        self.form_layout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.open_button)

        self.link_layout = QHBoxLayout()
        self.link_layout.setObjectName("link_layout")
        self.link_layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.link_text = QLineEdit(self.form_widget)
        self.link_text.setObjectName("link_text")
        self.link_text.setText("")
        self.link_text.setReadOnly(True)
        self.link_text.setPlaceholderText("")

        self.link_layout.addWidget(self.link_text)

        self.copy_button = QPushButton(self.form_widget)
        self.copy_button.setObjectName("copy_button")
        self.copy_button.setText("")

        self.link_layout.addWidget(self.copy_button)

        self.link_layout.setStretch(0, 1)

        self.form_layout.setLayout(0, QFormLayout.ItemRole.FieldRole, self.link_layout)

        self.sid_label = QLabel(self.form_widget)
        self.sid_label.setObjectName("sid_label")
        self.sid_label.setText("authorizationCode")
        self.sid_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.form_layout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.sid_label)

        self.status_field = QLabel(self.form_widget)
        self.status_field.setObjectName("status_field")
        self.status_field.setFrameShape(QFrame.Shape.StyledPanel)
        self.status_field.setFrameShadow(QFrame.Shadow.Sunken)
        self.status_field.setText("")
        self.status_field.setWordWrap(True)

        self.form_layout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.status_field)

        self.status_label = QLabel(self.form_widget)
        self.status_label.setObjectName("status_label")

        self.form_layout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.status_label)


        self.main_layout.addWidget(self.form_widget, 0, Qt.AlignmentFlag.AlignTop)

        self.main_layout.setStretch(1, 1)

        self.retranslateUi(BrowserLogin)
    # setupUi

    def retranslateUi(self, BrowserLogin):
        self.title_label.setText(QCoreApplication.translate("BrowserLogin", "Login through browser", None))
        self.open_button.setText(QCoreApplication.translate("BrowserLogin", "Open Browser", None))
        self.status_label.setText(QCoreApplication.translate("BrowserLogin", "Status", None))
    # retranslateUi

