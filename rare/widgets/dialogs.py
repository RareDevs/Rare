import sys
from abc import abstractmethod

from PyQt5.QtCore import Qt, pyqtSlot, QCoreApplication, QSize
from PyQt5.QtGui import QCloseEvent, QKeyEvent, QKeySequence
from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QApplication,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QLayout, QSpacerItem, QSizePolicy,
)

from rare.utils.misc import icon


def dialog_title_game(text: str, app_title: str) -> str:
    return f"{text} '{app_title}'"


def dialog_title(text: str) -> str:
    return f"{text} - {QCoreApplication.instance().applicationName()}"


class BaseDialog(QDialog):

    def __init__(self, parent=None):
        super(BaseDialog, self).__init__(parent=parent)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.setWindowModality(Qt.WindowModal)

    def setWindowTitle(self, a0):
        super().setWindowTitle(dialog_title(a0))

    def exec(self):
        raise RuntimeError(f"Don't use `exec()` with {type(self).__name__}")

    def exec_(self):
        raise RuntimeError(f"Don't use `exec_()` with {type(self).__name__}")

    # lk: because you will eventually find yourself back here.
    # on QDialogs the Esc key closes the dialog through keyPressEvent(),
    # which ultimately call `reject()`. Pressing the Enter/Return button
    # is a shortcut for pressing the default button and thus calling `accept()`
    # In turn  both `accept()` and `reject()` evetually call `done()`.

    # In the base dialog ignore both. In the subclasses, call the method
    # from QDialog if required, not this one.
    # `super(BaseDialog, self).keyPressEvent(a0)`
    def keyPressEvent(self, a0: QKeyEvent) -> None:
        if a0.matches(QKeySequence.Cancel):
            a0.ignore()
            return
        if a0.key() == Qt.Key_Enter or a0.key() == Qt.Key_Return:
            a0.ignore()
            return
        super().keyPressEvent(a0)

    # Using the 'X' button on the window manager comes directly here.
    # It is a spontaneous event so simply ignore it.
    def closeEvent(self, a0: QCloseEvent) -> None:
        if a0.spontaneous():
            a0.ignore()
            return
        super().closeEvent(a0)


class ButtonDialog(BaseDialog):

    def __init__(self, parent=None):
        super(ButtonDialog, self).__init__(parent=parent)

        self.reject_button = QPushButton(self)
        self.reject_button.setText(self.tr("Cancel"))
        self.reject_button.setIcon(icon("fa.remove"))
        self.reject_button.setAutoDefault(False)
        self.reject_button.clicked.connect(self.reject)

        self.accept_button = QPushButton(self)
        self.accept_button.setAutoDefault(False)
        self.accept_button.clicked.connect(self.accept)

        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.reject_button)
        self.button_layout.addStretch(20)
        self.button_layout.addStretch(1)
        self.button_layout.addWidget(self.accept_button)

        self.main_layout = QVBoxLayout(self)
        # lk: dirty way to set a minimum width with fixed size constraint
        spacer = QSpacerItem(
            480, self.main_layout.spacing(),
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )
        self.main_layout.addItem(spacer)
        self.main_layout.addLayout(self.button_layout)
        self.main_layout.setSizeConstraint(QLayout.SetFixedSize)

    def close(self):
        raise RuntimeError(f"Don't use `close()` with {type(self).__name__}")

    def setCentralWidget(self, widget: QWidget):
        widget.layout().setContentsMargins(0, 0, 0, 0)
        self.main_layout.insertWidget(0, widget)

    def setCentralLayout(self, layout: QLayout):
        layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.insertLayout(0, layout)

    @abstractmethod
    def accept_handler(self):
        raise NotImplementedError

    @abstractmethod
    def reject_handler(self):
        raise NotImplementedError

    @abstractmethod
    def done_handler(self):
        raise NotImplementedError

    # These only apply to QDialog. If we move to QWidget for embedded dialogs
    # we have to use close() and custom handling.

    # lk: Override accept to run our abstract handling method
    def accept(self):
        self.accept_handler()
        super().accept()

    # lk: Override reject to run our abstract handling method
    def reject(self):
        self.reject_handler()
        super().reject()

    # lk: Override `done()` to to run our abstract handling method
    def done(self, a0):
        self.done_handler()
        super().done(a0)

    # lk: Ignore BaseDialog::keyPressEvent and call QDialog::keyPressEvent
    # because we handle accept and reject here.
    def keyPressEvent(self, a0: QKeyEvent) -> None:
        super(BaseDialog, self).keyPressEvent(a0)

    # lk: Ignore BaseDialog::closeEvent and call QDialog::closeEvent
    # because we handle accept and reject here.
    def closeEvent(self, a0: QCloseEvent) -> None:
        super(BaseDialog, self).closeEvent(a0)


class ActionDialog(ButtonDialog):
    def __init__(self, parent=None):
        super(ActionDialog, self).__init__(parent=parent)
        self.__reject_close = False

        self.action_button = QPushButton(self)
        self.action_button.setAutoDefault(True)
        self.action_button.clicked.connect(self.action)

        self.button_layout.insertWidget(2, self.action_button)

    def active(self) -> bool:
        return self.__reject_close

    def setActive(self, active: bool):
        self.reject_button.setDisabled(active)
        self.action_button.setDisabled(active)
        self.accept_button.setDisabled(active)
        self.__reject_close = active

    @abstractmethod
    def action_handler(self):
        raise NotImplementedError

    @pyqtSlot()
    def action(self):
        self.setActive(True)
        self.action_handler()

    # lk: Ignore all key presses if there is an ongoing action
    def keyPressEvent(self, a0: QKeyEvent) -> None:
        if self.__reject_close:
            a0.ignore()
            return
        super(BaseDialog, self).keyPressEvent(a0)

    # lk: Ignore all closeEvents if there is an ongoing action
    def closeEvent(self, a0: QCloseEvent) -> None:
        if self.__reject_close:
            a0.ignore()
            return
        super(BaseDialog, self).closeEvent(a0)


__all__ = ["dialog_title", "dialog_title_game", "BaseDialog", "ButtonDialog", "ActionDialog"]


class TestDialog(BaseDialog):
    def __init__(self, parent=None):
        super(TestDialog, self).__init__(parent=parent)

        self.accept_button = QPushButton("accept", self)
        self.reject_button = QPushButton("reject", self)
        self.action_button = QPushButton("action", self)
        self.button_box = QDialogButtonBox(Qt.Horizontal, self)
        self.button_box.addButton(self.accept_button, QDialogButtonBox.AcceptRole)
        self.button_box.addButton(self.reject_button, QDialogButtonBox.RejectRole)
        self.button_box.addButton(self.action_button, QDialogButtonBox.ActionRole)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.button_box)

        self.setMinimumWidth(480)

    def setWindowTitle(self, a0):
        super().setWindowTitle(dialog_title(a0))

    def close(self):
        print("in close")
        super().close()

    def closeEvent(self, a0: QCloseEvent) -> None:
        print("in closeEvent")
        if a0.spontaneous():
            print("is spontaneous")
            a0.ignore()
            return
        if self.reject_close:
            a0.ignore()
        else:
            self._on_close()
            super().closeEvent(a0)
        # super().closeEvent(a0)

    def done(self, a0):
        print(f"in done {a0}")
        return
        super().done(a0)

    def accept(self):
        print("in accept")
        self._on_accept()
        # return
        # super().accept()

    def reject(self):
        print("in reject")
        self._on_reject()
        # return
        # super().reject()

    def _on_close(self):
        print("in _on_close")

    def _on_accept(self):
        print("in _on_accepted")
        # self.close()

    def _on_reject(self):
        print("in _on_rejected")
        self.close()

    def keyPressEvent(self, a0: QKeyEvent) -> None:
        super(BaseDialog, self).keyPressEvent(a0)


def test_dialog():
    app = QApplication(sys.argv)
    dlg = TestDialog(None)
    dlg.show()
    ret = app.exec()
    sys.exit(ret)


if __name__ == "__main__":
    test_dialog()
