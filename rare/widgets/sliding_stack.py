from PyQt5.QtCore import (
    pyqtSlot,
    QEvent,
    QEasingCurve,
    QParallelAnimationGroup,
    QAbstractAnimation,
    QPropertyAnimation,
    Qt,
    QPoint,
)
from PyQt5.QtWidgets import QStackedWidget, QGestureEvent, QSwipeGesture


class SlidingStackedWidget(QStackedWidget):
    """
    Taken from: https://stackoverflow.com/a/52597972
    """

    def __init__(self, parent=None):
        super(SlidingStackedWidget, self).__init__(parent)

        self.m_direction = Qt.Horizontal
        self.m_speed = 500
        self.m_animationtype = QEasingCurve.OutBack
        self.m_now = 0
        self.m_next = 0
        self.m_wrap = False
        self.m_pnow = QPoint(0, 0)
        self.m_active = False

    def setDirection(self, direction: Qt.Orientation) -> None:
        self.m_direction = direction

    def setSpeed(self, speed: int) -> None:
        self.m_speed = speed

    def setAnimation(self, animationtype: QEasingCurve.Type) -> None:
        self.m_animationtype = animationtype

    def setWrap(self, wrap: bool) -> None:
        self.m_wrap = wrap

    @pyqtSlot()
    def slideInPrev(self):
        now = self.currentIndex()
        if self.m_wrap or now > 0:
            self.slideInIndex(now - 1)

    @pyqtSlot()
    def slideInNext(self):
        now = self.currentIndex()
        if self.m_wrap or now < (self.count() - 1):
            self.slideInIndex(now + 1)

    def slideInIndex(self, idx):
        if idx > (self.count() - 1):
            idx = idx % self.count()
        elif idx < 0:
            idx = (idx + self.count()) % self.count()
        self.slideInWidget(self.widget(idx))

    def slideInWidget(self, newwidget):
        if self.m_active:
            return

        self.m_active = True

        _now = self.currentIndex()
        _next = self.indexOf(newwidget)

        if _now == _next:
            self.m_active = False
            return

        offsetx, offsety = self.frameRect().width(), self.frameRect().height()
        self.widget(_next).setGeometry(self.frameRect())

        if not self.m_direction == Qt.Horizontal:
            if _now < _next:
                offsetx, offsety = 0, -offsety
            else:
                offsetx = 0
        else:
            if _now < _next:
                offsetx, offsety = -offsetx, 0
            else:
                offsety = 0

        pnext = self.widget(_next).pos()
        pnow = self.widget(_now).pos()
        self.m_pnow = pnow

        offset = QPoint(offsetx, offsety)
        self.widget(_next).move(pnext - offset)
        self.widget(_next).show()
        self.widget(_next).raise_()

        animgroup = QParallelAnimationGroup(self, finished=self.animationDoneSlot)

        for index, start, end in zip((_now, _next), (pnow, pnext - offset), (pnow + offset, pnext)):
            animation = QPropertyAnimation(
                self.widget(index),
                b"pos",
                duration=self.m_speed,
                easingCurve=self.m_animationtype,
                startValue=start,
                endValue=end,
            )
            animgroup.addAnimation(animation)

        self.m_next = _next
        self.m_now = _now
        self.m_active = True
        animgroup.start(QAbstractAnimation.DeleteWhenStopped)

    @pyqtSlot()
    def animationDoneSlot(self):
        self.setCurrentIndex(self.m_next)
        self.widget(self.m_now).hide()
        self.widget(self.m_now).move(self.m_pnow)
        self.m_active = False

    def event(self, e: QEvent):
        if e.type() == QEvent.Gesture:
            return self.gestureEvent(QGestureEvent(e))
        return super(SlidingStackedWidget, self).event(e)

    def gestureEvent(self, e: QGestureEvent):
        if swipe := e.gesture(Qt.SwipeGesture):
            self.swipeTriggered(swipe)
        return True

    def swipeTriggered(self, g: QSwipeGesture):
        if g.state() == Qt.GestureFinished:
            if g.horizontalDirection() == QSwipeGesture.Left:
                self.slideInPrev()
            else:
                self.slideInNext()
