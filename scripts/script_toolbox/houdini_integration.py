# -*- coding: utf-8 -*-
from __future__ import print_function

from .integrations.config import get_integration_settings
from .integrations.discovery import parse_version


_SHELF_NAME = "script_toolbox"


def _hou():
    import hou
    return hou


def _current_settings(profile_id=None):
    hou = _hou()
    try:
        version = parse_version(
            hou.applicationVersionString()
        )
    except Exception:
        version = ""

    if not version:
        return None

    return get_integration_settings(
        "houdini",
        version,
        profile_id=profile_id
    )


def _shelf_object():
    hou = _hou()
    try:
        return hou.shelves.shelves().get(
            _SHELF_NAME
        )
    except Exception:
        return None


def ensure_shelf():
    hou = _hou()
    try:
        hou.shelves.reloadShelfFiles()
    except Exception:
        pass

    shelf = _shelf_object()
    if shelf is None:
        return False

    try:
        hou.hscript(
            "shelfdock add {0}".format(
                _SHELF_NAME
            )
        )
        return True
    except Exception:
        return False


def remove_shelf():
    hou = _hou()
    try:
        hou.hscript(
            "shelfdock remove {0}".format(
                _SHELF_NAME
            )
        )
        return True
    except Exception:
        return False


def apply_current_integration(profile_id=None):
    settings = _current_settings(
        profile_id=profile_id
    )
    if not settings:
        try:
            remove_shelf()
        except Exception:
            pass
        return False

    if settings.get(
        "shelf",
        True
    ):
        try:
            ensure_shelf()
        except Exception:
            pass
    else:
        try:
            remove_shelf()
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
    "ensure_shelf",
    "remove_shelf",
]
