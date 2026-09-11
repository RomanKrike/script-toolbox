# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..compat import QtGui
from ..core.event_bindings import dispatch_item_event
from ..model.bindings import binding_events
from ..model.bindings import matching_bindings
from ..pycompat import text_type


_RENDERER_MARKER = "_script_toolbox_event_binding_renderer"
_SEEN_MOUSE_EVENTS = set()


def _event_key(event):
    return id(event)


def _mark_event_seen(event):
    key = _event_key(event)
    if key in _SEEN_MOUSE_EVENTS:
        return False

    _SEEN_MOUSE_EVENTS.add(key)
    QtCore.QTimer.singleShot(
        0,
        lambda current=key: _SEEN_MOUSE_EVENTS.discard(current)
    )
    return True


def _mouse_button(event):
    button = event.button()
    if button == QtCore.Qt.MiddleButton:
        return "middle"
    if button == QtCore.Qt.RightButton:
        return "right"
    return "left"


def _modifiers(event):
    value = event.modifiers()
    result = []
    if value & QtCore.Qt.ControlModifier:
        result.append("ctrl")
    if value & QtCore.Qt.AltModifier:
        result.append("alt")
    if value & QtCore.Qt.ShiftModifier:
        result.append("shift")
    return result


def _dispatch(
    toolbox,
    item,
    event,
    mouse_button=None,
    modifiers=None,
    value=None,
    old_value=None
):
    callback = getattr(toolbox, "dispatch_binding_event", None)
    if callback is not None:
        return callback(
            item,
            event,
            value=value,
            old_value=old_value,
            mouse_button=mouse_button,
            modifiers=modifiers
        )

    return dispatch_item_event(
        toolbox,
        item,
        event,
        value=value,
        old_value=old_value,
        mouse_button=mouse_button,
        modifiers=modifiers,
        parent=toolbox
    )


class MouseBindingFilter(QtCore.QObject):

    def __init__(self, toolbox, item, parent=None):
        QtCore.QObject.__init__(self, parent)
        self.toolbox = toolbox
        self.item = item
        self.pending_clicks = {}
        self.skip_release = set()

    def _signature(self, button, modifiers):
        return (button, tuple(modifiers or []))

    def _bindings(self, event, button, modifiers):
        return matching_bindings(
            self.item,
            event,
            mouse_button=button,
            modifiers=modifiers
        )

    def _suppress_button_clicked(self, button):
        if (
            self.item.get("kind") not in ("button", "toggle_button") or
            button != "left"
        ):
            return

        suppressed = getattr(
            self.toolbox,
            "_binding_widget_click_suppression",
            None
        )
        if suppressed is None:
            suppressed = set()
            self.toolbox._binding_widget_click_suppression = suppressed

        suppressed.add(text_type(self.item.get("id", "")))

    def _dispatch_click(self, button, modifiers):
        self.pending_clicks.pop(
            self._signature(button, modifiers),
            None
        )
        _dispatch(
            self.toolbox,
            self.item,
            "click",
            mouse_button=button,
            modifiers=modifiers,
            value=self.toolbox.get_value(self.item.get("id"))
        )

    def eventFilter(self, watched, event):
        event_type = event.type()
        if event_type not in (
            QtCore.QEvent.MouseButtonRelease,
            QtCore.QEvent.MouseButtonDblClick,
        ):
            return False

        if not _mark_event_seen(event):
            return False

        button = _mouse_button(event)
        modifiers = _modifiers(event)
        signature = self._signature(button, modifiers)
        self._suppress_button_clicked(button)

        if event_type == QtCore.QEvent.MouseButtonDblClick:
            timer = self.pending_clicks.pop(signature, None)
            if timer is not None:
                timer.stop()
                timer.deleteLater()

            self.skip_release.add(signature)
            if self._bindings("double_click", button, modifiers):
                _dispatch(
                    self.toolbox,
                    self.item,
                    "double_click",
                    mouse_button=button,
                    modifiers=modifiers,
                    value=self.toolbox.get_value(self.item.get("id"))
                )
            return False

        if signature in self.skip_release:
            self.skip_release.discard(signature)
            return False

        click_bindings = self._bindings("click", button, modifiers)
        if not click_bindings:
            return False

        double_bindings = self._bindings(
            "double_click",
            button,
            modifiers
        )
        if not double_bindings:
            self._dispatch_click(button, modifiers)
            return False

        timer = QtCore.QTimer(self)
        timer.setSingleShot(True)
        timer.setInterval(QtGui.QApplication.doubleClickInterval())
        timer.timeout.connect(
            lambda current_button=button, current_modifiers=list(modifiers):
            self._dispatch_click(current_button, current_modifiers)
        )
        self.pending_clicks[signature] = timer
        timer.start()
        return False


def _mouse_targets(widget, kind):
    candidates = [widget]
    try:
        candidates.extend(widget.findChildren(QtGui.QWidget))
    except Exception:
        pass

    result = []

    def add(candidate):
        if candidate not in result:
            result.append(candidate)

    for candidate in candidates:
        if kind in ("button", "toggle_button") and isinstance(
            candidate,
            QtGui.QAbstractButton
        ):
            add(candidate)
        elif kind in ("icon", "toggle_icon", "label") and isinstance(
            candidate,
            (QtGui.QAbstractButton, QtGui.QLabel)
        ):
            add(candidate)
        elif kind == "string" and isinstance(candidate, QtGui.QLineEdit):
            add(candidate)
        elif kind in ("integer", "float") and isinstance(
            candidate,
            (QtGui.QAbstractSpinBox, QtGui.QSlider)
        ):
            add(candidate)
        elif kind == "checkbox" and isinstance(candidate, QtGui.QCheckBox):
            add(candidate)
        elif kind == "menu" and isinstance(candidate, QtGui.QComboBox):
            add(candidate)
        elif kind == "color" and isinstance(
            candidate,
            QtGui.QAbstractButton
        ):
            add(candidate)
        elif kind == "field" and isinstance(
            candidate,
            (QtGui.QLineEdit, QtGui.QAbstractItemView)
        ):
            add(candidate)

    return result


def _install_mouse_bindings(widget, toolbox, item):
    events = binding_events(item.get("kind"))
    if not any(
        event in ("click", "double_click")
        for event in events
    ):
        return

    for target in _mouse_targets(widget, item.get("kind")):
        installed_for = getattr(
            target,
            "_script_toolbox_binding_item",
            None
        )
        item_id = text_type(item.get("id", ""))
        if installed_for == item_id:
            continue

        filter_object = MouseBindingFilter(
            toolbox,
            item,
            parent=target
        )
        target.installEventFilter(filter_object)
        target._script_toolbox_binding_filter = filter_object
        target._script_toolbox_binding_item = item_id


def _semantic_value(toolbox, item):
    try:
        return toolbox.get_value(item.get("id"))
    except Exception:
        return item.get("value")


def _install_editing_finished(widget, toolbox, item):
    if "editing_finished" not in binding_events(item.get("kind")):
        return

    target_class = (
        QtGui.QLineEdit
        if item.get("kind") == "string"
        else QtGui.QAbstractSpinBox
    )
    candidates = []
    try:
        candidates = widget.findChildren(target_class)
    except Exception:
        pass

    if isinstance(widget, target_class):
        candidates.insert(0, widget)

    for control in candidates:
        if getattr(control, "_script_toolbox_editing_binding", False):
            continue

        control._script_toolbox_editing_binding = True
        control.editingFinished.connect(
            lambda current=item:
            _dispatch(
                toolbox,
                current,
                "editing_finished",
                value=_semantic_value(toolbox, current)
            )
        )


def _install_field_selection(widget, toolbox, item):
    if "selection_changed" not in binding_events("field"):
        return

    candidates = [widget]
    try:
        candidates.extend(widget.findChildren(QtGui.QWidget))
    except Exception:
        pass

    for control in candidates:
        if not hasattr(control, "selected_values"):
            continue
        if not hasattr(control, "itemSelectionChanged"):
            continue
        if getattr(control, "_script_toolbox_selection_binding", False):
            continue

        control._script_toolbox_selection_binding = True
        try:
            control._script_toolbox_binding_selection = list(
                control.selected_values()
            )
        except Exception:
            control._script_toolbox_binding_selection = []

        def selection_changed(
            current_item=item,
            current_control=control
        ):
            try:
                value = list(current_control.selected_values())
            except Exception:
                value = []
            old_value = getattr(
                current_control,
                "_script_toolbox_binding_selection",
                []
            )
            if old_value == value:
                return
            current_control._script_toolbox_binding_selection = list(value)
            _dispatch(
                toolbox,
                current_item,
                "selection_changed",
                value=value,
                old_value=old_value
            )

        control.itemSelectionChanged.connect(selection_changed)
        break


def _attach_runtime_bindings(widget, toolbox, item):
    if widget is None:
        return widget

    _install_mouse_bindings(widget, toolbox, item)
    _install_editing_finished(widget, toolbox, item)
    if item.get("kind") == "field":
        _install_field_selection(widget, toolbox, item)
    return widget


def install_event_binding_hooks(registry):
    """Decorate registered renderers with event-filter attachment once."""
    for kind in registry.kinds():
        if not binding_events(kind):
            continue

        renderer = registry.renderer_for(kind)
        if getattr(renderer, _RENDERER_MARKER, False):
            continue

        def wrapper(
            owner,
            item,
            compact=False,
            original=renderer
        ):
            widget = original(owner, item, compact=compact)
            return _attach_runtime_bindings(
                widget,
                owner.toolbox,
                item
            )

        setattr(wrapper, _RENDERER_MARKER, True)
        registry.register(kind, wrapper, replace=True)

    return True


__all__ = [
    "MouseBindingFilter",
    "install_event_binding_hooks",
]
