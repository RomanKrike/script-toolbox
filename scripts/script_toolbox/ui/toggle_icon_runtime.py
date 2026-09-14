# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..compat import QtGui


def render_toggle_icon(owner, item, compact=False):
    props = item.get("props", {}) or {}
    ui = item.get("ui", {}) or {}
    width = int(props.get("width", 24))
    height = int(props.get("height", 24))

    icon_widget = QtGui.QLabel()
    icon_widget.setFixedSize(width, height)
    icon_widget.setAlignment(QtCore.Qt.AlignCenter)
    icon_widget.setToolTip(ui.get("tooltip", ""))

    owner.toolbox.register_toggle_icon(item.get("id"), icon_widget)
    owner.toolbox.refresh_toggle_icon(item.get("id"))

    container = QtGui.QWidget()
    container.setToolTip(ui.get("tooltip", ""))
    layout = QtGui.QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    alignment = props.get("content_alignment", "left")
    if alignment in ("center", "right"):
        layout.addStretch(1)
    layout.addWidget(icon_widget, 0, QtCore.Qt.AlignVCenter)
    if alignment == "center":
        layout.addStretch(1)

    return container


__all__ = [
    "render_toggle_icon",
]
