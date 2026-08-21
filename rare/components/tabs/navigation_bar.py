from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPropertyAnimation,
    QRect,
    QSize,
    Qt,
)
from PySide6.QtGui import QColor, QFontMetrics, QIcon, QMouseEvent, QPainter, QPalette, QPixmap
from PySide6.QtWidgets import (
    QStyle,
    QStyleOptionTab,
    QStylePainter,
    QTabBar,
    QWidget,
)


class NavigationBar(QTabBar):

    def __init__(self, parent: QWidget | None = None):
        super(NavigationBar, self).__init__(parent=parent)
        self.setObjectName(type(self).__name__)
        self._margin = 8
        self.setShape(QTabBar.Shape.RoundedWest)
        self.setExpanding(False)
        self.setMovable(False)
        self.setDrawBase(False)
        self.setUsesScrollButtons(False)
        self.setIconSize(QSize(24, 24))
        self.setMouseTracking(True)

        self._progress: float = 0.0
        self._spacer_index: int = -1
        self._spacer_height: int = 0
        self._hover_index: int = -1

        self._animation = QPropertyAnimation(self, b'collapseProgress', self)
        self._animation.setDuration(180)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self.collapse_index: int | None = None
        self.expanded_index: int | None = None

    def is_collapsed(self) -> bool:
        return self._progress > 0.5

    @property
    def _collapsed(self) -> bool:
        return self._progress > 0.5

    def set_collapsed(self, collapsed: bool, animate: bool = True) -> None:
        self._animation.stop()
        if animate:
            self._animation.setStartValue(self._progress)
            self._animation.setEndValue(1.0 if collapsed else 0.0)
            self._animation.start()
        else:
            self._set_progress(1.0 if collapsed else 0.0)

    def toggle_collapsed(self) -> None:
        self.set_collapsed(not self.is_collapsed())

    def set_spacer_index(self, index: int) -> None:
        self._spacer_index = index

    def _collapsed_width(self) -> int:
        return self.iconSize().width() + self._margin * 2

    def _expanded_width(self) -> int:
      return max(
          QTabBar.tabSizeHint(self, x).height() for x in range(self.count())
      )

    def _natural_height(self) -> int:
        fm = QFontMetrics(self.font())
        tabs = self.count() - (1 if self._spacer_index >= 0 else 0)
        return tabs * (fm.height() + 18)

    def resizeEvent(self, event):
        self._spacer_height = max(0, self.height() - self._natural_height())
        return super(NavigationBar, self).resizeEvent(event)

    def leaveEvent(self, event):
        if self._hover_index != -1:
            self._hover_index = -1
            self.update()
        return super(NavigationBar, self).leaveEvent(event)

    def mouseMoveEvent(self, event):
        index = self.tabAt(event.pos())
        if index != self._hover_index:
            self._hover_index = index
            self.update()
        return super(NavigationBar, self).mouseMoveEvent(event)

    def mousePressEvent(self, e: QMouseEvent, /) -> None:
        if e.type() == QMouseEvent.Type.MouseButtonPress:
            index = self.tabAt(e.pos())
            if index == self.collapse_index and e.button() == Qt.MouseButton.LeftButton:
                self.toggle_collapsed()
                e.setAccepted(True)
                return
        super().mousePressEvent(e)

    def _get_progress(self) -> float:
        return self._progress

    def _set_progress(self, value: float) -> None:
        self._progress = float(value)
        self.updateGeometry()
        self.update()

    collapseProgress = Property(float, _get_progress, _set_progress)

    def tabSizeHint(self, index):
        fm = QFontMetrics(self.font())
        height = fm.height() + 18
        if index == self.expanded_index:
            offset = self.height()
            for _tab_index in range(self.count()):
                offset -= height
            height = max(height, height + offset)
        width = round(self._expanded_width() + (self._collapsed_width() - self._expanded_width()) * self._progress)
        return QSize(width, height)

    def sizeHint(self):
        if not self.count():
            return QSize(self._collapsed_width() + 150, 30)
        width = max(self.tabSizeHint(i).width() for i in range(self.count()))
        return QSize(width, self._natural_height())

    def minimumSizeHint(self):
        return self.sizeHint()

    def paintEvent(self, event):
        painter = QStylePainter(self)
        opt = QStyleOptionTab()
        pal = self.palette()

        for i in range(self.count()):
            if i == self._spacer_index:
                continue
            rect = self.tabRect(i)
            self.initStyleOption(opt, i)
            hovered = i == self._hover_index and not self._collapsed
            disabled = not self.isTabEnabled(i)
            if hovered:
                opt.state |= QStyle.StateFlag.State_MouseOver
            self.style().drawControl(QStyle.ControlElement.CE_TabBarTabShape, opt, painter, self)

            tab_icon = self.tabIcon(i)
            tab_text = '' if self._collapsed else self.tabText(i)
            self._draw_tab_label(
                painter, rect, tab_icon, tab_text, pal.color(QPalette.ColorRole.WindowText), disabled
            )

    def _tint_icon(self, icon: QIcon, color: QColor, size: QSize) -> QIcon:
        pm = icon.pixmap(size, QIcon.Mode.Normal)
        if pm.isNull():
            return icon
        tinted = QPixmap(pm.size())
        tinted.fill(Qt.GlobalColor.transparent)
        p = QPainter(tinted)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        p.drawPixmap(0, 0, pm)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        p.fillRect(tinted.rect(), color)
        p.end()
        return QIcon(tinted)

    def _draw_tab_label(self, painter, rect, icon, text, color, disabled: bool) -> None:
        icon_size = self.iconSize()
        painter.save()
        draw_color = QColor(color)
        if disabled:
            draw_color.setAlpha(120)
        paint_icon = self._tint_icon(icon, draw_color, icon_size)
        if not text:
            paint_icon.paint(
                painter,
                QRect(
                    rect.center().x() - icon_size.width() // 2,
                    rect.center().y() - icon_size.height() // 2,
                    icon_size.width(),
                    icon_size.height(),
                ),
                Qt.AlignmentFlag.AlignCenter,
                QIcon.Mode.Normal,
            )
        else:
            margin = 8
            icon_rect = QRect(
                rect.left() + margin,
                rect.center().y() - icon_size.height() // 2,
                icon_size.width(),
                icon_size.height(),
            )
            paint_icon.paint(painter, icon_rect, Qt.AlignmentFlag.AlignCenter, QIcon.Mode.Normal)
            text_rect = QRect(
                icon_rect.right() + margin,
                rect.top(),
                rect.right() - icon_rect.right() - margin,
                rect.height(),
            )
            fm = QFontMetrics(self.font())
            elided = fm.elidedText(text, Qt.TextElideMode.ElideRight, text_rect.width())
            painter.setPen(draw_color)
            painter.drawText(
                text_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                elided,
            )
        painter.restore()
