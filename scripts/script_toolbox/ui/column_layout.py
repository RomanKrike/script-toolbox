# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..compat import QtGui
from ..model.layout_geometry import distribution_spacer_positions


def _props(item):
    value = item.get("props", {}) if isinstance(item, dict) else {}
    return value if isinstance(value, dict) else {}


def _ui(item):
    value = item.get("ui", {}) if isinstance(item, dict) else {}
    return value if isinstance(value, dict) else {}


def _horizontal_flag(alignment):
    return (
        QtCore.Qt.AlignRight
        if alignment == "right"
        else QtCore.Qt.AlignHCenter
        if alignment == "center"
        else QtCore.Qt.AlignLeft
    )


def _add_spacer_if_needed(layout, positions, position):
    if position in positions:
        layout.addStretch(1)


def render_column(owner, item, compact=False):
    """Render a vertical layout container using the active runtime registry."""
    props = _props(item)
    widget = QtGui.QWidget()
    widget.setObjectName("RuntimeColumn")
    widget.setSizePolicy(
        QtGui.QSizePolicy.Preferred,
        QtGui.QSizePolicy.Expanding
    )

    try:
        widget.setToolTip(
            owner._tooltip(item)
        )
    except Exception:
        widget.setToolTip(
            _ui(item).get("tooltip", "")
        )

    layout = QtGui.QVBoxLayout(widget)
    layout.setContentsMargins(
        0,
        0,
        0,
        0
    )
    layout.setSpacing(
        int(props.get("spacing", 4))
    )

    alignment = props.get(
        "horizontal_alignment",
        "stretch"
    )
    if alignment not in (
        "stretch",
        "left",
        "center",
        "right",
    ):
        alignment = "stretch"

    distribution = props.get(
        "vertical_distribution",
        "top"
    )
    if distribution not in (
        "top",
        "center",
        "bottom",
        "space_between",
    ):
        distribution = "top"

    children = []
    has_stretch = False

    for child in item.get("items", []) or []:
        child_widget = owner.build_runtime_widget(
            child,
            compact=compact
        )
        if child_widget is None:
            continue

        child_ui = _ui(child)
        height_mode = child_ui.get(
            "height_mode",
            "auto"
        )
        if height_mode not in (
            "auto",
            "stretch",
            "fixed",
        ):
            height_mode = "auto"

        if height_mode == "stretch":
            has_stretch = True

        children.append((
            child,
            child_widget,
            height_mode
        ))

    count = len(children)
    spacers = (
        ()
        if has_stretch
        else distribution_spacer_positions(
            distribution,
            count,
            "top",
            "bottom"
        )
    )
    _add_spacer_if_needed(
        layout,
        spacers,
        0
    )

    for index, entry in enumerate(children):
        child, child_widget, height_mode = entry
        child_ui = _ui(child)

        horizontal_policy = (
            QtGui.QSizePolicy.Expanding
            if alignment == "stretch"
            else QtGui.QSizePolicy.Preferred
        )
        vertical_policy = (
            QtGui.QSizePolicy.Expanding
            if height_mode == "stretch"
            else QtGui.QSizePolicy.Preferred
        )
        child_widget.setSizePolicy(
            horizontal_policy,
            vertical_policy
        )

        if height_mode == "fixed":
            child_widget.setFixedHeight(
                int(child_ui.get("height", 28))
            )

        stretch = (
            max(
                1,
                int(child_ui.get("vertical_stretch", 1))
            )
            if height_mode == "stretch"
            else 0
        )

        if alignment == "stretch":
            layout.addWidget(
                child_widget,
                stretch
            )
        else:
            layout.addWidget(
                child_widget,
                stretch,
                _horizontal_flag(alignment)
            )

        _add_spacer_if_needed(
            layout,
            spacers,
            index + 1
        )

    return widget


__all__ = [
    "render_column",
]
