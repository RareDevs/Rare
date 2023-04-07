from typing import Callable

from PyQt5.QtCore import (
    Qt,
    QRect,
    QPoint,
)
from PyQt5.QtWidgets import (
    QSizePolicy,
)

from .flow_layout import FlowLayout


class LibraryLayout(FlowLayout):
    def __init__(self, parent=None, margin=6, spacing=11):
        super(LibraryLayout, self).__init__(parent=parent, margin=margin, hspacing=spacing, vspacing=spacing)

    def expandingDirections(self) -> Qt.Orientations:
        return Qt.Horizontal | Qt.Vertical

    def setGeometry(self, a0: QRect) -> None:
        super(FlowLayout, self).setGeometry(a0)
        self.doLayout(a0, False)

    def doLayout(self, rect, testonly):
        """!
        @brief Arranges the widgets for this layout

        <pre>
        Layout
        +-----------------------------------------------+
        | margin (above first row only)                 |
        |-----------------------------------------------|
        | vspace (hspace)                               |
        |-----------------------------------------------|
        | hpadding                                      |
        |-----------------------------------------------|
        | _  _  __ +--------+ _  __ +--------+ _  __  _ |
        ||m||h|| h|| Widget ||h|| h|| Widget ||h|| h||m||
        ||a||s|| p||        ||s|| p||        ||s|| p||a||
        ||r||p|| a||        ||p|| a||        ||p|| a||r||
        ||g||a|| d||        ||a|| d||        ||a|| d||g||
        ||i||c|| d||        ||c|| d||        ||c|| d||i||
        ||n||e|| i||        ||e|| i||        ||e|| i||n||
        || || || n||        || || n||        || || n|| ||
        || || || g||        || || g||        || || g|| ||
        | -  -  -- +--------+ -  -- +--------+ -  --  - |
        |-----------------------------------------------|
        | vspace (hspace)                               |
        |-----------------------------------------------|
        | hpadding                                      |
        |-----------------------------------------------|
        | margin (below last row only)                  |
        +-----------------------------------------------+

        margin:   doesn't play a role in the code below, it only affects the
                  effective rectangle inside which we can layout
        hspace:   static padding between widgets (minimum distance between them)
        hpadding: dynamic padding to fill the space when resizing
        </pre>

        @param self: object self-reference
        @param rect: the area the widgets should occupy
        @param testonly: only test the layout, don't arrange the items

        @return: the height of the layout
        """

        left, top, right, bottom = self.getContentsMargins()
        effective = rect.adjusted(+left, +top, -right, -bottom)
        x = effective.x()
        y = effective.y()
        lineheight = 0

        if not self._items:
            return y + lineheight - rect.y() + bottom

        widget = self._items[0].widget()
        hspace = self.horizontalSpacing()
        if hspace == -1:
            hspace = widget.style().layoutSpacing(
                QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal
            )
        vspace = self.verticalSpacing()
        if vspace == -1:
            vspace = widget.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Vertical)

        # lk: get the remaining space after subtracting the space required for each widget and its static padding
        # lk: also reserve space for the leading static padding
        rem_hspace = (effective.width() - hspace) % (widget.size().width() + hspace)
        # lk: the number of items and their static spacing that can be in the layout
        hspace_items = (effective.width() - hspace) // (widget.size().width() + hspace)

        # lk: in case the visible items are less than the maximum possible widgets
        visible_items = len([item for item in self._items if not item.isEmpty()])
        if visible_items < hspace_items:
            hspace_items = visible_items
            rem_hspace = (effective.width() - hspace) - ((widget.size().width() + hspace) * hspace_items)

        try:
            # lk: the dynamic padding between each item, also account for the leading dynamic padding
            hpadding = rem_hspace // (hspace_items + 1)
        except ZeroDivisionError:
            hpadding = 0

        for item in self._items:
            if item.isEmpty():
                continue
            # lk: compute the location of the next widget
            next_x = x + item.sizeHint().width() + hspace + hpadding
            # lk: find out if there is enough space for the widget in this row
            # lk: account for the leading static and dynamic padding too (at the start)
            if next_x - hspace * 2 - hpadding * 2 > effective.right() and lineheight > 0:
                x = effective.x()
                # lk: find next vertical position, add static and dynamic padding
                y = y + lineheight + vspace + hpadding
                next_x = x + item.sizeHint().width() + hspace + hpadding
                lineheight = 0
            # lk: add static and dynamic padding to the current widget
            x = x + hspace + hpadding
            if not testonly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            x = next_x
            lineheight = max(lineheight, item.sizeHint().height())
        return y + lineheight - rect.y() + bottom

    def sort(self, key: Callable, reverse=False) -> None:
        self._items.sort(key=key, reverse=reverse)
        self.setGeometry(self.parent().contentsRect())
