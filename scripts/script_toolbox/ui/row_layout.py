# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..compat import QtGui
from ..model.layout_geometry import distribution_spacer_positions


def _vertical_flag(item):
    vertical = item.get(
        "vertical_alignment",
        "center"
    )
    return (
        QtCore.Qt.AlignTop
        if vertical == "top"
        else QtCore.Qt.AlignBottom
        if vertical == "bottom"
        else QtCore.Qt.AlignVCenter
    )


def _add_spacer_if_needed(layout, positions, position):
    if position in positions:
        layout.addStretch(1)


def render_row(owner, item, compact=False):
    """Render a Row with parent-level horizontal distribution."""
    row_widget = QtGui.QWidget()
    row_widget.setObjectName("RuntimeRow")

    try:
        row_widget.setToolTip(
            owner._tooltip(item)
        )
    except Exception:
        row_widget.setToolTip(
            item.get("tooltip", "")
        )

    layout = QtGui.QHBoxLayout(
        row_widget
    )
    layout.setContentsMargins(
        0,
        0,
        0,
        0
    )
    layout.setSpacing(
        int(item.get("spacing", 4))
    )

    vertical_flag = _vertical_flag(item)
    equal_widths = bool(
        item.get("equal_widths", False)
    )
    distribution = item.get(
        "horizontal_distribution",
        "left"
    )
    if distribution not in (
        "left",
        "center",
        "right",
        "space_between",
    ):
        distribution = "left"

    children = []
    has_stretch = False

    for child in item.get("items", []) or []:
        child_widget = owner.build_runtime_widget(
            child,
            compact=True
        )
        if child_widget is None:
            continue

        width_mode = child.get(
            "row_width_mode",
            "auto"
        )
        equal_child = (
            equal_widths and
            child.get("kind") != "separator"
        )
        if equal_child or width_mode == "stretch":
            has_stretch = True

        children.append((
            child,
            child_widget,
            width_mode,
            equal_child
        ))

    count = len(children)
    spacers = (
        ()
        if has_stretch
        else distribution_spacer_positions(
            distribution,
            count,
            "left",
            "right"
        )
    )
    _add_spacer_if_needed(
        layout,
        spacers,
        0
    )

    for index, entry in enumerate(children):
        child, child_widget, width_mode, equal_child = entry

        if equal_child:
            child_widget.setSizePolicy(
                QtGui.QSizePolicy.Expanding,
                QtGui.QSizePolicy.Preferred
            )
            layout.addWidget(
                child_widget,
                1,
                vertical_flag
            )
        elif width_mode == "fixed":
            child_widget.setFixedWidth(
                int(child.get("row_width", 120))
            )
            layout.addWidget(
                child_widget,
                0,
                vertical_flag
            )
        elif width_mode == "stretch":
            child_widget.setSizePolicy(
                QtGui.QSizePolicy.Expanding,
                QtGui.QSizePolicy.Preferred
            )
            layout.addWidget(
                child_widget,
                max(
                    1,
                    int(child.get("row_stretch", 1))
                ),
                vertical_flag
            )
        else:
            layout.addWidget(
                child_widget,
                0,
                vertical_flag
            )

        _add_spacer_if_needed(
            layout,
            spacers,
            index + 1
        )

    return row_widget


__all__ = [
    "render_row",
]
