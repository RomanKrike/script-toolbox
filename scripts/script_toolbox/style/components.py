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

QMenu::separator {
    height: 1px;
    background-color: %(SEPARATOR)s;
    margin: 4px 6px;
}
""" % _STYLE_VALUES


__all__ = [
    "COMPONENT_STYLES",
]
