# -*- coding: utf-8 -*-
from __future__ import print_function

import sys

try:
    reload
except NameError:
    from importlib import reload


PACKAGE_NAME = "script_toolbox"


def show():
    from .ui.main_window import show as _show
    return _show()


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


def _close_live_ui():
    try:
        from .compat import QtGui
    except Exception:
        QtGui = None

    try:
        from .ui.main_window import close_toolbox
        close_toolbox()
    except Exception:
        pass

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
                        pass

                application.processEvents()
        except Exception:
            pass


def hot_reload_toolbox():
    """
    Reload an installed update without restarting the active DCC host.

    This is intentionally different from the development reload below:
    installed files may have been replaced with a different version, so all
    child modules must be discarded and imported from disk again.

    The package root object is reloaded in place. That keeps existing external
    references to `script_toolbox` useful and refreshes `__version__`.
    """
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


def reload_toolbox():
    """
    Development reload for the active DCC host.

    Close the live window first, then reload child modules from deepest names
    to shallowest names so UI classes do not keep stale module references.
    """
    try:
        from .ui.main_window import close_toolbox
        close_toolbox()
    except Exception:
        pass

    prefix = "script_toolbox."

    names = [
        name
        for name in list(sys.modules.keys())
        if (
            name.startswith(prefix) and
            name != __name__
        )
    ]

    names.sort(
        key=lambda value: (
            value.count("."),
            len(value)
        ),
        reverse=True
    )

    for name in names:
        module = sys.modules.get(
            name
        )

        if module is None:
            continue

        try:
            reload(
                module
            )
        except Exception:
            pass

    return show()


__all__ = [
    "hot_reload_toolbox",
    "package_child_module_names",
    "purge_child_modules",
    "reload_toolbox",
    "show",
]
