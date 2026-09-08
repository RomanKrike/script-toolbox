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
hou = None
shiboken = None
omui = None


def _mirror_qtwidgets_onto_qtgui(
    qt_gui,
    qt_widgets
):
    for name in dir(
        qt_widgets
    ):
        if hasattr(
            qt_gui,
            name
        ):
            continue

        try:
            setattr(
                qt_gui,
                name,
                getattr(
                    qt_widgets,
                    name
                )
            )
        except Exception:
            pass

    return qt_gui


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
    QtGui = _mirror_qtwidgets_onto_qtgui(
        _QtGui,
        QtWidgets
    )

    try:
        import shiboken2 as shiboken
    except ImportError:
        shiboken = None

elif HOST_KEY == "houdini":
    import hou

    from PySide2 import QtCore
    from PySide2 import QtGui as _QtGui
    from PySide2 import QtWidgets

    # Houdini 19 uses PySide2/Qt5. Preserve the legacy QtGui widget namespace
    # expected by the original Maya UI so all hosts can share one widget tree.
    QtGui = _mirror_qtwidgets_onto_qtgui(
        _QtGui,
        QtWidgets
    )

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

        QtGui = _mirror_qtwidgets_onto_qtgui(
            _QtGui,
            QtWidgets
        )

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


def _houdini_main_window():
    if (
        HOST_KEY != "houdini" or
        hou is None
    ):
        return None

    try:
        qt_api = getattr(
            hou,
            "qt",
            None
        )

        if qt_api is not None:
            main_window_getter = getattr(
                qt_api,
                "mainWindow",
                None
            )

            if callable(
                main_window_getter
            ):
                window = main_window_getter()

                if window is not None:
                    return window
    except Exception:
        pass

    # Compatibility fallback for older Houdini builds where the Qt main
    # window helper lives on hou.ui.
    try:
        ui_api = getattr(
            hou,
            "ui",
            None
        )
        main_window_getter = getattr(
            ui_api,
            "mainQtWindow",
            None
        )

        if callable(
            main_window_getter
        ):
            return main_window_getter()
    except Exception:
        pass

    return None


def main_window():
    if HOST_KEY == "maya":
        return _maya_main_window()

    if HOST_KEY == "nuke":
        return _nuke_main_window()

    if HOST_KEY == "houdini":
        return _houdini_main_window()

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
    "hou",
    "QtCore",
    "QtGui",
    "StringIO",
    "text_type",
    "integer_type",
    "main_window",
    "maya_main_window",
    "shift_pressed",
]
