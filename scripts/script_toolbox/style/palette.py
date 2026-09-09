# -*- coding: utf-8 -*-

"""Shared Script Toolbox UI color palette.

Keep theme colors here so QSS, runtime overrides and Qt compatibility
fallbacks use the same source of truth. Dynamic colors that are part of user
data (for example custom button colors) should stay local to the owning
widget instead of being added to this palette.
"""

# Surfaces -----------------------------------------------------------------
WINDOW_BG = "#292929"
CONTENT_BG = "#2b2b2b"
PANEL_BG = "#303030"
CONTROL_BG = "#202020"
LIST_BG = "#242424"

# Borders / separators -----------------------------------------------------
BORDER_DARK = "#151515"
BORDER_SOFT = "#191919"
BORDER_PANEL = "#1b1b1b"
SEPARATOR = "#414346"
FOCUS_BORDER = "#78604a"

# Text ---------------------------------------------------------------------
TEXT_PRIMARY = "#d6d6d6"
TEXT_STRONG = "#eeeeee"
TEXT_LIST = "#d4d4d4"
TEXT_MUTED = "#858585"
TEXT_DISABLED = "#686868"
TEXT_ON_ACCENT = "#ffffff"

# Accent / selection -------------------------------------------------------
ACCENT = "#b46d35"
SELECTION_BG = "#68462c"
SELECTION_TEXT = TEXT_ON_ACCENT


__all__ = [
    "WINDOW_BG",
    "CONTENT_BG",
    "PANEL_BG",
    "CONTROL_BG",
    "LIST_BG",
    "BORDER_DARK",
    "BORDER_SOFT",
    "BORDER_PANEL",
    "SEPARATOR",
    "FOCUS_BORDER",
    "TEXT_PRIMARY",
    "TEXT_STRONG",
    "TEXT_LIST",
    "TEXT_MUTED",
    "TEXT_DISABLED",
    "TEXT_ON_ACCENT",
    "ACCENT",
    "SELECTION_BG",
    "SELECTION_TEXT",
]
