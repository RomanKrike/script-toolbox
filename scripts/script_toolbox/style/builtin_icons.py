# -*- coding: utf-8 -*-
from __future__ import print_function

import os

from ..compat import QtCore
from ..compat import QtGui
from ..pycompat import text_type
from .palette import TOOLBAR_ICON


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
    ("folder-open", "Browse Icons", "folder-open.svg"),
    ("add", "Add", "add.svg"),
    ("close", "Close", "close.svg"),
    ("add-circle", "Add Circle", "add-circle.svg"),
    ("close-circle", "Close Circle", "close-circle.svg"),
    ("up", "Move Up", "alt-arrow-up.svg"),
    ("down", "Move Down", "alt-arrow-down.svg"),
    ("delete", "Delete", "trash-bin-minimalistic-2.svg"),
    ("clear", "Clear", "broom.svg"),
    ("reload", "Reload", "restart.svg"),
    ("gear", "Settings", "settings.svg"),
)

_ALIASES = {
    "update": "import",
    "settings": "gear",
}

_ICON_FILES = dict(
    (key, filename)
    for key, label, filename in _ICON_ENTRIES
)
_FILENAME_KEYS = dict(
    (filename, key)
    for key, label, filename in _ICON_ENTRIES
)
_ICON_CACHE = {}
_ICON_PIXMAP_SIZES = (
    10,
    12,
    16,
    18,
    20,
    24,
    32,
    48,
    64,
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


def solar_icon_directory():
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


def _tinted_icon(resource):
    """Render a monochrome SVG through the shared toolbar color token."""
    source = QtGui.QIcon(resource)
    if source.isNull():
        return source

    result = QtGui.QIcon()
    tint = QtGui.QColor(TOOLBAR_ICON)

    for size in _ICON_PIXMAP_SIZES:
        pixmap = source.pixmap(
            size,
            size
        )
        if pixmap.isNull():
            continue

        painter = QtGui.QPainter(
            pixmap
        )
        try:
            painter.setCompositionMode(
                QtGui.QPainter.CompositionMode_SourceIn
            )
            painter.fillRect(
                pixmap.rect(),
                tint
            )
        finally:
            painter.end()

        result.addPixmap(
            pixmap
        )

    if result.isNull():
        return source
    return result


def builtin_icon(name):
    resource = builtin_icon_resource(name)

    if not resource:
        return QtGui.QIcon()

    cached = _ICON_CACHE.get(resource)
    if cached is not None:
        return cached

    icon = _tinted_icon(resource)
    _ICON_CACHE[resource] = icon
    return icon


__all__ = [
    "builtin_icon",
    "builtin_icon_entries",
    "builtin_icon_id_from_path",
    "builtin_icon_resource",
    "solar_icon_directory",
]
