from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QHBoxLayout,
    QSpacerItem,
    QWidget,
)

from rare.utils.misc import icon
from rare.widgets.elide_label import ElideLabel


class ListWidget(object):
    def __init__(self):
        self.title_label = None
        self.status_label = None
        self.tooltip_label = None
        self.install_btn = None
        self.launch_btn = None

        self.developer_text = None
        self.version_text = None
        self.size_text = None

    def setupUi(self, widget: QWidget):
        self.title_label = QLabel(parent=widget)
        self.title_label.setWordWrap(False)

        self.status_label = QLabel(parent=widget)
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.status_label.setStyleSheet(
            "background-color: rgba(0,0,0,75%);"
            "border: 1px solid black;"
            "border-radius: 5px;"
        )

        self.tooltip_label = QLabel(parent=widget)
        self.tooltip_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.tooltip_label.setStyleSheet(
            "background-color: rgba(0,0,0,75%);"
            "border: 1px solid black;"
            "border-radius: 5px;"
        )

        self.install_btn = QPushButton(parent=widget)
        self.install_btn.setIcon(icon("ri.install-fill"))
        self.install_btn.setStyleSheet("text-align:left")
        self.install_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.install_btn.setFixedWidth(120)

        self.launch_btn = QPushButton(parent=widget)
        self.launch_btn.setIcon(icon("ei.play-alt"))
        self.launch_btn.setStyleSheet("text-align:left")
        self.launch_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.launch_btn.setFixedWidth(120)

        # self.info_btn = QPushButton(parent=widget)
        # self.info_btn.setIcon(icon("ei.info-circle"))
        # self.info_btn.setStyleSheet("text-align:left")
        # self.info_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # self.info_btn.setFixedWidth(120)

        font = QFont()
        font.setBold(True)
        # font.setWeight(75)

        # self.developer_label = QLabel(parent=widget)
        # self.developer_label.setStyleSheet(f"color: #999;")
        # self.developer_label.setFont(font)
        self.developer_text = ElideLabel(parent=widget)
        self.developer_text.setFixedWidth(120)
        self.developer_text.setStyleSheet(f"color: #999;")

        # self.version_label = QLabel(parent=widget)
        # self.version_label.setStyleSheet(f"color: #999;")
        # self.version_label.setFont(font)
        self.version_text = ElideLabel(parent=widget)
        self.version_text.setFixedWidth(120)
        self.version_text.setStyleSheet(f"color: #999;")

        # self.size_label = QLabel(parent=widget)
        # self.size_label.setStyleSheet(f"color: #999;")
        # self.size_label.setFont(font)
        self.size_text = ElideLabel(parent=widget)
        self.size_text.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.size_text.setFixedWidth(60)
        self.size_text.setStyleSheet(f"color: #999;")

        # Create layouts
        top_layout = QHBoxLayout()
        top_layout.setAlignment(Qt.AlignLeft)

        bottom_layout = QHBoxLayout()
        bottom_layout.setAlignment(Qt.AlignRight)

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(3, 3, 3, 3)

        # Layout the widgets
        # (from inner to outer)
        top_layout.addWidget(self.title_label, stretch=1)
        # top_layout.addWidget(self.status_label, stretch=0)

        bottom_layout.addWidget(self.developer_text, stretch=0, alignment=Qt.AlignLeft)
        bottom_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        bottom_layout.addWidget(self.version_text, stretch=0, alignment=Qt.AlignLeft)
        bottom_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        bottom_layout.addWidget(self.size_text, stretch=0, alignment=Qt.AlignLeft)
        bottom_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        bottom_layout.addWidget(self.status_label, stretch=0, alignment=Qt.AlignLeft)
        bottom_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        bottom_layout.addWidget(self.tooltip_label, stretch=0, alignment=Qt.AlignRight)
        # bottom_layout.addWidget(self.info_btn, stretch=0, alignment=Qt.AlignRight)
        bottom_layout.addWidget(self.install_btn, stretch=0, alignment=Qt.AlignRight)
        bottom_layout.addWidget(self.launch_btn, stretch=0, alignment=Qt.AlignRight)

        layout.addLayout(top_layout)
        layout.addLayout(bottom_layout)

        widget.setLayout(layout)

        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        widget.leaveEvent(None)

        # lk: for debug, DO NOT REMOVE
        # self.image.setObjectName(f"{type(self).__name__}_image")
        # self.title_label.setObjectName(f"{type(self).__name__}_title_label")
        # self.status_label.setObjectName(f"{type(self).__name__}_status_label")
        # self.status_label.setObjectName(f"{type(self).__name__}_progress")
        # self.install_btn.setObjectName(f"{type(self).__name__}_install_btn")
        # self.launch_btn.setObjectName(f"{type(self).__name__}_launch_btn")
        # self.info_btn.setObjectName(f"{type(self).__name__}_info_btn")
        # self.developer_label.setObjectName(f"{type(self).__name__}_developer_label")
        # self.developer_text.setObjectName(f"{type(self).__name__}_developer_text")
        # self.version_label.setObjectName(f"{type(self).__name__}_version_label")
        # self.version_text.setObjectName(f"{type(self).__name__}_version_text")
        # self.size_label.setObjectName(f"{type(self).__name__}_size_label")
        # self.size_text.setObjectName(f"{type(self).__name__}_size_text")
        # middle_layout.setObjectName(f"{type(self).__name__}_info_layout")
        # form_layout.setObjectName(f"{type(self).__name__}_form_layout")
        # right_layout.setObjectName(f"{type(self).__name__}_button_layout")
        # right_layout.setObjectName(f"{type(self).__name__}_right_layout")
        # layout.setObjectName(f"{type(self).__name__}_layout")

        self.translateUi(widget)

    def translateUi(self, widget: QWidget):
        # self.info_btn.setText(widget.tr("Information"))
        self.install_btn.setText(widget.tr("Install"))
        # self.developer_label.setText(widget.tr("Developer"))
        # self.version_label.setText(widget.tr("Version"))
        # self.size_label.setText(widget.tr("Installed size"))
