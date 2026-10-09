# -*- coding: utf-8 -*-
from __future__ import print_function

import os

from ..compat import QtCore
from ..compat import QtGui
from ..pycompat import text_type
from .palette import TOOLBAR_ICON
from .metrics import EDITOR_ITEM_ICON_SIZE
from .metrics import SETTINGS_CATEGORY_ICON_SIZE


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
    ("reference", "Preset Reference", "reference.svg"),
    ("undo", "Undo", "undo-left-round.svg"),
    ("redo", "Redo", "undo-right-round.svg"),
    ("cut", "Cut", "scissors.svg"),
    ("copy", "Copy", "copy.svg"),
    ("paste", "Paste", "clipboard.svg"),
    ("find", "Find", "magnifier.svg"),
    ("run", "Run", "play.svg"),
    ("console", "Console", "console.svg"),
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
    ("right", "Expand", "alt-arrow-right.svg"),
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
_ICON_SOURCES = {}
_THEME_ICON_CACHE = {}
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


def _tinted_icon(resource, pixmap_sizes=None, color=TOOLBAR_ICON):
    """Render a monochrome SVG through the shared toolbar color token."""
    source = QtGui.QIcon(resource)
    if source.isNull():
        return source

    result = QtGui.QIcon()
    tint = QtGui.QColor(color)

    for size in (pixmap_sizes or _ICON_PIXMAP_SIZES):
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
    _ICON_SOURCES[result.cacheKey()] = (resource, pixmap_sizes)
    return result


def themed_icon(icon, color):
    source = _ICON_SOURCES.get(icon.cacheKey())
    if source is None:
        return icon
    resource, sizes = source
    key = (resource, color.lower())
    if key not in _THEME_ICON_CACHE:
        if color.lower() == TOOLBAR_ICON.lower() and resource in _ICON_CACHE:
            _THEME_ICON_CACHE[key] = _ICON_CACHE[resource]
        else:
            _THEME_ICON_CACHE[key] = _tinted_icon(resource, sizes, color)
    return _THEME_ICON_CACHE[key]


def _active_icon(icon):
    app = QtGui.QApplication.instance()
    manager = getattr(app, "_script_toolbox_themes", None)
    return themed_icon(icon, manager.active["colors"]["text"]) if manager else icon


def builtin_icon(name):
    resource = builtin_icon_resource(name)

    if not resource:
        return QtGui.QIcon()

    cached = _ICON_CACHE.get(resource)
    if cached is not None:
        return _active_icon(cached)

    icon = _tinted_icon(resource)
    _ICON_CACHE[resource] = icon
    return _active_icon(icon)


def settings_category_icon(name):
    """Settings navigation symbols share the existing monochrome tint."""
    if name == "appearance":
        return item_type_icon("color")
    if name == "general":
        return builtin_icon("gear")
    if name not in ("network", "integrations", "library", "privacy", "about"):
        return QtGui.QIcon()
    resource = os.path.join(os.path.dirname(_RESOURCE_ROOT), "settings", name + ".svg")
    cached = _ICON_CACHE.get(resource)
    if cached is None:
        cached = _tinted_icon(resource, (SETTINGS_CATEGORY_ICON_SIZE, SETTINGS_CATEGORY_ICON_SIZE * 2))
        _ICON_CACHE[resource] = cached
    return _active_icon(cached)


def item_type_icon(kind):
    """Use the same monochrome type symbol in both editor item trees."""
    kind = text_type(kind or "").strip().lower()
    if kind == "folder":
        return builtin_icon("folder-open")
    if kind not in (
        "button", "toggle_button", "icon", "toggle_icon", "string",
        "integer", "float", "checkbox", "menu", "color", "field",
        "label", "text", "separator", "image", "row", "column",
    ):
        kind = "icon"
    resource = os.path.join(os.path.dirname(_RESOURCE_ROOT), "items", kind + ".svg")
    cached = _ICON_CACHE.get(resource)
    if cached is None:
        cached = _tinted_icon(resource, (EDITOR_ITEM_ICON_SIZE, EDITOR_ITEM_ICON_SIZE * 2))
        _ICON_CACHE[resource] = cached
    return _active_icon(cached)


__all__ = [
    "builtin_icon",
    "builtin_icon_entries",
    "builtin_icon_id_from_path",
    "builtin_icon_resource",
    "item_type_icon",
    "settings_category_icon",
    "solar_icon_directory",
]
