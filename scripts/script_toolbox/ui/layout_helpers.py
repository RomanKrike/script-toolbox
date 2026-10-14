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
from ..style.metrics import SINGLE_LINE_CONTROL_HEIGHT
from ..style.metrics import CONTROL_BORDER_WIDTH
from ..style.metrics import CONTROL_PADDING_VERTICAL


def _set_contents_margins(layout, margins):
    layout.setContentsMargins(
        margins[0],
        margins[1],
        margins[2],
        margins[3]
    )


def set_layout_margins(layout, margins):
    """Apply shared margins without changing a layout's spacing."""
    _set_contents_margins(
        layout,
        margins
    )
    return layout


def _set_form_growth(form):
    try:
        form.setFieldGrowthPolicy(
            QtGui.QFormLayout.AllNonFixedFieldsGrow
        )
    except Exception:
        pass


def configure_layout(
    layout,
    margins=MARGINS_NONE,
    spacing=INLINE_CONTROL_SPACING
):
    """Apply explicit shared margins and spacing to a layout."""
    _set_contents_margins(
        layout,
        margins
    )
    layout.setSpacing(spacing)
    return layout


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
    return configure_layout(
        layout,
        margins=MARGINS_NONE,
        spacing=spacing
    )


def configure_runtime_item_geometry(widget, item, reference=None):
    """Give inline items one row footprint without resizing their content.

    Minimums preserve font-driven growth and explicit Column height settings.
    Icon artwork, images, multiline fields and text retain their own sizes.
    """
    kind = item.get("kind")
    props = item.get("props", {})
    single_line = kind in (
        "button", "toggle_button", "string", "integer", "float", "menu",
        "color", "checkbox", "label", "icon", "toggle_icon",
    )
    if kind == "field":
        single_line = not (props.get("display_mode") == "list" and
                           props.get("multiple", True))
    if widget is not None and single_line:
        # Native spin/combo size hints differ across Qt styles even with the
        # same QSS padding. Size actual controls, not only their outer wrapper.
        if kind not in ("icon", "toggle_icon"):
            classes = (QtGui.QLineEdit, QtGui.QAbstractSpinBox, QtGui.QComboBox,
                       QtGui.QPushButton, QtGui.QToolButton, QtGui.QCheckBox, QtGui.QSlider)
            controls = [widget] + widget.findChildren(QtGui.QWidget)
            for control in controls:
                if isinstance(control, classes):
                    if isinstance(control.parentWidget(), (QtGui.QAbstractSpinBox, QtGui.QComboBox)):
                        continue
                    # The renderer has not parented its root yet. Measure the
                    # owning surface's font, not the platform default font.
                    source = reference if reference is not None else control
                    height = max(SINGLE_LINE_CONTROL_HEIGHT,
                                 source.fontMetrics().height() +
                                 2 * (CONTROL_PADDING_VERTICAL + CONTROL_BORDER_WIDTH))
                    if isinstance(control, QtGui.QAbstractButton):
                        icon_size = getattr(control, "_centered_icon_size", control.iconSize())
                        height = max(height, icon_size.height() +
                                     2 * (CONTROL_PADDING_VERTICAL + CONTROL_BORDER_WIDTH))
                    control.setFixedHeight(height)
        widget.setMinimumHeight(max(widget.minimumHeight(), SINGLE_LINE_CONTROL_HEIGHT))
    return widget


__all__ = [
    "configure_inline_layout",
    "configure_runtime_item_geometry",
    "configure_layout",
    "configure_property_form",
    "configure_property_group_form",
    "set_layout_margins",
]
