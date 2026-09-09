# -*- coding: utf-8 -*-
from __future__ import print_function

import os

from ..compat import QtCore
from ..compat import QtGui
from ..pycompat import text_type


_RESOURCE_PREFIX = "stsolar"
_RESOURCE_ROOT = os.path.normpath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "resources",
        "icons",
        "solar"
    )
)

_ICON_ENTRIES = (
    ("undo", "Undo", "undo-left-round.svg"),
    ("redo", "Redo", "undo-right-round.svg"),
    ("cut", "Cut", "scissors.svg"),
    ("copy", "Copy", "copy.svg"),
    ("paste", "Paste", "clipboard.svg"),
    ("find", "Find", "magnifier.svg"),
    ("run", "Run", "play.svg"),
    ("import", "Import", "download-minimalistic.svg"),
    ("export", "Export", "upload-minimalistic.svg"),
    ("cloud-download", "Cloud Download", "cloud-download.svg"),
    ("cloud-upload", "Cloud Upload", "cloud-upload.svg"),
    ("up", "Move Up", "alt-arrow-up.svg"),
    ("down", "Move Down", "alt-arrow-down.svg"),
    ("delete", "Delete", "trash-bin-minimalistic-2.svg"),
    ("clear", "Clear", "broom.svg"),
    ("reload", "Reload", "restart.svg"),
    ("gear", "Settings Minimalistic", "settings-minimalistic.svg"),
    ("settings", "Settings", "settings.svg"),
)

# Keep aliases limited to genuine synonyms. In particular, ``update`` must not
# map to ``reload``: the legacy update glyph is the download arrow over a bar.
_ALIASES = {}

_ICON_FILES = dict(
    (key, filename)
    for key, label, filename in _ICON_ENTRIES
)
_FILENAME_KEYS = dict(
    (filename, key)
    for key, label, filename in _ICON_ENTRIES
)


def _register_search_path():
    try:
        QtCore.QDir.addSearchPath(
            _RESOURCE_PREFIX,
            _RESOURCE_ROOT
        )
    except Exception:
        pass


_register_search_path()


def builtin_icons_directory():
    """Return the physical directory containing bundled Solar SVG files."""
    return _RESOURCE_ROOT


def builtin_icon_entries():
    return tuple(
        (key, label)
        for key, label, filename in _ICON_ENTRIES
    )


def builtin_icon_resource(name):
    key = text_type(name or "").strip()
    key = _ALIASES.get(key, key)
    filename = _ICON_FILES.get(key)

    if not filename:
        return ""

    return "{0}:{1}".format(
        _RESOURCE_PREFIX,
        filename
    )


def builtin_icon_id_from_path(value):
    value = text_type(value or "").strip()
    prefix = _RESOURCE_PREFIX + ":"

    if not value.startswith(prefix):
        return ""

    filename = value[len(prefix):]
    return _FILENAME_KEYS.get(filename, "")


def builtin_icon_resource_from_file_path(value):
    """Convert a bundled Solar file path to a portable stsolar resource."""
    value = text_type(value or "").strip()
    if not value:
        return ""

    absolute = os.path.abspath(
        os.path.normpath(value)
    )
    root = os.path.abspath(
        os.path.normpath(_RESOURCE_ROOT)
    )

    if os.path.normcase(os.path.dirname(absolute)) != os.path.normcase(root):
        return ""

    key = _FILENAME_KEYS.get(
        os.path.basename(absolute)
    )
    if not key:
        return ""

    return builtin_icon_resource(key)


def builtin_icon(name):
    resource = builtin_icon_resource(name)

    if not resource:
        return QtGui.QIcon()

    return QtGui.QIcon(resource)


__all__ = [
    "builtin_icon",
    "builtin_icon_entries",
    "builtin_icon_id_from_path",
    "builtin_icon_resource",
    "builtin_icon_resource_from_file_path",
    "builtin_icons_directory",
]
