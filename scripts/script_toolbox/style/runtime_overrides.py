# -*- coding: utf-8 -*-

from .metrics import LIST_ITEM_MIN_HEIGHT
from .metrics import LIST_ITEM_PADDING_HORIZONTAL
from .metrics import LIST_ITEM_PADDING_VERTICAL
from .palette import LIST_BG
from .palette import SELECTION_BG
from .palette import SELECTION_TEXT
from .palette import SEPARATOR
from .palette import TEXT_LIST
from .palette import WINDOW_BG


# Runtime-only QSS fixes that must override the base theme. Keeping these
# rules separate makes host-specific Qt4/Qt5 rendering quirks explicit.
RUNTIME_OVERRIDES = """
/* Qt4/Qt5 can mis-size the first tooltip when QToolTip uses QSS padding.
   The next tooltip is then laid out correctly, which looks like the first
   line was clipped until the cursor moves to another control. Keep tooltip
   colors/border from the base theme, but let the native style own its text
   margins so geometry is stable in Maya 2015 and newer hosts. */
QToolTip {{
    padding: 0px;
}}

/* Keep Parameter Description on the same surface as the main dialog. The
   base theme historically used the lighter panel surface here. Explicit
   palette fallbacks are installed separately for Maya 2015 / Qt4, where
   viewport QSS is not reliable. */
QWidget#PropertyPane,
QScrollArea#PropertyScroll,
QWidget#PropertyViewport,
QWidget#PropertyHost,
QWidget#PropertyEditor {{
    background-color: {window_bg};
    border: 0px;
}}

QFrame#RuntimeSeparatorLine {{
    background-color: transparent;
    border: 0px;
    border-top: 1px solid {separator};
}}

QFrame#RuntimeSeparatorLineVertical {{
    background-color: transparent;
    border: 0px;
    border-left: 1px solid {separator};
}}

/* Runtime Field keeps the editor list surface without row decoration:
   one flat background, no alternating rows or separators, and only the
   selected row receives the editor's orange highlight. The visible outer
   pane border is owned by ScrollSurfaceFrame so Maya/Qt4 scrollbars cannot
   cover its bottom/right edge. */
QListWidget#RuntimeFieldList {{
    background-color: {list_bg};
    alternate-background-color: {list_bg};
    color: {text_list};
    border: 0px;
    border-radius: 0px;
    outline: 0px;
    padding: 0px;
}}

QListWidget#RuntimeFieldList::item {{
    min-height: {list_item_min_height}px;
    padding: {list_item_padding_vertical}px {list_item_padding_horizontal}px;
    border: 0px;
}}

QListWidget#RuntimeFieldList::item:selected {{
    background-color: {selection_bg};
    color: {selection_text};
}}

""".format(
    window_bg=WINDOW_BG,
    separator=SEPARATOR,
    list_bg=LIST_BG,
    text_list=TEXT_LIST,
    selection_bg=SELECTION_BG,
    selection_text=SELECTION_TEXT,
    list_item_min_height=LIST_ITEM_MIN_HEIGHT,
    list_item_padding_vertical=LIST_ITEM_PADDING_VERTICAL,
    list_item_padding_horizontal=LIST_ITEM_PADDING_HORIZONTAL,
)

__all__ = ["RUNTIME_OVERRIDES"]
