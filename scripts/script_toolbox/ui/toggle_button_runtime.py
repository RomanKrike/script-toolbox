# -*- coding: utf-8 -*-
from __future__ import print_function

import os

from ..compat import QtCore
from ..compat import QtGui
from ..pycompat import text_type


def render_toggle_button(owner, item, compact=False):
    button = owner._button_widget(item)
    icon_path = os.path.expanduser(
        os.path.expandvars(text_type(item.get("icon_path") or ""))
    )
    icon_size = int(item.get("icon_size", 18))

    if icon_path:
        button.setIcon(QtGui.QIcon(icon_path))
        button.setIconSize(QtCore.QSize(icon_size, icon_size))

    owner.toolbox.register_state_button(item.get("id"), button)
    owner.toolbox.refresh_state_button(item.get("id"))
    return button


__all__ = [
    "render_toggle_button",
]
