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

from rare.utils.misc import icon
from rare.widgets.elide_label import ElideLabel


class IconWidget(object):
    def __init__(self):
        self._effect = None
        self._animation = None

        self.status_label = None
        self.mini_widget = None
        self.mini_effect = None
        self.title_label = None
        self.tooltip_label = None
        self.launch_btn = None
        self.install_btn = None

    def setupUi(self, widget: QWidget):
        # information at top
        self.status_label = ElideLabel(parent=widget)
        self.status_label.setObjectName(f"{type(self).__name__}StatusLabel")
        self.status_label.setStyleSheet(
            f"QLabel#{self.status_label.objectName()}"
            "{"
            "color: white;"
            "background-color: rgba(0, 0, 0, 65%);"
            "border-radius: 5%;"
            "border-top-left-radius: 11%;"
            "border-top-right-radius: 11%;"
            "}"
        )
        self.status_label.setContentsMargins(6, 6, 6, 6)
        self.status_label.setAutoFillBackground(False)

        # on-hover popup
        self.mini_widget = QWidget(parent=widget)
        self.mini_widget.setObjectName(f"{type(self).__name__}MiniWidget")
        self.mini_widget.setStyleSheet(
            f"QWidget#{self.mini_widget.objectName()}"
            "{"
            "color: rgb(238, 238, 238);"
            "background-color: rgba(0, 0, 0, 65%);"
            "border-radius: 5%;"
            "border-bottom-left-radius: 9%;"
            "border-bottom-right-radius: 9%;"
            "}"
        )
        self.mini_widget.setFixedHeight(widget.height() // 3)

        self.mini_effect = QGraphicsOpacityEffect(self.mini_widget)
        self.mini_widget.setGraphicsEffect(self.mini_effect)

        # game title
        self.title_label = QLabel(parent=self.mini_widget)
        self.title_label.setObjectName(f"{type(self).__name__}TitleLabel")
        self.title_label.setStyleSheet(
            f"QLabel#{self.title_label.objectName()}"
            "{"
            "background-color: rgba(0, 0, 0, 0%); color: white;"
            "}"
        )
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.title_label.setAlignment(Qt.AlignTop)
        self.title_label.setAutoFillBackground(False)
        self.title_label.setWordWrap(True)

        # information below title
        self.tooltip_label = ElideLabel(parent=self.mini_widget)
        self.tooltip_label.setObjectName(f"{type(self).__name__}StatusLabel")
        self.tooltip_label.setStyleSheet(
            f"QLabel#{self.tooltip_label.objectName()}"
            "{"
            "background-color: rgba(0, 0, 0, 0%); color: white;"
            "}"
        )
        self.tooltip_label.setAutoFillBackground(False)

        # play button
        self.launch_btn = QPushButton(parent=self.mini_widget)
        self.launch_btn.setObjectName(f"{type(self).__name__}LaunchButton")
        self.launch_btn.setStyleSheet(
            f"QPushButton#{self.launch_btn.objectName()}"
            "{"
            "border-radius: 10%;"
            "background-color: rgba(0, 0, 0, 65%);"
            "border-color: black; border-width: 1px;"
            "}"
            f"QPushButton#{self.launch_btn.objectName()}::hover"
            "{"
            "border-color: gray;"
            "}"
        )
        self.launch_btn.setIcon(icon("ei.play-alt", color="white"))
        self.launch_btn.setIconSize(QSize(20, 20))
        self.launch_btn.setFixedSize(QSize(widget.width() // 4, widget.width() // 4))

        self.install_btn = QPushButton(parent=self.mini_widget)
        self.install_btn.setObjectName(f"{type(self).__name__}InstallButton")
        self.install_btn.setStyleSheet(
            f"QPushButton#{self.install_btn.objectName()}"
            "{"
            "border-radius: 10%;"
            "background-color: rgba(0, 0, 0, 65%);"
            "border-color: black; border-width: 1px;"
            "}"
            f"QPushButton#{self.install_btn.objectName()}::hover"
            "{"
            "border-color: gray;"
            "}"
        )
        self.install_btn.setIcon(icon("ri.install-fill", color="white"))
        self.install_btn.setIconSize(QSize(20, 20))
        self.install_btn.setFixedSize(QSize(widget.width() // 4, widget.width() // 4))

        # Create layouts
        # layout for the whole widget, holds the image
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSizeConstraint(QVBoxLayout.SetFixedSize)

        # layout for the image, holds the mini widget and a spacer item
        image_layout = QVBoxLayout()
        image_layout.setContentsMargins(0, 0, 0, 0)

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

        # layout.addWidget(widget.image)
        # widget.setLayout(layout)

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
