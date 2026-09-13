# -*- coding: utf-8 -*-

"""Shared Inspector tab chrome matching runtime Tabs folders."""

from ...compat import QtGui
from ...style.metrics import BORDER_RADIUS_PANEL
from ...style.metrics import RUNTIME_TAB_BAR_OFFSET
from ...style.metrics import RUNTIME_TAB_BAR_VERTICAL_OFFSET
from ...style.metrics import RUNTIME_TAB_MIN_HEIGHT
from ...style.metrics import RUNTIME_TAB_PADDING_HORIZONTAL
from ...style.metrics import RUNTIME_TAB_PADDING_VERTICAL
from ...style.metrics import RUNTIME_TAB_PANE_TOP_OFFSET
from ...style.metrics import RUNTIME_TAB_SELECTED_OVERLAP
from ...style.metrics import TAB_BORDER_WIDTH
from ...style.metrics import TAB_MARGIN_RIGHT
from ...style.metrics import TRIGGER_PAGE_MARGINS
from ...style.metrics import TRIGGER_PAGE_SPACING
from ...style.palette import FOLDER_CARD_BG
from ...style.palette import FOLDER_HEADER_HOVER_BG
from ...style.palette import SEPARATOR
from ...style.palette import TEXT_FOLDER_COLLAPSED
from ...style.palette import TEXT_FOLDER_HOVER
from ...style.palette import TEXT_HEADING
from ...style.palette import WINDOW_BG
from ..layout_helpers import configure_layout


_INSPECTOR_TAB_STYLE = """
QTabWidget#InspectorTabs::pane {{
    background-color: transparent;
    border: 0px;
    border-radius: 0px;
    top: {runtime_tab_pane_top_offset}px;
}}

QTabWidget#InspectorTabs::tab-bar {{
    left: {runtime_tab_bar_offset}px;
    top: {runtime_tab_bar_vertical_offset}px;
}}

QTabWidget#InspectorTabs QTabBar::tab {{
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

QTabWidget#InspectorTabs QTabBar::tab:hover {{
    background-color: {folder_header_hover_bg};
    color: {text_folder_hover};
}}

QTabWidget#InspectorTabs QTabBar::tab:selected {{
    background-color: {folder_card_bg};
    color: {text_heading};
    border-color: {separator};
    border-bottom-color: {folder_card_bg};
    margin-bottom: {runtime_tab_selected_overlap}px;
    font-weight: normal;
}}
""".format(
    window_bg=WINDOW_BG,
    folder_card_bg=FOLDER_CARD_BG,
    folder_header_hover_bg=FOLDER_HEADER_HOVER_BG,
    separator=SEPARATOR,
    text_folder_collapsed=TEXT_FOLDER_COLLAPSED,
    text_folder_hover=TEXT_FOLDER_HOVER,
    text_heading=TEXT_HEADING,
    panel_radius=BORDER_RADIUS_PANEL,
    tab_border_width=TAB_BORDER_WIDTH,
    tab_margin_right=TAB_MARGIN_RIGHT,
    runtime_tab_min_height=RUNTIME_TAB_MIN_HEIGHT,
    runtime_tab_padding_vertical=RUNTIME_TAB_PADDING_VERTICAL,
    runtime_tab_padding_horizontal=RUNTIME_TAB_PADDING_HORIZONTAL,
    runtime_tab_bar_offset=RUNTIME_TAB_BAR_OFFSET,
    runtime_tab_bar_vertical_offset=RUNTIME_TAB_BAR_VERTICAL_OFFSET,
    runtime_tab_pane_top_offset=RUNTIME_TAB_PANE_TOP_OFFSET,
    runtime_tab_selected_overlap=RUNTIME_TAB_SELECTED_OVERLAP,
)


_TRIGGER_PANEL_STYLE = """
QGroupBox#TriggerBindingPanel {{
    background-color: transparent;
    border: 0px;
    margin: 0px;
    padding: 0px;
}}
"""


def style_inspector_tabs(tab_widget):
    """Give an Inspector QTabWidget runtime-like tabs without a nested pane."""
    tab_widget.setObjectName("InspectorTabs")
    tab_widget.setStyleSheet(_INSPECTOR_TAB_STYLE)
    return tab_widget


def add_inspector_script_tab(tab_widget, editor, label):
    """Add a script editor page using the shared trigger-page geometry."""
    page = QtGui.QWidget(tab_widget)
    root = QtGui.QVBoxLayout(page)
    configure_layout(
        root,
        margins=TRIGGER_PAGE_MARGINS,
        spacing=TRIGGER_PAGE_SPACING
    )
    root.addWidget(editor, 1)
    tab_widget.addTab(page, label)
    return page


def style_binding_panel(panel):
    """Keep BindingPanel structural only; TRIGGERS owns all outer chrome."""
    panel.setObjectName("TriggerBindingPanel")
    panel.setStyleSheet(_TRIGGER_PANEL_STYLE)
    try:
        panel.setContentsMargins(0, 0, 0, 0)
    except Exception:
        pass
    return panel


__all__ = [
    "add_inspector_script_tab",
    "style_binding_panel",
    "style_inspector_tabs",
]
