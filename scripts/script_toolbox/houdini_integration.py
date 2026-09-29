# -*- coding: utf-8 -*-
from __future__ import print_function

from .integrations.config import get_integration_settings
from .integrations.discovery import parse_version


_SHELF_NAME = "script_toolbox"


def _hou():
    import hou
    return hou


def _current_settings():
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
        version
    )


def _shelf_object():
    hou = _hou()
    try:
        return hou.shelves.shelves().get(
            _SHELF_NAME
        )
    except Exception:
        return None


def _writable_shelf_sets():
    hou = _hou()
    try:
        values = list(
            hou.shelves.shelfSets().values()
        )
    except Exception:
        return []

    result = []
    for shelf_set in values:
        try:
            if shelf_set.isReadOnly():
                continue
        except Exception:
            pass
        result.append(shelf_set)
    return result


def ensure_shelf():
    hou = _hou()
    try:
        hou.shelves.reloadShelfFiles()
    except Exception:
        pass

    shelf = _shelf_object()
    if shelf is None:
        return False

    for shelf_set in _writable_shelf_sets():
        try:
            current = tuple(
                shelf_set.shelves() or ()
            )
            if shelf in current:
                return True
            shelf_set.setShelves(
                current + (shelf,)
            )
            return True
        except Exception:
            continue

    return True


def remove_shelf():
    shelf = _shelf_object()
    if shelf is None:
        return False

    removed = False
    for shelf_set in _writable_shelf_sets():
        try:
            current = tuple(
                shelf_set.shelves() or ()
            )
            if shelf not in current:
                continue
            shelf_set.setShelves(
                tuple(
                    item
                    for item in current
                    if item != shelf
                )
            )
            removed = True
        except Exception:
            continue
    return removed


def apply_current_integration():
    settings = _current_settings()
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
