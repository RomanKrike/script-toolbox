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
_MONOCHROME_ICON_PATH = os.path.join(
    os.path.dirname(_ICON_PATH),
    "logo_sbt_monochrome.ico"
)
_ICON_CACHE = {}


def application_icon_path(monochrome=False):
    return _MONOCHROME_ICON_PATH if monochrome else _ICON_PATH


def application_icon(monochrome=False):
    path = application_icon_path(monochrome)

    if path not in _ICON_CACHE:
        _ICON_CACHE[path] = QtGui.QIcon(
            path
        )

    return _ICON_CACHE[path]


def apply_window_icon(widget, monochrome=False):
    icon = application_icon(monochrome)

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
