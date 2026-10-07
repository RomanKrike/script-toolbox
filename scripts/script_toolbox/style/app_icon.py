# -*- coding: utf-8 -*-
from __future__ import print_function

import os

from ..compat import QtGui


_ICON_PATH = os.path.normpath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "resources",
        "logo_sbt.ico"
    )
)
_ICON_CACHE = None


def application_icon_path():
    return _ICON_PATH


def application_icon():
    global _ICON_CACHE

    if _ICON_CACHE is None:
        _ICON_CACHE = QtGui.QIcon(
            _ICON_PATH
        )

    return _ICON_CACHE


def apply_window_icon(widget):
    icon = application_icon()

    if (
        widget is not None and
        not icon.isNull()
    ):
        widget.setWindowIcon(
            icon
        )

    return icon


__all__ = [
    "application_icon",
    "application_icon_path",
    "apply_window_icon",
]
