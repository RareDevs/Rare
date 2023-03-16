from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGraphicsOpacityEffect,
    QSpacerItem,
    QSizePolicy,
    QHBoxLayout,
    QLabel,
    QPushButton,
)

from rare.utils.misc import icon, widget_object_name
from rare.widgets.elide_label import ElideLabel


class IconWidget(object):
    def __init__(self):
        self._effect = None
        self._animation: QPropertyAnimation = None

        self.status_label: ElideLabel = None
        self.mini_widget: QWidget = None
        self.mini_effect: QGraphicsOpacityEffect = None
        self.title_label: QLabel = None
        self.tooltip_label: ElideLabel = None
        self.launch_btn: QPushButton = None
        self.install_btn: QPushButton = None

    def setupUi(self, widget: QWidget):
        # information at top
        self.status_label = ElideLabel(parent=widget)
        self.status_label.setObjectName(f"{type(self).__name__}StatusLabel")
        self.status_label.setFixedHeight(False)
        self.status_label.setContentsMargins(6, 6, 6, 6)
        self.status_label.setAutoFillBackground(False)

        # on-hover popup
        self.mini_widget = QWidget(parent=widget)
        self.mini_widget.setObjectName(f"{type(self).__name__}MiniWidget")
        self.mini_widget.setFixedHeight(widget.height() // 3)

        self.mini_effect = QGraphicsOpacityEffect(self.mini_widget)
        self.mini_widget.setGraphicsEffect(self.mini_effect)

        # game title
        self.title_label = QLabel(parent=self.mini_widget)
        self.title_label.setObjectName(f"{type(self).__name__}TitleLabel")
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.title_label.setAlignment(Qt.AlignVCenter)
        self.title_label.setAutoFillBackground(False)
        self.title_label.setWordWrap(True)

        # information below title
        self.tooltip_label = ElideLabel(parent=self.mini_widget)
        self.tooltip_label.setObjectName(f"{type(self).__name__}TooltipLabel")
        self.tooltip_label.setAutoFillBackground(False)

        # play button
        self.launch_btn = QPushButton(parent=self.mini_widget)
        self.launch_btn.setObjectName(f"{type(self).__name__}Button")
        self.launch_btn.setIcon(icon("ei.play-alt", color="white"))
        self.launch_btn.setIconSize(QSize(20, 20))
        self.launch_btn.setFixedSize(QSize(widget.width() // 4, widget.width() // 4))

        self.install_btn = QPushButton(parent=self.mini_widget)
        self.install_btn.setObjectName(f"{type(self).__name__}Button")
        self.install_btn.setIcon(icon("ri.install-fill", color="white"))
        self.install_btn.setIconSize(QSize(20, 20))
        self.install_btn.setFixedSize(QSize(widget.width() // 4, widget.width() // 4))

        # lk: do not focus on button
        # When the button gets clicked on, it receives keyboard focus. Disabling the button
        # afterwards leads to `focusNextChild` getting called. This makes the scrollarea
        # trying to ensure that `nextChild` is visible, essentially scrolling to a random widget
        self.launch_btn.setFocusPolicy(Qt.NoFocus)
        self.install_btn.setFocusPolicy(Qt.NoFocus)

        # Create layouts
        # layout on top of the image, holds the status label, a spacer item and the mini widget
        image_layout = QVBoxLayout()
        image_layout.setContentsMargins(2, 2, 2, 2)

        # layout for the mini widget, holds the top row and the info label
        mini_layout = QVBoxLayout()
        mini_layout.setSpacing(0)

        # layout for the top row, holds the title and the launch button
        row_layout = QHBoxLayout()
        row_layout.setSpacing(0)
        row_layout.setAlignment(Qt.AlignTop)

        # Layout the widgets
        # (from inner to outer)
        row_layout.addWidget(self.title_label, stretch=2)
        row_layout.addWidget(self.launch_btn)
        row_layout.addWidget(self.install_btn)
        mini_layout.addLayout(row_layout, stretch=2)
        mini_layout.addWidget(self.tooltip_label)
        self.mini_widget.setLayout(mini_layout)

        image_layout.addWidget(self.status_label)
        image_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding))
        image_layout.addWidget(self.mini_widget)
        widget.setLayout(image_layout)

        widget.setContextMenuPolicy(Qt.ActionsContextMenu)
        widget.leaveEvent(None)

        self.translateUi(widget)

    def translateUi(self, widget: QWidget):
        pass

    def enterAnimation(self, widget: QWidget):
        self._animation = QPropertyAnimation(self.mini_effect, b"opacity")
        self._animation.setDuration(250)
        self._animation.setStartValue(0)
        self._animation.setEndValue(1)
        self._animation.setEasingCurve(QEasingCurve.InSine)
        self._animation.start(QPropertyAnimation.DeleteWhenStopped)

    def leaveAnimation(self, widget: QWidget):
        self._animation = QPropertyAnimation(self.mini_effect, b"opacity")
        self._animation.setDuration(150)
        self._animation.setStartValue(1)
        self._animation.setEndValue(0)
        self._animation.setEasingCurve(QEasingCurve.OutSine)
        self._animation.start(QPropertyAnimation.DeleteWhenStopped)
