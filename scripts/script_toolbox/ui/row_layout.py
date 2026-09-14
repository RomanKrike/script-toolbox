# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..compat import QtGui
from ..model.item_builtins import register_builtin_items
from ..model.item_registry import ITEM_TYPES
from ..model.layout_geometry import distribution_spacer_positions


def _props(item):
    value = item.get("props", {}) if isinstance(item, dict) else {}
    return value if isinstance(value, dict) else {}


def _ui(item):
    value = item.get("ui", {}) if isinstance(item, dict) else {}
    return value if isinstance(value, dict) else {}


def _vertical_flag(props):
    vertical = props.get(
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


def _is_divider(child):
    register_builtin_items()
    definition = ITEM_TYPES.get(child.get("kind"))
    return bool(definition and definition.has_capability("divider"))


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
    """Render a horizontal layout container from envelope data."""
    props = _props(item)
    row_widget = QtGui.QWidget()
    row_widget.setObjectName("RuntimeRow")

    try:
        row_widget.setToolTip(
            owner._tooltip(item)
        )
    except Exception:
        row_widget.setToolTip(
            _ui(item).get("tooltip", "")
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
        int(props.get("spacing", 4))
    )

    vertical_flag = _vertical_flag(props)
    equal_widths = bool(
        props.get("equal_widths", False)
    )
    distribution = props.get(
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

        child_ui = _ui(child)
        width_mode = child_ui.get(
            "width_mode",
            "auto"
        )
        equal_child = (
            equal_widths and
            not _is_divider(child)
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
        child_ui = _ui(child)
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
                int(child_ui.get("width", 120))
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
                    int(child_ui.get("stretch", 1))
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
