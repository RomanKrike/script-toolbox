# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..compat import QtGui
from ..model.item_builtins import register_builtin_items
from ..model.item_registry import ITEM_TYPES
from ..model.item_view import item_view
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


def _layout_child_fills_height(child):
    register_builtin_items()
    definition = ITEM_TYPES.get(child.get("kind"))
    return bool(definition and definition.is_layout)


def _add_child_widget(
    layout,
    child_widget,
    stretch,
    vertical_flag,
    fill_height
):
    if fill_height:
        layout.addWidget(
            child_widget,
            stretch
        )
        return

    layout.addWidget(
        child_widget,
        stretch,
        vertical_flag
    )


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

    for raw_child in item.get("items", []) or []:
        child = item_view(raw_child)
        child_widget = owner.build_runtime_widget(
            raw_child,
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
        fill_height = _layout_child_fills_height(
            child
        )
        vertical_policy = (
            QtGui.QSizePolicy.Expanding
            if fill_height
            else QtGui.QSizePolicy.Preferred
        )

        if equal_child:
            child_widget.setSizePolicy(
                QtGui.QSizePolicy.Expanding,
                vertical_policy
            )
            _add_child_widget(
                layout,
                child_widget,
                1,
                vertical_flag,
                fill_height
            )
        elif width_mode == "fixed":
            if fill_height:
                policy = child_widget.sizePolicy()
                child_widget.setSizePolicy(
                    policy.horizontalPolicy(),
                    vertical_policy
                )
            child_widget.setFixedWidth(
                int(child.get("row_width", 120))
            )
            _add_child_widget(
                layout,
                child_widget,
                0,
                vertical_flag,
                fill_height
            )
        elif width_mode == "stretch":
            child_widget.setSizePolicy(
                QtGui.QSizePolicy.Expanding,
                vertical_policy
            )
            _add_child_widget(
                layout,
                child_widget,
                max(
                    1,
                    int(child.get("row_stretch", 1))
                ),
                vertical_flag,
                fill_height
            )
        else:
            if fill_height:
                policy = child_widget.sizePolicy()
                child_widget.setSizePolicy(
                    policy.horizontalPolicy(),
                    vertical_policy
                )
            _add_child_widget(
                layout,
                child_widget,
                0,
                vertical_flag,
                fill_height
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
