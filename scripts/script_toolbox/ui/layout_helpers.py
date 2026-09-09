# -*- coding: utf-8 -*-

"""Small helpers for applying shared layout metrics consistently."""

from ..compat import QtCore
from ..compat import QtGui
from ..style.metrics import INLINE_CONTROL_SPACING
from ..style.metrics import MARGINS_NONE
from ..style.metrics import PROPERTY_FORM_HORIZONTAL_SPACING
from ..style.metrics import PROPERTY_FORM_VERTICAL_SPACING
from ..style.metrics import PROPERTY_GROUP_HORIZONTAL_SPACING
from ..style.metrics import PROPERTY_GROUP_MARGINS
from ..style.metrics import PROPERTY_GROUP_VERTICAL_SPACING


def _set_contents_margins(layout, margins):
    layout.setContentsMargins(
        margins[0],
        margins[1],
        margins[2],
        margins[3]
    )


def _set_form_growth(form):
    try:
        form.setFieldGrowthPolicy(
            QtGui.QFormLayout.AllNonFixedFieldsGrow
        )
    except Exception:
        pass


def configure_property_form(form):
    """Apply the existing top-level property form geometry."""
    form.setHorizontalSpacing(
        PROPERTY_FORM_HORIZONTAL_SPACING
    )
    form.setVerticalSpacing(
        PROPERTY_FORM_VERTICAL_SPACING
    )
    _set_form_growth(form)
    form.setLabelAlignment(
        QtCore.Qt.AlignLeft |
        QtCore.Qt.AlignVCenter
    )
    return form


def configure_property_group_form(form):
    """Apply the existing nested property group form geometry."""
    _set_contents_margins(
        form,
        PROPERTY_GROUP_MARGINS
    )
    form.setHorizontalSpacing(
        PROPERTY_GROUP_HORIZONTAL_SPACING
    )
    form.setVerticalSpacing(
        PROPERTY_GROUP_VERTICAL_SPACING
    )
    _set_form_growth(form)
    return form


def configure_inline_layout(
    layout,
    spacing=INLINE_CONTROL_SPACING
):
    """Apply the flat zero-margin geometry used by inline controls."""
    _set_contents_margins(
        layout,
        MARGINS_NONE
    )
    layout.setSpacing(spacing)
    return layout


__all__ = [
    "configure_inline_layout",
    "configure_property_form",
    "configure_property_group_form",
]
