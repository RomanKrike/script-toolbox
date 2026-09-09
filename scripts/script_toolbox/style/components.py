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
""" % vars(palette)


__all__ = [
    "COMPONENT_STYLES",
]
