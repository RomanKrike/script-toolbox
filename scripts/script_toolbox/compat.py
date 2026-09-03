# -*- coding: utf-8 -*-
from __future__ import print_function

from .hosts import HOST
from .pycompat import StringIO
from .pycompat import integer_type
from .pycompat import text_type


HOST_KEY = HOST.key
HOST_DISPLAY_NAME = HOST.display_name


cmds = None
mel = None
nuke = None
nukescripts = None
shiboken = None
omui = None


if HOST_KEY == "maya":
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

elif HOST_KEY == "nuke":
    import nuke

    try:
        import nukescripts
    except ImportError:
        nukescripts = None

    from PySide2 import QtCore
    from PySide2 import QtGui as _QtGui
    from PySide2 import QtWidgets

    # The Maya 2015 codebase uses the Qt4/PySide1 layout where widgets live
    # under QtGui. Mirror QtWidgets onto QtGui so the same UI code works in
    # Nuke 12 / PySide2 without maintaining a second widget tree.
    for _name in dir(
        QtWidgets
    ):
        if not hasattr(
            _QtGui,
            _name
        ):
            try:
                setattr(
                    _QtGui,
                    _name,
                    getattr(
                        QtWidgets,
                        _name
                    )
                )
            except Exception:
                pass

    QtGui = _QtGui

    try:
        import shiboken2 as shiboken
    except ImportError:
        shiboken = None

else:
    # Standalone imports are useful for development tooling. Prefer PySide2
    # when available and fall back to PySide1.
    try:
        from PySide2 import QtCore
        from PySide2 import QtGui as _QtGui
        from PySide2 import QtWidgets

        for _name in dir(
            QtWidgets
        ):
            if not hasattr(
                _QtGui,
                _name
            ):
                try:
                    setattr(
                        _QtGui,
                        _name,
                        getattr(
                            QtWidgets,
                            _name
                        )
                    )
                except Exception:
                    pass

        QtGui = _QtGui

    except ImportError:
        from PySide import QtCore
        from PySide import QtGui


def _maya_main_window():
    if (
        HOST_KEY != "maya" or
        omui is None or
        shiboken is None
    ):
        return None

    try:
        pointer = omui.MQtUtil.mainWindow()

        if not pointer:
            return None

        return shiboken.wrapInstance(
            integer_type(
                pointer
            ),
            QtGui.QWidget
        )
    except Exception:
        return None


def _nuke_main_window():
    if HOST_KEY != "nuke":
        return None

    try:
        application = QtGui.QApplication.instance()

        if application is None:
            return None

        fallback = None

        for widget in application.topLevelWidgets():
            try:
                class_name = text_type(
                    widget.metaObject().className()
                )
            except Exception:
                class_name = ""

            if (
                "DockMainWindow" in class_name or
                "Foundry" in class_name
            ):
                return widget

            try:
                title = text_type(
                    widget.windowTitle()
                )
            except Exception:
                title = ""

            if (
                fallback is None and
                "Nuke" in title
            ):
                fallback = widget

        return fallback

    except Exception:
        return None


def main_window():
    if HOST_KEY == "maya":
        return _maya_main_window()

    if HOST_KEY == "nuke":
        return _nuke_main_window()

    return None


# Backward-compatible alias used by the first modular Maya-only releases.
def maya_main_window():
    return main_window()


def shift_pressed():
    native = HOST.shift_pressed_native()

    if native is not None:
        return bool(
            native
        )

    try:
        return bool(
            QtGui.QApplication.keyboardModifiers() &
            QtCore.Qt.ShiftModifier
        )
    except Exception:
        return False


__all__ = [
    "HOST",
    "HOST_DISPLAY_NAME",
    "HOST_KEY",
    "cmds",
    "mel",
    "nuke",
    "nukescripts",
    "QtCore",
    "QtGui",
    "StringIO",
    "text_type",
    "integer_type",
    "main_window",
    "maya_main_window",
    "shift_pressed",
]
