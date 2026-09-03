# -*- coding: utf-8 -*-
from __future__ import print_function

import maya.cmds as cmds
import maya.mel as mel

from PySide import QtCore
from PySide import QtGui

from .pycompat import StringIO
from .pycompat import integer_type
from .pycompat import text_type

try:
    import shiboken
except ImportError:
    shiboken = None

try:
    from maya import OpenMayaUI as omui
except ImportError:
    omui = None


def maya_main_window():
    if omui is None or shiboken is None:
        return None

    try:
        pointer = omui.MQtUtil.mainWindow()

        if not pointer:
            return None

        return shiboken.wrapInstance(
            integer_type(pointer),
            QtGui.QWidget
        )
    except Exception:
        return None


def shift_pressed():
    try:
        return bool(cmds.getModifiers() & 1)
    except Exception:
        return False


__all__ = [
    "cmds",
    "mel",
    "QtCore",
    "QtGui",
    "StringIO",
    "text_type",
    "integer_type",
    "maya_main_window",
    "shift_pressed",
]
