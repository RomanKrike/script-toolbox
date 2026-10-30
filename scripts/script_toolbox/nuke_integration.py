# -*- coding: utf-8 -*-
from __future__ import print_function

from .compat import HOST
from .compat import nuke
from .compat import nukescripts
from .integrations.config import get_integration_settings
from .integrations.discovery import parse_version
from .integrations.icons import integration_icon_path



_ACTIVE_PROFILE_ID = None
PANEL_ID = "com.romankrike.scripttoolbox"
_PANEL_MARKER = "_script_toolbox_dock_panel_registered"


def active_profile_id():
    return _ACTIVE_PROFILE_ID


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
    icon_path = integration_icon_path()

    root = nuke.menu(
        "Nuke"
    )

    menu = root.findItem(
        "Script Toolbox"
    )

    if menu is None:
        menu = root.addMenu(
            "Script Toolbox",
            icon=icon_path
        )
    else:
        menu.setIcon(icon_path)

    open_item = menu.findItem(
        "Open"
    )
    if open_item is None:
        menu.addCommand(
            "Open",
            "import script_toolbox; script_toolbox.show()",
            icon=icon_path
        )
    else:
        open_item.setIcon(icon_path)

    if menu.findItem("Open Pane Tab") is None:
        menu.addCommand(
            "Open Pane Tab",
            "import script_toolbox; script_toolbox.open_pane_tab()",
            icon=icon_path
        )

    if nukescripts is not None:
        register_panel()
    return menu


def register_panel():
    """Register a QWidget container in Nuke's native Pane menu once."""
    _require_nuke()
    if nukescripts is None or getattr(nukescripts, "panels", None) is None:
        raise RuntimeError("nukescripts.panels is unavailable.")
    if getattr(nuke, _PANEL_MARKER, False):
        return True
    nukescripts.panels.registerWidgetAsPanel(
        "script_toolbox.ui.panel_container.ScriptToolboxPanel",
        "Script Toolbox",
        PANEL_ID
    )
    setattr(nuke, _PANEL_MARKER, True)
    return True


def unregister_panel():
    """Remove our Pane entry when this profile is uninstalled live."""
    _require_nuke()
    if not getattr(nuke, _PANEL_MARKER, False):
        return False
    pane_menu = nuke.menu("Pane")
    remove_item = getattr(pane_menu, "removeItem", None)
    if callable(remove_item) and pane_menu.findItem("Script Toolbox") is not None:
        remove_item("Script Toolbox")
    nukescripts.panels.unregisterPanel(PANEL_ID, None)
    setattr(nuke, _PANEL_MARKER, False)
    return True


def open_pane_tab():
    """Open the registered native panel, moving a floating runtime first."""
    register_panel()
    from .ui.debounced_main_window import active_toolbox
    toolbox = active_toolbox()
    if toolbox is not None:
        if getattr(toolbox, "_script_toolbox_mode", "window") == "panel":
            toolbox.raise_()
            toolbox.activateWindow()
            return toolbox
    return nukescripts.panels.restorePanel(PANEL_ID)


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


def _current_settings(profile_id=None):
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
        version,
        profile_id=profile_id
    )


def apply_current_integration(profile_id=None, activate_profile=False):
    global _ACTIVE_PROFILE_ID
    if activate_profile or _ACTIVE_PROFILE_ID is None:
        _ACTIVE_PROFILE_ID = profile_id or "default"
    elif profile_id is not None and profile_id != _ACTIVE_PROFILE_ID:
        return False
    settings = _current_settings(
        profile_id=profile_id
    )
    if not settings:
        try:
            remove_menu()
            unregister_panel()
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

    register_panel()

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



__all__ = [
    "PANEL_ID",
    "apply_current_integration",
    "open_pane_tab",
    "register_menu",
    "register_panel",
    "remove_menu",
    "unregister_panel",
]
