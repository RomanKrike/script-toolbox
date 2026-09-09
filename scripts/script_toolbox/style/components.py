# -*- coding: utf-8 -*-

from . import palette


COMPONENT_STYLES = """
/* ---------------------------------------------------------------
   Shared UI components
   --------------------------------------------------------------- */
QLineEdit#SearchField {
    background-color: %(FILTER_BG)s;
    border: 1px solid %(BORDER_SOFT)s;
    border-radius: 2px;
    min-height: 24px;
    padding: 2px 7px;
}

QLineEdit#SearchField:focus {
    border: 1px solid %(FOCUS_BORDER)s;
}

QToolButton#SearchFieldIcon,
QToolButton#SearchFieldClear {
    background-color: transparent;
    border: 0px;
    padding: 0px;
}

QToolButton#SearchFieldClear:hover {
    background-color: %(ICON_BUTTON_HOVER_BG)s;
    border: 0px;
    border-radius: 3px;
}

QToolButton#SearchFieldClear:pressed {
    background-color: %(ICON_BUTTON_PRESSED_BG)s;
    border: 0px;
    border-radius: 3px;
}
""" % vars(palette)


__all__ = [
    "COMPONENT_STYLES",
]
