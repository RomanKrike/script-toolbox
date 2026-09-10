# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..compat import QtGui
from ..pycompat import text_type
from ..style.palette import TEXT_SUBTLE


def render_text(owner, item, compact=False):
    """Render static multiline explanatory text without a frame or surface."""
    label = QtGui.QLabel(
        text_type(item.get("text", ""))
    )
    label.setObjectName("RuntimeText")
    label.setWordWrap(True)
    label.setTextFormat(QtCore.Qt.PlainText)
    label.setAlignment(
        QtCore.Qt.AlignLeft |
        QtCore.Qt.AlignTop
    )
    label.setSizePolicy(
        QtGui.QSizePolicy.Expanding,
        QtGui.QSizePolicy.Minimum
    )
    label.setToolTip(
        owner._tooltip(item)
    )
    label.setStyleSheet(
        "color:{0};".format(TEXT_SUBTLE)
    )
    return label


__all__ = [
    "render_text",
]
