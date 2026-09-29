# -*- coding: utf-8 -*-

from . import metrics
from . import palette


_STYLE_VALUES = dict(vars(palette))
_STYLE_VALUES.update(vars(metrics))


COMPONENT_STYLES = """
/* ---------------------------------------------------------------
   Shared UI components
   --------------------------------------------------------------- */
QLineEdit#SearchField {
    background-color: %(FILTER_BG)s;
    border: 1px solid %(BORDER_SOFT)s;
    border-radius: %(BORDER_RADIUS_CONTROL)spx;
    min-height: %(SEARCH_FIELD_MIN_HEIGHT)spx;
    padding: %(SEARCH_FIELD_PADDING_VERTICAL)spx %(SEARCH_FIELD_PADDING_HORIZONTAL)spx;
}

QLineEdit#SearchField:focus {
    border: 1px solid %(FOCUS_BORDER)s;
}

QMenuBar#ToolboxMenuBar {
    background-color: %(CONTROL_BG)s;
    color: %(TEXT_PRIMARY)s;
    border: 0px;
    border-bottom: 1px solid %(BORDER_TOPBAR)s;
    padding: 0px 4px;
}

QMenuBar#ToolboxMenuBar::item {
    background-color: transparent;
    color: %(TEXT_PRIMARY)s;
    padding: %(RUNTIME_TAB_PADDING_VERTICAL)spx %(RUNTIME_TAB_PADDING_HORIZONTAL)spx;
    margin: 0px;
}

QMenuBar#ToolboxMenuBar::item:selected,
QMenuBar#ToolboxMenuBar::item:pressed {
    background-color: %(ICON_BUTTON_HOVER_BG)s;
    color: %(TEXT_STRONG)s;
}

QStatusBar#ToolboxStatusBar {
    background-color: %(STATUS_BG)s;
    color: %(TEXT_STATUS)s;
    border-top: 1px solid %(BORDER_INSET)s;
}

QStatusBar#ToolboxStatusBar::item {
    border: 0px;
}

QLabel#StatusLogs {
    color: %(TEXT_STATUS)s;
    padding: 0px 6px;
}

QToolButton#StatusAction {
    background-color: transparent;
    color: %(TEXT_STATUS)s;
    border: 0px;
    border-radius: 0px;
    padding: 2px 7px;
}

QToolButton#StatusAction:hover {
    background-color: %(ICON_BUTTON_HOVER_BG)s;
    color: %(TEXT_STRONG)s;
    border: 0px;
}

QToolButton#StatusAction:pressed {
    background-color: %(ICON_BUTTON_PRESSED_BG)s;
    border: 0px;
}

QMenu {
    background-color: %(PANEL_BG)s;
    color: %(TEXT_PRIMARY)s;
    border: 1px solid %(BORDER_GROUP)s;
    padding: 4px;
}

QMenu::item {
    background-color: transparent;
    color: %(TEXT_PRIMARY)s;
    padding: 5px 22px 5px 9px;
    border: 0px;
}

QMenu::item:selected {
    background-color: %(ICON_BUTTON_HOVER_BG)s;
    color: %(TEXT_STRONG)s;
}

QMenu::item:disabled {
    color: %(TEXT_DISABLED)s;
}

QMenu::separator {
    height: 1px;
    background-color: %(SEPARATOR)s;
    margin: 4px 6px;
}
""" % _STYLE_VALUES


__all__ = [
    "COMPONENT_STYLES",
]
