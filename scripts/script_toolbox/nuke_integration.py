# -*- coding: utf-8 -*-
from __future__ import print_function

from .compat import HOST
from .compat import nuke
from .integrations.config import get_integration_settings
from .integrations.discovery import parse_version



_ACTIVE_PROFILE_ID = None


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
    "apply_current_integration",
    "register_menu",
    "remove_menu",
]
