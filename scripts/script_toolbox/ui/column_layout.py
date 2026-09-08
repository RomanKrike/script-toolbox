# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..compat import QtGui


def render_column(owner, item, compact=False):
    """Render a vertical layout container using the active runtime registry."""
    widget = QtGui.QWidget()
    widget.setObjectName("RuntimeColumn")

    try:
        widget.setToolTip(
            owner._tooltip(item)
        )
    except Exception:
        widget.setToolTip(
            item.get("tooltip", "")
        )

    layout = QtGui.QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(
        int(item.get("spacing", 4))
    )

    alignment = item.get(
        "horizontal_alignment",
        "stretch"
    )

    for child in item.get("items", []) or []:
        child_widget = owner.build_runtime_widget(
            child,
            compact=compact
        )
        if child_widget is None:
            continue

        if alignment == "stretch":
            child_widget.setSizePolicy(
                QtGui.QSizePolicy.Expanding,
                QtGui.QSizePolicy.Preferred
            )
            layout.addWidget(child_widget)
            continue

        flag = (
            QtCore.Qt.AlignRight
            if alignment == "right"
            else QtCore.Qt.AlignHCenter
            if alignment == "center"
            else QtCore.Qt.AlignLeft
        )
        layout.addWidget(
            child_widget,
            0,
            flag
        )

    # Keep the stack pinned to the top when sibling columns in a Row have
    # different heights.
    layout.addStretch(1)

    return widget


__all__ = [
    "render_column",
]
