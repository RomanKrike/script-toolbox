# -*- coding: utf-8 -*-
"""Portable, versioned UI themes. Layout and item data never enter this format."""
import copy
import io
import json
import re

from ..pycompat import text_type

_STRING_TYPES = (str, text_type)
from .preferences import load_preferences, save_preferences

VERSION = 2
DEFAULT_NAME = "Default - Charcoal"
ROLES = (
    ("window", "Window background", "#292b2e"),
    ("panel", "Panels", "#313337"),
    ("input", "Input background", "#27292c"),
    ("border", "Borders", "#45484d"),
    ("text", "Text", "#dadde1"),
    ("secondary", "Secondary text", "#aeb3bb"),
    ("accent", "Accent", "#b46d35"),
    ("selection", "Selection", "#68462c"),
    ("on_accent", "Text on selection / accent", "#ffffff"),
    ("group", "Item / preset group titles", "#bda88f"),
    ("row", "Structure: Row", "#b6c4cf"),
    ("column", "Structure: Column", "#c7b7d7"),
    ("code_gutter", "Code: gutter background", "#3b3d41"),
    ("code_line", "Code: current line", "#313337"),
    ("code_numbers", "Code: line numbers", "#777777"),
    ("syntax_keyword", "Code: keywords", "#d4a15d"),
    ("syntax_string", "Code: strings", "#b9c66b"),
    ("syntax_comment", "Code: comments", "#757575"),
    ("syntax_number", "Code: numbers", "#79a8d7"),
    ("syntax_host", "Code: host commands", "#69b5b5"),
    ("expression_string", "Expressions: strings", "#b9c66b"),
    ("expression_keyword", "Expressions: values", "#d4a15d"),
    ("expression_name", "Expressions: parameter names", "#79a8d7"),
    ("expression_reserved", "Expressions: reserved words", "#c7b7d7"),
    ("expression_error", "Expressions: errors", "#e28b8b"),
)
DEFAULT_COLORS = dict((key, color) for key, label, color in ROLES)


def theme(name=DEFAULT_NAME, colors=None):
    return {"version": VERSION, "name": name,
            "colors": dict(DEFAULT_COLORS if colors is None else colors)}


def builtins():
    soft = dict(DEFAULT_COLORS)
    soft.update(window="#34363a", panel="#3c3f44", input="#2f3135", border="#50545b")
    return [theme(), theme("Soft Dark", soft)]


def validate(data):
    if not isinstance(data, dict) or type(data.get("version")) is not int or data["version"] not in (1, VERSION):
        raise ValueError("Unsupported theme format version.")
    name = data.get("name")
    if not isinstance(name, _STRING_TYPES) or not name.strip() or len(name.strip()) > 80:
        raise ValueError("Theme name must contain 1 to 80 characters.")
    colors = data.get("colors")
    expected = set(key for key, unused, color in ROLES[:8]) if data["version"] == 1 else set(DEFAULT_COLORS)
    if not isinstance(colors, dict) or set(colors) != expected:
        raise ValueError("Theme must contain all colors for its format version.")
    result = dict(DEFAULT_COLORS)
    for key, value in colors.items():
        if not isinstance(value, _STRING_TYPES) or not re.match(r"^#[0-9a-fA-F]{6}$", value):
            raise ValueError("Invalid RGB color for " + key + ".")
        result[key] = value.lower()
    return theme(name.strip(), result)


def load_state():
    data = load_preferences().get("appearance", {})
    saved = []
    reserved = set(t["name"] for t in builtins()) | set(["Custom"])
    if not isinstance(data, dict):
        data = {}
    for candidate in data.get("themes", []) if isinstance(data.get("themes", []), list) else []:
        try:
            candidate = validate(candidate)
        except ValueError:
            continue
        if candidate["name"] not in reserved:
            saved.append(candidate)
            reserved.add(candidate["name"])
    try:
        active = validate(data.get("active"))
    except ValueError:
        active = theme()
    return active, saved


def save_state(active, saved):
    active = validate(active)
    saved = [validate(value) for value in saved]
    prefs = load_preferences()
    prefs["appearance"] = {"active": active, "themes": saved}
    save_preferences(prefs)


def read_theme(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return validate(json.load(handle))


def write_theme(path, value):
    value = validate(value)
    with io.open(path, "w", encoding="utf-8") as handle:
        handle.write(text_type(json.dumps(copy.deepcopy(value), indent=2, sort_keys=True)))
        handle.write(u"\n")
