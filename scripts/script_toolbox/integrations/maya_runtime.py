# -*- coding: utf-8 -*-
from __future__ import print_function

import os

from ..core.logging_utils import get_logger
from .config import find_profile_id_for_paths
from .config import get_integration_settings
from .discovery import parse_version


_LOGGER = get_logger()
_MENU_NAME = "ScriptToolboxMainMenu"
_SHELF_NAME = "ScriptToolbox"
_SHELF_BUTTON_NAME = "ScriptToolboxOpenButton"


def _cmds():
    import maya.cmds as cmds
    return cmds


def _current_version():
    try:
        return parse_version(
            _cmds().about(version=True)
        )
    except Exception:
        return ""


def _current_profile_id():
    candidates = []
    cmds = _cmds()

    try:
        candidates.append(cmds.internalVar(userAppDir=True))
    except Exception:
        pass

    try:
        user_pref = cmds.internalVar(userPrefDir=True)
        if user_pref:
            candidates.append(
                os.path.dirname(
                    os.path.normpath(
                        user_pref.rstrip("\\/")
                    )
                )
            )
    except Exception:
        pass

    return find_profile_id_for_paths(
        "maya",
        candidates
    )


def _current_settings():
    version = _current_version()
    if not version:
        return None
    return get_integration_settings(
        "maya",
        version,
        profile_id=_current_profile_id()
    )


def _open_toolbox(*unused):
    import script_toolbox
    return script_toolbox.show()


def _reload_toolbox(*unused):
    import script_toolbox
    return script_toolbox.reload_toolbox()


def _open_settings(*unused):
    try:
        import script_toolbox
        window = script_toolbox.show()
        callback = getattr(window, "open_settings_dialog", None)
        if callable(callback):
            return callback()
    except Exception:
        _LOGGER.exception("[DCC] Could not open Script Toolbox settings from Maya menu.")
    return None


def remove_main_menu():
    cmds = _cmds()
    try:
        if cmds.menu(_MENU_NAME, exists=True):
            cmds.deleteUI(_MENU_NAME, menu=True)
            return True
    except Exception:
        pass
    return False


def ensure_main_menu():
    cmds = _cmds()
    remove_main_menu()
    menu = cmds.menu(
        _MENU_NAME,
        label="ScriptToolbox",
        parent="MayaWindow",
        tearOff=True
    )
    cmds.menuItem(
        label="Open ScriptToolbox",
        parent=menu,
        command=_open_toolbox
    )
    cmds.menuItem(
        divider=True,
        parent=menu
    )
    cmds.menuItem(
        label="Reload Scripts",
        parent=menu,
        command=_reload_toolbox
    )
    cmds.menuItem(
        label="Settings",
        parent=menu,
        command=_open_settings
    )
    return menu


def _shelf_parent():
    try:
        import maya.mel as mel
        return mel.eval("$tmp=$gShelfTopLevel")
    except Exception:
        return "ShelfLayout"


def remove_shelf_button():
    cmds = _cmds()
    removed = False
    try:
        if cmds.shelfButton(_SHELF_BUTTON_NAME, exists=True):
            cmds.deleteUI(_SHELF_BUTTON_NAME)
            removed = True
    except Exception:
        pass
    return removed


def ensure_shelf_button():
    cmds = _cmds()
    parent = _shelf_parent()
    if not cmds.shelfLayout(_SHELF_NAME, exists=True):
        cmds.shelfLayout(
            _SHELF_NAME,
            parent=parent
        )
    remove_shelf_button()
    return cmds.shelfButton(
        _SHELF_BUTTON_NAME,
        parent=_SHELF_NAME,
        label="ScriptToolbox",
        annotation="Open Script Toolbox",
        image1="pythonFamily.png",
        command=_open_toolbox
    )


def apply_current_integration():
    settings = _current_settings()
    if not settings:
        remove_main_menu()
        remove_shelf_button()
        return False

    if settings.get("shelf", True):
        ensure_shelf_button()
    else:
        remove_shelf_button()

    if settings.get("main_menu", True):
        ensure_main_menu()
    else:
        remove_main_menu()

    if settings.get("auto_open", False):
        _open_toolbox()
    return True


def install_startup_ui():
    """Schedule Maya UI integration after Maya has finished building its UI."""
    try:
        import maya.utils as maya_utils
        maya_utils.executeDeferred(apply_current_integration)
        return True
    except Exception:
        pass

    try:
        _cmds().evalDeferred(
            "import script_toolbox.integrations.maya_runtime as _stb_maya_runtime; "
            "_stb_maya_runtime.apply_current_integration()"
        )
        return True
    except Exception:
        _LOGGER.exception("[DCC] Maya startup integration failed.")
        return False


__all__ = [
    "apply_current_integration",
    "ensure_main_menu",
    "ensure_shelf_button",
    "install_startup_ui",
    "remove_main_menu",
    "remove_shelf_button",
]
