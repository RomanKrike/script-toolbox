# -*- coding: utf-8 -*-
from __future__ import print_function

import maya.cmds as cmds
import maya.mel as mel

from PySide import QtCore
from PySide import QtGui

try:
    import shiboken
except ImportError:
    shiboken = None

try:
    from maya import OpenMayaUI as omui
except ImportError:
    omui = None

try:
    text_type = unicode
except NameError:
    text_type = str

try:
    integer_type = long
except NameError:
    integer_type = int

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


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
