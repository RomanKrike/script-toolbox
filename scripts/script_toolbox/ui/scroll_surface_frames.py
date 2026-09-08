# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtGui


_INSTALLED_RUNTIME = False
_INSTALLED_SCRIPT_EDITOR = False
_INSTALLED_PROPERTIES = False

_FRAME_STYLE = """
QFrame#ScrollSurfaceFrame {
    background-color: #202020;
    border: 1px solid #151515;
    border-radius: 2px;
}
"""

_RUNTIME_FIELD_FRAME_STYLE = """
QFrame#ScrollSurfaceFrame {
    background-color: #303030;
    border: 1px solid #1b1b1b;
    border-radius: 3px;
}
"""

_CHILD_STYLE = """
border: 0px;
border-radius: 0px;
"""


def _frame_style(background, border):
    if background == "#202020" and border == "#151515":
        return _FRAME_STYLE

    return """
QFrame#ScrollSurfaceFrame {
    background-color: %s;
    border: 1px solid %s;
    border-radius: 2px;
}
""" % (
        background,
        border
    )


def _bounded_maximum(value):
    try:
        value = int(value)
    except Exception:
        return None

    # Qt's default QWidget maximum is 16777215.  Do not copy that as an
    # explicit constraint; it only matters when the source widget is bounded.
    if value >= 16777215:
        return None
    return value


def _copy_constraints(widget, frame):
    """Preserve the source control's *outer* geometry after framing.

    The external frame replaces the control's own 1 px border; it must not
    make a fixed-height runtime control two pixels taller.  The frame keeps the
    exact original min/max bounds and its 1 px contents margin is consumed from
    the inner viewport area instead.  This prevents cumulative layout growth
    in long toolboxes while still keeping scrollbars away from the visible
    border.
    """
    try:
        frame.setSizePolicy(widget.sizePolicy())
    except Exception:
        pass

    try:
        minimum_height = int(widget.minimumHeight())
        if minimum_height > 0:
            frame.setMinimumHeight(minimum_height)
    except Exception:
        pass

    try:
        maximum_height = _bounded_maximum(widget.maximumHeight())
        if maximum_height is not None:
            frame.setMaximumHeight(maximum_height)
    except Exception:
        pass

    try:
        minimum_width = int(widget.minimumWidth())
        if minimum_width > 0:
            frame.setMinimumWidth(minimum_width)
    except Exception:
        pass

    try:
        maximum_width = _bounded_maximum(widget.maximumWidth())
        if maximum_width is not None:
            frame.setMaximumWidth(maximum_width)
    except Exception:
        pass


def _find_layout(layout, target):
    """Find the nested layout that directly owns *target*."""
    if layout is None:
        return None, -1

    for index in range(layout.count()):
        item = layout.itemAt(index)
        if item is None:
            continue

        if item.widget() is target:
            return layout, index

        child_layout = item.layout()
        if child_layout is not None:
            found_layout, found_index = _find_layout(
                child_layout,
                target
            )
            if found_layout is not None:
                return found_layout, found_index

    return None, -1


def _make_frame(
    widget,
    parent,
    background="#202020",
    border="#151515"
):
    frame = QtGui.QFrame(parent)
    frame.setObjectName("ScrollSurfaceFrame")
    frame.setStyleSheet(
        _frame_style(
            background,
            border
        )
    )

    layout = QtGui.QVBoxLayout(frame)
    layout.setContentsMargins(1, 1, 1, 1)
    layout.setSpacing(0)

    try:
        widget.setFrameShape(QtGui.QFrame.NoFrame)
    except Exception:
        pass

    try:
        existing = widget.styleSheet() or ""
        widget.setStyleSheet(
            existing + "\n" + _CHILD_STYLE
        )
    except Exception:
        pass

    _copy_constraints(widget, frame)
    return frame, layout


def wrap_scroll_widget(
    widget,
    background="#202020",
    border="#151515"
):
    """Move a framed QAbstractScrollArea into an external border frame.

    Maya/Qt4 paints scrollbars inside QAbstractScrollArea's frame rectangle.
    With a QSS border this can cover the right/bottom border pixels. Keeping
    the border on one shared parent QFrame makes scroll geometry independent
    from the visible outline and works consistently for QListWidget,
    QTreeWidget and QPlainTextEdit descendants.
    """
    if widget is None:
        return None

    existing = getattr(
        widget,
        "_script_toolbox_scroll_surface_frame",
        None
    )
    if existing is not None:
        return existing

    parent = widget.parentWidget()
    if parent is None:
        return None

    # QSplitter owns children directly instead of through a public layout.
    if isinstance(parent, QtGui.QSplitter):
        index = parent.indexOf(widget)
        if index < 0:
            return None

        try:
            sizes = parent.sizes()
        except Exception:
            sizes = None

        frame, frame_layout = _make_frame(
            widget,
            parent,
            background=background,
            border=border
        )
        widget.setParent(frame)
        frame_layout.addWidget(widget)
        parent.insertWidget(index, frame)

        if sizes:
            try:
                parent.setSizes(sizes)
            except Exception:
                pass

        widget._script_toolbox_scroll_surface_frame = frame
        return frame

    root_layout = parent.layout()
    owner_layout, index = _find_layout(
        root_layout,
        widget
    )
    if owner_layout is None or index < 0:
        return None

    frame, frame_layout = _make_frame(
        widget,
        parent,
        background=background,
        border=border
    )

    # QFormLayout needs row/role replacement rather than insertWidget().
    if isinstance(owner_layout, QtGui.QFormLayout):
        try:
            row, role = owner_layout.getWidgetPosition(widget)
        except Exception:
            return None

        if row < 0:
            return None

        owner_layout.removeWidget(widget)
        widget.setParent(frame)
        frame_layout.addWidget(widget)
        owner_layout.setWidget(row, role, frame)

        widget._script_toolbox_scroll_surface_frame = frame
        return frame

    try:
        stretch = owner_layout.stretch(index)
    except Exception:
        stretch = 0

    try:
        item = owner_layout.itemAt(index)
        alignment = item.alignment() if item is not None else 0
    except Exception:
        alignment = 0

    owner_layout.removeWidget(widget)
    widget.setParent(frame)
    frame_layout.addWidget(widget)

    try:
        owner_layout.insertWidget(
            index,
            frame,
            stretch,
            alignment
        )
    except Exception:
        try:
            owner_layout.insertWidget(index, frame)
        except Exception:
            return None

    widget._script_toolbox_scroll_surface_frame = frame
    return frame


def install_runtime_scroll_frames(registry, runtime_module):
    """Frame runtime list Fields without changing their public widget API."""
    global _INSTALLED_RUNTIME
    if _INSTALLED_RUNTIME:
        return

    original = registry.renderer_for("field")
    if original is None:
        return

    def render_field(owner, item, compact=False):
        result = original(
            owner,
            item,
            compact=compact
        )

        list_mode = (
            item.get("display_mode") == "list" and
            bool(item.get("multiple", True))
        )
        if not list_mode:
            return result

        control = owner.toolbox.field_widgets.get(
            item.get("id")
        )
        if (
            control is not None and
            isinstance(control, runtime_module.DisplayFieldList)
        ):
            frame = wrap_scroll_widget(
                control,
                background="#303030",
                border="#1b1b1b"
            )
            if frame is not None:
                frame.setStyleSheet(
                    _RUNTIME_FIELD_FRAME_STYLE
                )

        return result

    registry.register(
        "field",
        render_field,
        replace=True
    )
    _INSTALLED_RUNTIME = True


def install_script_editor_scroll_frames(script_editor_class):
    """Frame both code and output text areas used by every script editor."""
    global _INSTALLED_SCRIPT_EDITOR
    if _INSTALLED_SCRIPT_EDITOR:
        return

    original_build_ui = script_editor_class.build_ui

    def build_ui(self):
        original_build_ui(self)
        self.editor_scroll_frame = wrap_scroll_widget(
            getattr(self, "editor", None)
        )
        self.output_scroll_frame = wrap_scroll_widget(
            getattr(self, "output", None)
        )

    script_editor_class.build_ui = build_ui
    _INSTALLED_SCRIPT_EDITOR = True


def install_property_editor_scroll_frames():
    """Frame multiline property fields that can show scrollbars."""
    global _INSTALLED_PROPERTIES
    if _INSTALLED_PROPERTIES:
        return

    from .properties import basic as basic_module
    from .properties import field as field_module

    menu_class = basic_module.MenuPropertyEditor
    original_menu_init = menu_class.__init__

    def menu_init(self, *args, **kwargs):
        original_menu_init(self, *args, **kwargs)
        self.items_scroll_frame = wrap_scroll_widget(
            getattr(self, "items_edit", None)
        )

    menu_class.__init__ = menu_init

    field_class = field_module.FieldPropertyEditor
    original_field_init = field_class.__init__

    def field_init(self, *args, **kwargs):
        original_field_init(self, *args, **kwargs)
        self.value_scroll_frame = wrap_scroll_widget(
            getattr(self, "value", None)
        )

    field_class.__init__ = field_init
    _INSTALLED_PROPERTIES = True


__all__ = [
    "wrap_scroll_widget",
    "install_runtime_scroll_frames",
    "install_script_editor_scroll_frames",
    "install_property_editor_scroll_frames",
]
