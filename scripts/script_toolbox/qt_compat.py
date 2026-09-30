# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import os
import re
import sys


PYSIDE = "PySide"
PYSIDE2 = "PySide2"
PYSIDE6 = "PySide6"


class QtBinding(object):
    """Resolved Qt binding and compatibility metadata."""

    def __init__(
        self,
        name,
        qt_core,
        qt_gui,
        qt_widgets,
        shiboken
    ):
        self.name = name
        self.QtCore = qt_core
        self.QtGui = qt_gui
        self.QtWidgets = qt_widgets
        self.shiboken = shiboken

    @property
    def qt_major(self):
        if self.name == PYSIDE:
            return 4
        if self.name == PYSIDE2:
            return 5
        if self.name == PYSIDE6:
            return 6
        return 0


def version_major(value):
    """Return the leading integer from a DCC version string."""
    match = re.match(
        r"\s*(\d+)",
        str(value or "")
    )
    if match is None:
        return 0

    try:
        return int(
            match.group(1)
        )
    except Exception:
        return 0


def _normalized_binding_name(value):
    text = str(value or "").strip().lower()
    if text == "pyside6":
        return PYSIDE6
    if text == "pyside2":
        return PYSIDE2
    if text == "pyside":
        return PYSIDE
    return ""


def binding_candidates(
    host_key,
    app_version="",
    preferred_binding=""
):
    """Return safest binding order for the active DCC generation.

    The explicit preferred binding is primarily used by Houdini, whose
    ``HOUDINI_QT_PREFERRED_BINDING`` environment variable distinguishes
    Qt5/PySide2 from optional Qt6/PySide6 builds in the 20.5 generation.
    """
    preferred = _normalized_binding_name(
        preferred_binding
    )
    major = version_major(
        app_version
    )
    host_key = str(
        host_key or ""
    ).lower()

    if host_key == "maya":
        if 0 < major <= 2016:
            ordered = [
                PYSIDE,
                PYSIDE2,
                PYSIDE6,
            ]
        elif 2017 <= major <= 2024:
            ordered = [
                PYSIDE2,
                PYSIDE6,
                PYSIDE,
            ]
        elif major >= 2025:
            ordered = [
                PYSIDE6,
                PYSIDE2,
                PYSIDE,
            ]
        else:
            ordered = [
                PYSIDE6,
                PYSIDE2,
                PYSIDE,
            ]

    elif host_key == "nuke":
        if 0 < major < 16:
            ordered = [
                PYSIDE2,
                PYSIDE6,
                PYSIDE,
            ]
        else:
            ordered = [
                PYSIDE6,
                PYSIDE2,
                PYSIDE,
            ]

    elif host_key == "houdini":
        if 0 < major < 21:
            ordered = [
                PYSIDE2,
                PYSIDE6,
                PYSIDE,
            ]
        else:
            ordered = [
                PYSIDE6,
                PYSIDE2,
                PYSIDE,
            ]

    else:
        ordered = [
            PYSIDE6,
            PYSIDE2,
            PYSIDE,
        ]

    if preferred:
        ordered = [
            preferred
        ] + [
            name
            for name in ordered
            if name != preferred
        ]

    # Houdini supports optional Qt generations; standalone can reuse a loaded
    # binding. Known Maya/Nuke versions must keep their required generation
    # even when another plugin has imported a different PySide package.
    loaded = []
    for name in (
        PYSIDE6,
        PYSIDE2,
        PYSIDE,
    ):
        if (
            name in sys.modules or
            (name + ".QtCore") in sys.modules
        ):
            loaded.append(
                name
            )

    if loaded and (host_key not in ("maya", "nuke") or not major):
        ordered = loaded + [
            name
            for name in ordered
            if name not in loaded
        ]

    if host_key in ("maya", "nuke", "houdini") and (major or preferred or loaded):
        return (ordered[0],)
    return tuple(ordered)


def _import_module(name):
    return __import__(
        name,
        globals(),
        locals(),
        ["*"],
        0
    )


def _optional_import(name):
    try:
        return _import_module(
            name
        )
    except ImportError:
        return None


class QtNamespace(object):
    """Private facade; never add attributes to shared PySide modules/classes."""
    def __init__(self, module):
        self._module = module

    def __getattr__(self, name):
        return getattr(self._module, name)


def mirror_widgets_onto_qtgui(qt_gui, qt_widgets):
    facade = QtNamespace(qt_gui)
    if qt_widgets is not None:
        for name in dir(qt_widgets):
            if not hasattr(qt_gui, name):
                setattr(facade, name, getattr(qt_widgets, name))
    return facade


def qt_exec(instance, *args, **kwargs):
    """Run a modal/event loop across Qt4, Qt5 and Qt6 without class patches."""
    callback = getattr(instance, "exec_", None) or getattr(instance, "exec")
    return callback(*args, **kwargs)


def _install_qregexp_compat(qt_core):
    """Restore the QRegExp subset used by the code highlighter on Qt6."""
    if hasattr(
        qt_core,
        "QRegExp"
    ):
        return

    regular_expression = getattr(
        qt_core,
        "QRegularExpression",
        None
    )
    if regular_expression is None:
        return

    class QRegExpCompat(object):

        def __init__(
            self,
            pattern=""
        ):
            self._expression = regular_expression(
                pattern
            )
            self._last_match = None

        def indexIn(
            self,
            text,
            offset=0
        ):
            self._last_match = None

            try:
                iterator = self._expression.globalMatch(
                    text,
                    int(offset)
                )
                if not iterator.hasNext():
                    return -1
                match = iterator.next()
            except Exception:
                return -1

            if not match.hasMatch():
                return -1

            self._last_match = match
            return int(
                match.capturedStart()
            )

        def matchedLength(self):
            if self._last_match is None:
                return -1

            try:
                return int(
                    self._last_match.capturedLength()
                )
            except Exception:
                return -1

    qt_core.QRegExp = QRegExpCompat


def install_legacy_api(qt_core, qt_gui, qt_widgets=None):
    core_facade = QtNamespace(qt_core)
    gui_facade = mirror_widgets_onto_qtgui(qt_gui, qt_widgets)
    _install_qregexp_compat(core_facade)
    return core_facade, gui_facade


def load_qt_binding(
    host_key="",
    app_version="",
    preferred_binding=""
):
    """Load the host-compatible PySide generation with safe fallbacks."""
    failures = []

    for name in binding_candidates(
        host_key,
        app_version,
        preferred_binding
    ):
        try:
            qt_core = _import_module(
                name + ".QtCore"
            )
            qt_gui = _import_module(
                name + ".QtGui"
            )

            if name == PYSIDE:
                qt_widgets = None
                shiboken = _optional_import(
                    "shiboken"
                )
            elif name == PYSIDE2:
                qt_widgets = _import_module(
                    name + ".QtWidgets"
                )
                shiboken = _optional_import(
                    "shiboken2"
                )
            else:
                qt_widgets = _import_module(
                    name + ".QtWidgets"
                )
                shiboken = _optional_import(
                    "shiboken6"
                )

            qt_core, qt_gui = install_legacy_api(
                qt_core,
                qt_gui,
                qt_widgets
            )

            return QtBinding(
                name,
                qt_core,
                qt_gui,
                qt_widgets,
                shiboken
            )

        except ImportError as exc:
            failures.append(
                "{0}: {1}".format(
                    name,
                    exc
                )
            )

    raise ImportError(
        "Could not load a supported PySide binding for {0} {1}. "
        "Tried: {2}. Failures: {3}".format(
            host_key or "standalone",
            app_version or "",
            ", ".join(
                binding_candidates(
                    host_key,
                    app_version,
                    preferred_binding
                )
            ),
            "; ".join(
                failures
            )
        )
    )


def houdini_preferred_binding():
    return os.environ.get(
        "HOUDINI_QT_PREFERRED_BINDING",
        ""
    )


__all__ = [
    "PYSIDE",
    "PYSIDE2",
    "PYSIDE6",
    "QtBinding",
    "binding_candidates",
    "houdini_preferred_binding",
    "install_legacy_api",
    "load_qt_binding",
    "mirror_widgets_onto_qtgui",
    "version_major",
]
