# -*- coding: utf-8 -*-
from __future__ import print_function

from .core.logging_utils import get_logger


_LOGGER = get_logger()

import sys

try:
    reload
except NameError:
    from importlib import reload


PACKAGE_NAME = "script_toolbox"


def _begin_standalone_window_transition():
    """Keep the standalone Qt loop alive while replacing its last window."""
    try:
        from .compat import HOST
        from .compat import QtCore
        from .compat import QtGui
    except Exception:
        return None

    if HOST.key != "standalone":
        return None

    application = QtGui.QApplication.instance()
    if application is None:
        return None

    setter = getattr(
        application,
        "setQuitOnLastWindowClosed",
        None
    )
    getter = getattr(
        application,
        "quitOnLastWindowClosed",
        None
    )
    previous = True

    if getter is not None:
        try:
            previous = bool(
                getter()
            )
        except Exception:
            pass

    if setter is not None:
        try:
            setter(
                False
            )
        except Exception:
            setter = None

    # Older standalone builds may already have queued a Quit event when the
    # last window closed. Removing it here lets an updated bootstrap recover
    # during the same self-update that installs this fix.
    try:
        remove_posted_events = getattr(
            QtCore.QCoreApplication,
            "removePostedEvents",
            None
        )
        quit_event = getattr(
            QtCore.QEvent,
            "Quit",
            None
        )
        if (
            remove_posted_events is not None and
            quit_event is not None
        ):
            remove_posted_events(
                application,
                quit_event
            )
    except Exception:
        pass

    return (
        application,
        setter,
        previous,
    )


def _end_standalone_window_transition(state):
    if state is None:
        return

    application, setter, previous = state
    if application is None or setter is None:
        return

    try:
        setter(
            previous
        )
    except Exception:
        pass


def show():
    transition = _begin_standalone_window_transition()
    try:
        try:
            from .telemetry import initialize_telemetry
            initialize_telemetry()
        except Exception:
            # Telemetry must never prevent Script Toolbox from opening.
            _LOGGER.debug(
                "Telemetry initialization failed; continuing without telemetry.",
                exc_info=True
            )

        from .ui.debounced_main_window import show as _show
        window = _show()

        try:
            from .ui.window_geometry import install_window_geometry_persistence
            install_window_geometry_persistence(
                window
            )
        except Exception:
            # Window placement recovery must never prevent the toolbox from opening.
            pass

        return window
    finally:
        _end_standalone_window_transition(
            transition
        )


def package_child_module_names(
    module_names=None
):
    """
    Return Script Toolbox child modules in deepest-first unload order.

    The root `script_toolbox` module is deliberately preserved so external
    references such as a variable created by `import script_toolbox` can be
    refreshed in place with reload().
    """
    if module_names is None:
        module_names = list(
            sys.modules.keys()
        )

    prefix = PACKAGE_NAME + "."

    names = [
        name
        for name in module_names
        if name.startswith(
            prefix
        )
    ]

    names.sort(
        key=lambda value: (
            value.count("."),
            len(value)
        ),
        reverse=True
    )

    return names


def purge_child_modules():
    names = package_child_module_names()

    for name in names:
        try:
            del sys.modules[
                name
            ]
        except KeyError:
            pass

    return names


def _close_telemetry():
    try:
        from .telemetry.service import close
        close()
    except Exception:
        _LOGGER.debug(
            "Telemetry shutdown failed during reload.",
            exc_info=True
        )


def _close_live_ui():
    try:
        from .compat import QtGui
    except Exception:
        QtGui = None

    # Persistence failures must abort reload instead of being swallowed. The
    # debounced window flushes pending runtime values before it closes.
    from .ui.debounced_main_window import close_toolbox
    close_toolbox()
    _close_telemetry()

    if QtGui is not None:
        try:
            from .constants import WINDOW_OBJECT_NAME

            application = QtGui.QApplication.instance()

            if application is not None:
                for widget in application.allWidgets():
                    try:
                        if widget.objectName() == WINDOW_OBJECT_NAME:
                            widget.close()
                            widget.deleteLater()
                    except Exception:
                        _LOGGER.warning(
                            "Failed to close a live Script Toolbox widget during reload.",
                            exc_info=True
                        )

                application.processEvents()
        except Exception:
            _LOGGER.warning(
                "Failed to complete live UI cleanup during reload.",
                exc_info=True
            )


def hot_reload_toolbox():
    """
    Reload an installed update without restarting the active DCC host.

    This is intentionally different from the development reload below:
    installed files may have been replaced with a different version, so all
    child modules must be discarded and imported from disk again.

    The package root object is reloaded in place. That keeps existing external
    references to `script_toolbox` useful and refreshes `__version__`.
    """
    transition = _begin_standalone_window_transition()
    try:
        _close_live_ui()

        root_module = sys.modules.get(
            PACKAGE_NAME
        )

        if root_module is None:
            root_module = __import__(
                PACKAGE_NAME
            )

        purge_child_modules()

        root_module = reload(
            root_module
        )

        window = root_module.show()

        try:
            window.statusBar().showMessage(
                "Updated to Script Toolbox {0}.".format(
                    root_module.__version__
                ),
                7000
            )
        except Exception:
            pass

        return window
    finally:
        _end_standalone_window_transition(
            transition
        )


def reload_toolbox():
    """Use the same close, purge and fresh import lifecycle as update reload."""
    return hot_reload_toolbox()


__all__ = [
    "hot_reload_toolbox",
    "package_child_module_names",
    "purge_child_modules",
    "reload_toolbox",
    "show",
]
