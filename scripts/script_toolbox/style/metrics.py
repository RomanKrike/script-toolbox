# -*- coding: utf-8 -*-

"""Shared Script Toolbox UI layout metrics.

These values describe repeated presentation geometry only. Functional limits
such as numeric ranges, runtime row sizes and user-configurable spacing stay
with the owning model or widget.
"""

# Generic layout geometry ---------------------------------------------------
MARGINS_NONE = (0, 0, 0, 0)
INLINE_CONTROL_SPACING = 4

# Property editor -----------------------------------------------------------
PROPERTY_EDITOR_SPACING = 8
PROPERTY_FORM_HORIZONTAL_SPACING = 8
PROPERTY_FORM_VERTICAL_SPACING = 6

PROPERTY_GROUP_MARGINS = (7, 7, 7, 7)
PROPERTY_GROUP_HORIZONTAL_SPACING = 8
PROPERTY_GROUP_VERTICAL_SPACING = 5


__all__ = [
    "MARGINS_NONE",
    "INLINE_CONTROL_SPACING",
    "PROPERTY_EDITOR_SPACING",
    "PROPERTY_FORM_HORIZONTAL_SPACING",
    "PROPERTY_FORM_VERTICAL_SPACING",
    "PROPERTY_GROUP_MARGINS",
    "PROPERTY_GROUP_HORIZONTAL_SPACING",
    "PROPERTY_GROUP_VERTICAL_SPACING",
]
