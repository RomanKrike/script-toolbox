# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtGui


_FRAME_STYLE = """
QFrame#EditorScrollFrame {
    background-color: #242424;
    border: 1px solid #161616;
    border-radius: 2px;
}
"""

_TREE_STYLE = """
QTreeWidget {
    border: 0px;
    border-radius: 0px;
}
"""


def _wrap_scroll_widget(widget):
    """Put a scrollable tree inside an external 1px frame.

    Qt paints QAbstractScrollArea scroll bars inside the widget frame rect.
    On Maya/Qt4 that can visually cover the tree's own border. Moving the
    border to a parent frame keeps it outside the scroll-bar geometry.
    """
    if widget is None:
        return None

    parent = widget.parentWidget()
    if parent is None:
        return None

    layout = parent.layout()
    if layout is None:
        return None

    index = layout.indexOf(widget)
    if index < 0:
        return None

    frame = QtGui.QFrame(parent)
    frame.setObjectName("EditorScrollFrame")
    frame.setStyleSheet(_FRAME_STYLE)

    frame_layout = QtGui.QVBoxLayout(frame)
    frame_layout.setContentsMargins(1, 1, 1, 1)
    frame_layout.setSpacing(0)

    layout.takeAt(index)

    try:
        widget.setFrameShape(QtGui.QFrame.NoFrame)
    except Exception:
        pass
    widget.setStyleSheet(_TREE_STYLE)
    frame_layout.addWidget(widget)

    # Both editor trees are the expanding item in their pane. Preserve that
    # behavior after replacing the direct tree widget with the outer frame.
    layout.insertWidget(index, frame, 1)
    return frame


def build_scroll_frame_interface_editor_class(base_class):
    class ScrollFrameInterfaceEditor(base_class):

        def __init__(self, toolbox, parent=None):
            base_class.__init__(self, toolbox, parent)
            self.palette_scroll_frame = _wrap_scroll_widget(
                getattr(self, "palette", None)
            )
            self.tree_scroll_frame = _wrap_scroll_widget(
                getattr(self, "tree", None)
            )

    ScrollFrameInterfaceEditor.__name__ = base_class.__name__
    return ScrollFrameInterfaceEditor


__all__ = ["build_scroll_frame_interface_editor_class"]
