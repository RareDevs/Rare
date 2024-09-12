from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QHBoxLayout,
    QSpacerItem,
    QWidget,
)

from rare.utils.misc import qta_icon
from rare.widgets.elide_label import ElideLabel


class ListWidget(object):
    def __init__(self):
        self.title_label = None
        self.status_label = None
        self.tooltip_label = None
        self.install_btn = None
        self.launch_btn = None

        self.developer_label = None
        self.version_label = None
        self.size_label = None

    def setupUi(self, widget: QWidget):
        self.title_label = ElideLabel(parent=widget)
        self.title_label.setObjectName(f"{type(self).__name__}TitleLabel")
        self.title_label.setWordWrap(False)

        self.status_label = QLabel(parent=widget)
        self.status_label.setObjectName(f"{type(self).__name__}StatusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.tooltip_label = QLabel(parent=widget)
        self.tooltip_label.setObjectName(f"{type(self).__name__}TooltipLabel")
        self.tooltip_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.install_btn = QPushButton(parent=widget)
        self.install_btn.setObjectName(f"{type(self).__name__}Button")
        self.install_btn.setIcon(qta_icon("ri.install-line"))
        self.install_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.install_btn.setFixedWidth(120)

        self.launch_btn = QPushButton(parent=widget)
        self.launch_btn.setObjectName(f"{type(self).__name__}Button")
        self.launch_btn.setIcon(qta_icon("ei.play-alt"))
        self.launch_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.launch_btn.setFixedWidth(120)

        # lk: do not focus on button
        # When the button gets clicked on, it receives keyboard focus. Disabling the button
        # afterwards leads to `focusNextChild` getting called. This makes the scrollarea
        # trying to ensure that `nextChild` is visible, essentially scrolling to a random widget
        self.launch_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.install_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.developer_label = ElideLabel(parent=widget)
        self.developer_label.setObjectName(f"{type(self).__name__}InfoLabel")
        self.developer_label.setFixedWidth(120)

        self.version_label = ElideLabel(parent=widget)
        self.version_label.setObjectName(f"{type(self).__name__}InfoLabel")
        self.version_label.setFixedWidth(120)

        self.size_label = ElideLabel(parent=widget)
        self.size_label.setObjectName(f"{type(self).__name__}InfoLabel")
        self.size_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.size_label.setFixedWidth(60)

        # Create layouts
        left_layout = QVBoxLayout()
        left_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        bottom_layout = QHBoxLayout()
        bottom_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(3, 3, 3, 3)

        # Layout the widgets
        # (from inner to outer)
        left_layout.addWidget(self.title_label, stretch=1)

        bottom_layout.addWidget(self.developer_label, stretch=0, alignment=Qt.AlignmentFlag.AlignLeft)
        bottom_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
        bottom_layout.addWidget(self.version_label, stretch=0, alignment=Qt.AlignmentFlag.AlignLeft)
        bottom_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
        bottom_layout.addWidget(self.size_label, stretch=0, alignment=Qt.AlignmentFlag.AlignLeft)
        bottom_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
        bottom_layout.addWidget(self.status_label, stretch=0, alignment=Qt.AlignmentFlag.AlignLeft)
        bottom_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        bottom_layout.addWidget(self.tooltip_label, stretch=0, alignment=Qt.AlignmentFlag.AlignRight)

        left_layout.addLayout(bottom_layout)

        layout.addLayout(left_layout)
        layout.addWidget(self.install_btn, stretch=0, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.launch_btn, stretch=0, alignment=Qt.AlignmentFlag.AlignRight)

        widget.setLayout(layout)

        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        widget.setFixedHeight(widget.sizeHint().height())
        widget.leaveEvent(None)

        self.translateUi(widget)

    def translateUi(self, widget: QWidget):
        self.install_btn.setText(widget.tr("Install"))
