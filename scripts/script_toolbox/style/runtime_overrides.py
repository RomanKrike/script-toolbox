# -*- coding: utf-8 -*-

from .metrics import BORDER_RADIUS_CARD
from .metrics import BORDER_RADIUS_PANEL
from .metrics import LIST_ITEM_MIN_HEIGHT
from .metrics import LIST_ITEM_PADDING_HORIZONTAL
from .metrics import LIST_ITEM_PADDING_VERTICAL
from .metrics import RUNTIME_TAB_BAR_OFFSET
from .metrics import RUNTIME_TAB_BAR_VERTICAL_OFFSET
from .metrics import RUNTIME_TAB_MIN_HEIGHT
from .metrics import RUNTIME_TAB_PADDING_HORIZONTAL
from .metrics import RUNTIME_TAB_PADDING_VERTICAL
from .metrics import RUNTIME_TAB_PANE_TOP_OFFSET
from .metrics import RUNTIME_TAB_SELECTED_OVERLAP
from .metrics import TAB_BORDER_WIDTH
from .metrics import TAB_MARGIN_RIGHT
from .metrics import TAB_PANE_TOP_OFFSET
from .palette import FOLDER_CARD_BG
from .palette import FOLDER_HEADER_HOVER_BG
from .palette import LIST_BG
from .palette import SELECTION_BG
from .palette import SELECTION_TEXT
from .palette import SEPARATOR
from .palette import TEXT_FOLDER_COLLAPSED
from .palette import TEXT_FOLDER_HOVER
from .palette import TEXT_HEADING
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

/* Runtime QTabWidget owns switching and tab-bar geometry only. Its pane is
   intentionally frameless: Qt/Houdini can clip or anti-alias a one-pixel
   rounded QTabWidget::pane border inconsistently at the corners. The existing
   embedded RuntimeFolder tab page already is a QFrame and exposes the semantic
   folderType="tabs" property, so that stable widget owns the visible surface
   and outline instead. No extra wrapper or runtime item type is introduced.

   The whole runtime tab bar still moves down by one border width and owns the
   seam with the page frame. CreatePaletteTabs keeps its editor geometry
   independently; both surfaces still share tab sizing and colors below. */
QWidget#ToolboxContent QTabWidget::pane {{
    background-color: transparent;
    border: 0px;
    border-radius: 0px;
    top: {runtime_tab_pane_top_offset}px;
}}

QFrame#RuntimeFolder[folderType="tabs"] {{
    background-color: {folder_card_bg};
    border: {tab_border_width}px solid {separator};
    border-radius: {panel_radius}px;
    border-top-left-radius: 0px;
}}

QTabWidget#CreatePaletteTabs::pane {{
    background-color: {folder_card_bg};
    border: {tab_border_width}px solid {separator};
    border-radius: {card_radius}px;
    top: {tab_pane_top_offset}px;
}}

QWidget#ToolboxContent QTabWidget::tab-bar,
QTabWidget#CreatePaletteTabs::tab-bar {{
    left: {runtime_tab_bar_offset}px;
}}

QWidget#ToolboxContent QTabWidget::tab-bar {{
    top: {runtime_tab_bar_vertical_offset}px;
}}

QWidget#ToolboxContent QTabBar::tab,
QTabWidget#CreatePaletteTabs QTabBar::tab {{
    background-color: {window_bg};
    color: {text_folder_collapsed};
    border: {tab_border_width}px solid {separator};
    border-bottom: {tab_border_width}px solid {separator};
    border-top-left-radius: {panel_radius}px;
    border-top-right-radius: {panel_radius}px;
    border-bottom-left-radius: 0px;
    border-bottom-right-radius: 0px;
    min-height: {runtime_tab_min_height}px;
    padding: {runtime_tab_padding_vertical}px {runtime_tab_padding_horizontal}px;
    margin-right: {tab_margin_right}px;
    font-weight: normal;
}}

QWidget#ToolboxContent QTabBar::tab:hover,
QTabWidget#CreatePaletteTabs QTabBar::tab:hover {{
    background-color: {folder_header_hover_bg};
    color: {text_folder_hover};
}}

QWidget#ToolboxContent QTabBar::tab:selected,
QTabWidget#CreatePaletteTabs QTabBar::tab:selected {{
    background-color: {folder_card_bg};
    color: {text_heading};
    border-color: {separator};
    border-bottom-color: {folder_card_bg};
    font-weight: normal;
}}

QWidget#ToolboxContent QTabBar::tab:selected {{
    margin-bottom: {runtime_tab_selected_overlap}px;
}}

QTabWidget#CreatePaletteTabs QTabBar::tab:selected {{
    margin-bottom: -{tab_border_width}px;
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
    folder_card_bg=FOLDER_CARD_BG,
    folder_header_hover_bg=FOLDER_HEADER_HOVER_BG,
    text_folder_collapsed=TEXT_FOLDER_COLLAPSED,
    text_folder_hover=TEXT_FOLDER_HOVER,
    text_heading=TEXT_HEADING,
    card_radius=BORDER_RADIUS_CARD,
    panel_radius=BORDER_RADIUS_PANEL,
    tab_border_width=TAB_BORDER_WIDTH,
    tab_pane_top_offset=TAB_PANE_TOP_OFFSET,
    tab_margin_right=TAB_MARGIN_RIGHT,
    runtime_tab_min_height=RUNTIME_TAB_MIN_HEIGHT,
    runtime_tab_padding_vertical=RUNTIME_TAB_PADDING_VERTICAL,
    runtime_tab_padding_horizontal=RUNTIME_TAB_PADDING_HORIZONTAL,
    runtime_tab_bar_offset=RUNTIME_TAB_BAR_OFFSET,
    runtime_tab_bar_vertical_offset=RUNTIME_TAB_BAR_VERTICAL_OFFSET,
    runtime_tab_pane_top_offset=RUNTIME_TAB_PANE_TOP_OFFSET,
    runtime_tab_selected_overlap=RUNTIME_TAB_SELECTED_OVERLAP,
    list_bg=LIST_BG,
    text_list=TEXT_LIST,
    selection_bg=SELECTION_BG,
    selection_text=SELECTION_TEXT,
    list_item_min_height=LIST_ITEM_MIN_HEIGHT,
    list_item_padding_vertical=LIST_ITEM_PADDING_VERTICAL,
    list_item_padding_horizontal=LIST_ITEM_PADDING_HORIZONTAL,
)

__all__ = ["RUNTIME_OVERRIDES"]
