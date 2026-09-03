# -*- coding: utf-8 -*-
from __future__ import print_function

from .compat import HOST
from .compat import nuke
from .compat import nukescripts


PANEL_ID = "com.romankrike.scripttoolbox"


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


def register_panel():
    """
    Register Script Toolbox as a Nuke dockable pane.

    Nuke may decide when the pane instance is created. The normal
    script_toolbox.show() entry point remains available as a floating window.
    """
    _require_nuke()

    if nukescripts is None:
        raise RuntimeError(
            "nukescripts.panels is unavailable."
        )

    return nukescripts.panels.registerWidgetAsPanel(
        "script_toolbox.ui.main_window.ScriptToolbox",
        "Script Toolbox",
        PANEL_ID
    )


__all__ = [
    "PANEL_ID",
    "register_menu",
    "register_panel",
]
