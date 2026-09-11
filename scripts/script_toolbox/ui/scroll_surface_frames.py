# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtGui
from ..style import metrics
from ..style import palette


_INSTALLED_RUNTIME = False
_INSTALLED_SCRIPT_EDITOR = False
_INSTALLED_PROPERTIES = False

# All ScrollSurfaceFrame border geometry is rendered from this one template.
# Surface colors vary by caller; border width/radius are one explicit Qt4
# compatibility contract shared by Runtime Field, editor trees and editors.
_SCROLL_SURFACE_STYLE_VALUES = dict(palette.__dict__)
_SCROLL_SURFACE_STYLE_VALUES.update(vars(metrics))

_FRAME_STYLE_TEMPLATE = """
QFrame#ScrollSurfaceFrame {
    background-color: %(background)s;
    border: %(SCROLL_SURFACE_BORDER_WIDTH)spx solid %(border)s;
    border-radius: %(SCROLL_SURFACE_BORDER_RADIUS)spx;
}
"""

# Runtime Field should match the actual editor list/tree surface, not the
# surrounding EditorPane container. The list stays frameless because the
# external ScrollSurfaceFrame owns the visible outline in Maya/Qt4.

_RUNTIME_FIELD_LIST_STYLE = """
QListWidget#RuntimeFieldList {
    background-color: %(LIST_BG)s;
    alternate-background-color: %(LIST_BG)s;
    color: %(TEXT_LIST)s;
    border: 0px;
    border-radius: 0px;
    outline: 0px;
    padding: 0px;
}

QListWidget#RuntimeFieldList::item {
    min-height: %(LIST_ITEM_MIN_HEIGHT)spx;
    padding: %(LIST_ITEM_PADDING_VERTICAL)spx %(LIST_ITEM_PADDING_HORIZONTAL)spx;
    border: 0px;
}

QListWidget#RuntimeFieldList::item:selected {
    background-color: %(SELECTION_BG)s;
    color: %(SELECTION_TEXT)s;
}
""" % _SCROLL_SURFACE_STYLE_VALUES

_CHILD_STYLE = """
border: 0px;
border-radius: 0px;
"""


def _frame_style(background, border):
    values = dict(_SCROLL_SURFACE_STYLE_VALUES)
    values.update({
        "background": background,
        "border": border,
    })
    return _FRAME_STYLE_TEMPLATE % values


def _apply_runtime_field_surface(control):
    """Apply the editor list surface directly to a runtime Field.

    The top-level toolbox stylesheet is inherited through Maya's host widget
    hierarchy. Some Qt4/Qt5 builds do not reliably repaint the viewport of a
    QListWidget after it is reparented into ScrollSurfaceFrame, so keep a
    local QSS plus palette fallback on the concrete Field control.
    """
    if control is None:
        return

    try:
        existing = control.styleSheet() or ""
        if _RUNTIME_FIELD_LIST_STYLE not in existing:
            control.setStyleSheet(
                existing + "\n" + _RUNTIME_FIELD_LIST_STYLE
            )
    except Exception:
        pass

    try:
        control_palette = control.palette()
        control_palette.setColor(
            QtGui.QPalette.Base,
            QtGui.QColor(palette.LIST_BG)
        )
        control_palette.setColor(
            QtGui.QPalette.AlternateBase,
            QtGui.QColor(palette.LIST_BG)
        )
        control_palette.setColor(
            QtGui.QPalette.Text,
            QtGui.QColor(palette.TEXT_LIST)
        )
        control_palette.setColor(
            QtGui.QPalette.Highlight,
            QtGui.QColor(palette.SELECTION_BG)
        )
        control_palette.setColor(
            QtGui.QPalette.HighlightedText,
            QtGui.QColor(palette.SELECTION_TEXT)
        )
        control.setPalette(control_palette)

        viewport = control.viewport()
        if viewport is not None:
            viewport.setPalette(control_palette)
            viewport.setAutoFillBackground(True)
    except Exception:
        pass


def _bounded_maximum(value):
    try:
        value = int(value)
    except Exception:
        return None

    # Qt's default QWidget maximum is 16777215. Do not copy that as an
    # explicit constraint; it only matters when the source widget is bounded.
    if value >= 16777215:
        return None
    return value


def _copy_constraints(widget, frame):
    """Preserve the source control's *outer* geometry after framing.

    The external frame replaces the control's own 1 px border; it must not
    make a fixed-height runtime control two pixels taller. The frame keeps the
    exact original min/max bounds and its 1 px contents margin is consumed from
    the inner viewport area instead. This prevents cumulative layout growth
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


def _frame_vertical_inset(frame):
    """Return the border + layout inset consumed inside a framed surface."""
    vertical_inset = metrics.SCROLL_SURFACE_BORDER_WIDTH * 2

    try:
        margins = frame.layout().contentsMargins()
        vertical_inset += int(margins.top())
        vertical_inset += int(margins.bottom())
    except Exception:
        vertical_inset += metrics.SCROLL_SURFACE_CONTENT_INSET * 2

    return vertical_inset


def _fit_runtime_field_inside_frame(control, frame):
    """Keep a fixed-height Field fully inside the painted frame.

    There are two independent vertical insets around the child: the QSS frame
    border itself (1 px top + 1 px bottom) and the QVBoxLayout contents margins
    (another 1 px top + 1 px bottom). The previous fix only accounted for the
    layout margins, leaving the child two pixels too tall and still able to
    cover the bottom border in Maya.
    """
    if control is None or frame is None:
        return

    try:
        minimum_height = int(frame.minimumHeight())
        maximum_height = _bounded_maximum(frame.maximumHeight())
    except Exception:
        return

    if (
        minimum_height <= 0 or
        maximum_height is None or
        minimum_height != maximum_height
    ):
        return

    # Do not rely on QFrame.frameWidth(): QSS borders are unreliable there on
    # older Maya/Qt4 builds. The explicit ScrollSurfaceFrame contract owns the
    # border width and child inset used to derive the viewport height.
    inner_height = max(
        1,
        minimum_height - _frame_vertical_inset(frame)
    )

    try:
        control.setMinimumHeight(inner_height)
        control.setMaximumHeight(inner_height)
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
    background=palette.CONTROL_BG,
    border=palette.BORDER_DARK
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
    inset = metrics.SCROLL_SURFACE_CONTENT_INSET
    layout.setContentsMargins(
        inset,
        inset,
        inset,
        inset
    )
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
    background=palette.CONTROL_BG,
    border=palette.BORDER_DARK
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
            _apply_runtime_field_surface(control)

            frame = wrap_scroll_widget(
                control,
                background=palette.LIST_BG,
                border=palette.BORDER_PRESSED
            )
            if frame is not None:
                _fit_runtime_field_inside_frame(
                    control,
                    frame
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
