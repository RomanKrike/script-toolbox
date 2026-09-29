# -*- coding: utf-8 -*-
from __future__ import print_function

from .compat import HOST
from .compat import nuke
from .compat import nukescripts
from .integrations.config import get_integration_settings
from .integrations.discovery import parse_version


PANEL_ID = "com.romankrike.scripttoolbox"
_PANEL_REGISTERED = False


def _require_nuke():
    if HOST.key != "nuke" or nuke is None:
        raise RuntimeError(
            "Nuke integration is only available inside Nuke."
        )


def register_menu():
    """
    Register Script Toolbox in Nuke's main application menu.

    This function is safe to call repeatedly from ~/.nuke/menu.py.
    """
    _require_nuke()

    root = nuke.menu(
        "Nuke"
    )

    menu = root.findItem(
        "Script Toolbox"
    )

    if menu is None:
        menu = root.addMenu(
            "Script Toolbox"
        )

    if menu.findItem(
        "Open"
    ) is None:
        menu.addCommand(
            "Open",
            "import script_toolbox; script_toolbox.show()"
        )

    if (
        nukescripts is not None and
        menu.findItem(
            "Register Dock Panel"
        ) is None
    ):
        menu.addCommand(
            "Register Dock Panel",
            (
                "import script_toolbox; "
                "script_toolbox.register_nuke_panel()"
            )
        )

    return menu


def remove_menu():
    _require_nuke()

    root = nuke.menu(
        "Nuke"
    )
    menu = root.findItem(
        "Script Toolbox"
    )
    if menu is None:
        return False

    remove_item = getattr(
        root,
        "removeItem",
        None
    )
    if callable(remove_item):
        try:
            remove_item(
                "Script Toolbox"
            )
            return True
        except Exception:
            pass
    return False


def _current_settings():
    try:
        version = parse_version(
            getattr(
                nuke,
                "NUKE_VERSION_STRING",
                ""
            )
        )
    except Exception:
        version = ""

    if not version:
        return None

    return get_integration_settings(
        "nuke",
        version
    )


def apply_current_integration():
    settings = _current_settings()
    if not settings:
        try:
            remove_menu()
        except Exception:
            pass
        return False

    if settings.get(
        "main_menu",
        True
    ):
        register_menu()
    else:
        try:
            remove_menu()
        except Exception:
            pass

    if settings.get(
        "dock_panel",
        True
    ):
        try:
            register_panel()
        except Exception:
            pass

    if settings.get(
        "auto_open",
        False
    ):
        try:
            import script_toolbox
            script_toolbox.show()
        except Exception:
            pass

    return True


def register_panel():
    """
    Register Script Toolbox as a Nuke dockable pane.

    Nuke may decide when the pane instance is created. The normal
    script_toolbox.show() entry point remains available as a floating window.
    """
    global _PANEL_REGISTERED
    _require_nuke()

    if nukescripts is None:
        raise RuntimeError(
            "nukescripts.panels is unavailable."
        )

    if _PANEL_REGISTERED:
        return True

    result = nukescripts.panels.registerWidgetAsPanel(
        "script_toolbox.ui.debounced_main_window.ScriptToolbox",
        "Script Toolbox",
        PANEL_ID
    )
    _PANEL_REGISTERED = True
    return result


__all__ = [
    "PANEL_ID",
    "apply_current_integration",
    "register_menu",
    "register_panel",
    "remove_menu",
]
