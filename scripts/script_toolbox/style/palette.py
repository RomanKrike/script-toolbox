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
LIST_ALT_BG = "#282828"
FILTER_BG = "#262626"
STATUS_BG = "#232323"
TOOLTIP_BG = "#1d1d1d"

# Folder surfaces -----------------------------------------------------------
FOLDER_CARD_BG = "#292b2c"
FOLDER_NESTED_BG = "#282a2b"
FOLDER_HEADER_BG = "#323436"
FOLDER_HEADER_HOVER_BG = "#393c3f"
FOLDER_HEADER_PRESSED_BG = "#2c2e30"
FOLDER_HEADER_COLLAPSED_BG = "#2e3032"
FOLDER_NESTED_HEADER_BG = "#2d2f30"
FOLDER_NESTED_HEADER_HOVER_BG = "#343637"
FOLDER_NESTED_HEADER_COLLAPSED_BG = "#2b2d2e"
SIMPLE_SECTION_NESTED_BG = "#2e3031"

# Borders / separators -----------------------------------------------------
BORDER_TOPBAR = "#111111"
BORDER_DARK = "#151515"
BORDER_PRESSED = "#161616"
BORDER_INSET = "#171717"
BORDER_SOFT = "#191919"
BORDER_PANEL = "#1b1b1b"
BORDER_TAB = "#1c1c1c"
BORDER_DISABLED = "#252525"
BORDER_FOLDER_NESTED = "#393b3d"
BORDER_GROUP = "#414141"
SEPARATOR = "#414346"
TOOLTIP_BORDER = "#555555"
HOVER_BORDER = "#595959"
FOCUS_BORDER = "#78604a"

# Text ---------------------------------------------------------------------
TEXT_PRIMARY = "#d6d6d6"
TEXT_STRONG = "#eeeeee"
TEXT_HEADING = "#e2e2e2"
TEXT_PANE_TITLE = "#e0e0e0"
TEXT_BUTTON = "#dedede"
TEXT_INPUT = "#dddddd"
TEXT_LIST = "#d4d4d4"
TEXT_SECTION = "#d2d2d2"
TEXT_SECTION_NESTED = "#d8d8d8"
TEXT_FOLDER_NESTED = "#d7d7d7"
TEXT_FOLDER_HOVER = "#f1f1f1"
TEXT_FOLDER_COLLAPSED = "#c5c5c5"
TEXT_MUTED = "#858585"
TEXT_STATUS = "#8f8f8f"
TEXT_EDITOR_STATUS = "#8c8c8c"
TEXT_HEADER = "#a8a8a8"
TEXT_TAB = "#aaaaaa"
TEXT_TAB_SELECTED = "#f0f0f0"
TEXT_SUBTLE = "#bdbdbd"
TEXT_DISABLED = "#686868"
TEXT_INPUT_DISABLED = "#6f6f6f"
TEXT_ON_ACCENT = "#ffffff"

# Generic controls ---------------------------------------------------------
BUTTON_BG = "#3a3a3a"
BUTTON_HOVER_BG = "#464646"
BUTTON_PRESSED_BG = "#2f2f2f"
ICON_BUTTON_HOVER_BG = "#404040"
ICON_BUTTON_HOVER_BORDER = "#545454"
ICON_BUTTON_PRESSED_BG = "#272727"
LIST_HOVER_BG = "#333333"

# Accent / selection -------------------------------------------------------
ACCENT = "#b46d35"
SELECTION_BG = "#68462c"
INPUT_SELECTION_BG = "#8b572c"
SELECTION_TEXT = TEXT_ON_ACCENT

# Update / primary action controls ----------------------------------------
UPDATE_BG = "#925426"
UPDATE_BORDER = "#b36b34"
UPDATE_HOVER_BG = "#a7622d"
UPDATE_HOVER_BORDER = "#cc7b3c"
UPDATE_PRESSED_BG = "#7f4720"
UPDATE_DISABLED_BG = "#4a4038"
UPDATE_DISABLED_TEXT = "#8b827a"
UPDATE_DISABLED_BORDER = "#55483e"
ACCEPT_BG = "#9a5826"
ACCEPT_BORDER = "#ba7139"
ACCEPT_HOVER_BG = "#ad652d"
ACCEPT_HOVER_BORDER = "#d18447"

# Tabs / scrolling ---------------------------------------------------------
TAB_HOVER_BG = "#393939"
TAB_SELECTED_BG = BORDER_GROUP
SCROLL_HANDLE_BG = "#4a4a4a"
SCROLL_HANDLE_HOVER_BG = "#5a5a5a"


__all__ = [
    "WINDOW_BG",
    "CONTENT_BG",
    "PANEL_BG",
    "CONTROL_BG",
    "LIST_BG",
    "LIST_ALT_BG",
    "FILTER_BG",
    "STATUS_BG",
    "TOOLTIP_BG",
    "FOLDER_CARD_BG",
    "FOLDER_NESTED_BG",
    "FOLDER_HEADER_BG",
    "FOLDER_HEADER_HOVER_BG",
    "FOLDER_HEADER_PRESSED_BG",
    "FOLDER_HEADER_COLLAPSED_BG",
    "FOLDER_NESTED_HEADER_BG",
    "FOLDER_NESTED_HEADER_HOVER_BG",
    "FOLDER_NESTED_HEADER_COLLAPSED_BG",
    "SIMPLE_SECTION_NESTED_BG",
    "BORDER_TOPBAR",
    "BORDER_DARK",
    "BORDER_PRESSED",
    "BORDER_INSET",
    "BORDER_SOFT",
    "BORDER_PANEL",
    "BORDER_TAB",
    "BORDER_DISABLED",
    "BORDER_FOLDER_NESTED",
    "BORDER_GROUP",
    "SEPARATOR",
    "TOOLTIP_BORDER",
    "HOVER_BORDER",
    "FOCUS_BORDER",
    "TEXT_PRIMARY",
    "TEXT_STRONG",
    "TEXT_HEADING",
    "TEXT_PANE_TITLE",
    "TEXT_BUTTON",
    "TEXT_INPUT",
    "TEXT_LIST",
    "TEXT_SECTION",
    "TEXT_SECTION_NESTED",
    "TEXT_FOLDER_NESTED",
    "TEXT_FOLDER_HOVER",
    "TEXT_FOLDER_COLLAPSED",
    "TEXT_MUTED",
    "TEXT_STATUS",
    "TEXT_EDITOR_STATUS",
    "TEXT_HEADER",
    "TEXT_TAB",
    "TEXT_TAB_SELECTED",
    "TEXT_SUBTLE",
    "TEXT_DISABLED",
    "TEXT_INPUT_DISABLED",
    "TEXT_ON_ACCENT",
    "BUTTON_BG",
    "BUTTON_HOVER_BG",
    "BUTTON_PRESSED_BG",
    "ICON_BUTTON_HOVER_BG",
    "ICON_BUTTON_HOVER_BORDER",
    "ICON_BUTTON_PRESSED_BG",
    "LIST_HOVER_BG",
    "ACCENT",
    "SELECTION_BG",
    "INPUT_SELECTION_BG",
    "SELECTION_TEXT",
    "UPDATE_BG",
    "UPDATE_BORDER",
    "UPDATE_HOVER_BG",
    "UPDATE_HOVER_BORDER",
    "UPDATE_PRESSED_BG",
    "UPDATE_DISABLED_BG",
    "UPDATE_DISABLED_TEXT",
    "UPDATE_DISABLED_BORDER",
    "ACCEPT_BG",
    "ACCEPT_BORDER",
    "ACCEPT_HOVER_BG",
    "ACCEPT_HOVER_BORDER",
    "TAB_HOVER_BG",
    "TAB_SELECTED_BG",
    "SCROLL_HANDLE_BG",
    "SCROLL_HANDLE_HOVER_BG",
]
