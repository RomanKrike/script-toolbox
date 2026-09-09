# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..compat import QtGui
from ..style import toolbar_icon


ICON_BUTTON_COMPACT = "compact"
ICON_BUTTON_TOOLBAR = "toolbar"
ICON_BUTTON_HEADER = "header"

_ICON_BUTTON_PRESETS = {
    ICON_BUTTON_COMPACT: (16, 25),
    ICON_BUTTON_TOOLBAR: (18, 26),
    ICON_BUTTON_HEADER: (18, 28),
}


def create_icon_button(
    icon_name,
    tooltip="",
    callback=None,
    parent=None,
    preset=ICON_BUTTON_COMPACT
):
    """Create a theme-compatible technical icon button.

    Presets preserve the existing Script Toolbox button geometry while
    centralizing object name, icon sizing, tooltip and signal wiring.
    """
    icon_size, button_size = _ICON_BUTTON_PRESETS.get(
        preset,
        _ICON_BUTTON_PRESETS[ICON_BUTTON_COMPACT]
    )

    button = QtGui.QToolButton(parent)
    button.setObjectName("IconButton")
    button.setIcon(
        toolbar_icon(icon_name)
    )
    button.setIconSize(
        QtCore.QSize(
            icon_size,
            icon_size
        )
    )
    button.setFixedSize(
        button_size,
        button_size
    )

    if tooltip:
        button.setToolTip(tooltip)

    if callback is not None:
        button.clicked.connect(callback)

    return button


__all__ = [
    "ICON_BUTTON_COMPACT",
    "ICON_BUTTON_HEADER",
    "ICON_BUTTON_TOOLBAR",
    "create_icon_button",
]
