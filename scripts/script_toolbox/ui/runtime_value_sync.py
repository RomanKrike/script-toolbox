# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtGui
import logging
from ..model.item_builtins import register_builtin_items
from ..model.item_registry import ITEM_TYPES
from ..pycompat import text_type


_VALUE_RENDERER_MARKER = "_script_toolbox_runtime_value_renderer"


def _controls(root, control_class):
    result = []

    if root is None:
        return result
    explicit = getattr(root, "_item_controls", None)
    if explicit is not None:
        return [control for control in explicit if isinstance(control, control_class)]

    try:
        if isinstance(root, control_class):
            result.append(root)
    except Exception:
        pass

    try:
        result.extend(
            root.findChildren(control_class)
        )
    except Exception:
        pass

    unique = []
    seen = set()
    for control in result:
        identity = id(control)
        if identity in seen:
            continue
        seen.add(identity)
        unique.append(control)
    return unique


def _block_signals(controls):
    previous = []
    for control in controls:
        try:
            previous.append((
                control,
                bool(control.blockSignals(True))
            ))
        except Exception:
            pass
    return previous


def _restore_signals(previous):
    for control, was_blocked in reversed(previous):
        try:
            control.blockSignals(was_blocked)
        except Exception:
            pass


def _numeric_values(value, size):
    if isinstance(value, (list, tuple)):
        values = list(value)
    else:
        values = [value] * size
    while len(values) < size:
        values.append(0)
    return values[:size]


def _float_slider_position(value, minimum, maximum):
    if maximum <= minimum:
        return 0
    ratio = (
        (float(value) - float(minimum)) /
        float(maximum - minimum)
    )
    return max(0, min(10000, int(round(ratio * 10000.0))))


def connect_value_signal(root, signal, callback):
    """Connect during built-in construction; transfer ownership to its binding."""
    signal.connect(callback)
    connections = getattr(root, "_value_connections", None)
    if connections is None:
        connections = root._value_connections = []
    connections.append((signal, callback))


class ValueBinding(object):
    """GUI-thread binding owning only the signal connections it creates."""

    def __init__(self, root):
        self.root = root
        self.active = True
        self._connections = []
        destroyed = getattr(root, "destroyed", None)
        if destroyed is not None:
            self.connect(destroyed, self._root_destroyed)

    def _root_destroyed(self, *args):
        self.dispose()

    def connect(self, signal, callback):
        if not self.active:
            raise RuntimeError("Cannot connect a disposed value binding.")
        signal.connect(callback)
        self._connections.append((signal, callback))

    def sync(self, item):
        raise NotImplementedError

    def dispose(self):
        if not self.active:
            return
        self.active = False
        for signal, callback in self._connections:
            try:
                signal.disconnect(callback)
            except (RuntimeError, TypeError):
                pass
        self._connections = []
        self.root = None


class RuntimeValueBinding(ValueBinding):
    """Typed adapter for built-in controls; never used for custom renderers."""

    def __init__(self, root, owner):
        ValueBinding.__init__(self, root)
        self.owner = owner
        self._connections.extend(getattr(root, "_value_connections", []))
        root._value_connections = []

    def dispose(self):
        ValueBinding.dispose(self)
        self.owner = None

    def _signal_controls(self):
        classes = (
            QtGui.QLineEdit,
            QtGui.QCheckBox,
            QtGui.QSpinBox,
            QtGui.QDoubleSpinBox,
            QtGui.QSlider,
            QtGui.QComboBox,
            QtGui.QPushButton,
        )
        result = []
        for control_class in classes:
            result.extend(_controls(self.root, control_class))
        unique = []
        for control in result:
            if control not in unique:
                unique.append(control)
        return unique

    def _sync_numeric(self, props, is_float):
        spin_class = QtGui.QDoubleSpinBox if is_float else QtGui.QSpinBox
        spins = _controls(self.root, spin_class)
        if not spins:
            return False

        values = _numeric_values(
            props.get("value", 0.0 if is_float else 0),
            len(spins)
        )
        for index, control in enumerate(spins):
            control.setRange(props.get("min", 0.0 if is_float else 0),
                             props.get("max", 1.0 if is_float else 100))
            control.setValue(
                float(values[index]) if is_float else int(values[index])
            )

        sliders = _controls(self.root, QtGui.QSlider)
        minimum = props.get("min", 0.0 if is_float else 0)
        maximum = props.get("max", 1.0 if is_float else 1)
        for index, slider in enumerate(sliders):
            if index >= len(values):
                break
            if is_float:
                slider.setValue(
                    _float_slider_position(
                        values[index],
                        float(minimum),
                        float(maximum)
                    )
                )
            else:
                slider.setRange(int(minimum), int(maximum))
                slider.setValue(int(values[index]))
        return True

    def sync(self, item):
        if not self.active:
            return False
        kind = item.get("kind")
        if kind in ("field", "toggle_button", "toggle_icon"):
            method = {"field": "refresh_field_widget",
                      "toggle_button": "refresh_state_button",
                      "toggle_icon": "refresh_toggle_icon"}[kind]
            getattr(self.owner.toolbox, method)(item["id"])
            return True
        props = item.get("props", {}) or {}
        previous = _block_signals(self._signal_controls())
        try:
            if kind in ("integer", "float"):
                return self._sync_numeric(props, is_float=(kind == "float"))

            checkboxes = _controls(self.root, QtGui.QCheckBox)
            if kind == "checkbox" and checkboxes:
                value = bool(props.get("value", False))
                for control in checkboxes:
                    control.setChecked(value)
                return True

            combos = _controls(self.root, QtGui.QComboBox)
            if kind == "menu" and combos:
                value = text_type(props.get("value", "") or "")
                for control in combos:
                    options = [text_type(option) for option in props.get("items", [])]
                    if "items" in props and [text_type(control.itemText(index)) for index in range(control.count())] != options:
                        control.clear()
                        control.addItems(options)
                    index = control.findText(value)
                    control.setCurrentIndex(index)
                return True

            lines = _controls(self.root, QtGui.QLineEdit)
            if kind == "string" and lines:
                value = text_type(props.get("value", "") or "")
                for control in lines:
                    control.setText(value)
                return True

            if kind == "color":
                styler = getattr(
                    self.owner,
                    "_color_button_style",
                    None
                )
                if styler is None:
                    return False
                for control in _controls(self.root, QtGui.QPushButton):
                    styler(control, props.get("value"))
                return True
        finally:
            _restore_signals(previous)

        return False


def builtin_value_binding_factory(kind, renderer_path=None):
    if renderer_path is not None:
        expected = {
            "toggle_button": ".toggle_button_runtime:render_toggle_button",
            "toggle_icon": ".toggle_icon_runtime:render_toggle_icon",
        }.get(kind, ".runtime_renderers:_render_" + kind)
        if renderer_path != expected:
            return None
    if kind in ("string", "integer", "float", "checkbox", "menu", "color",
                "field", "toggle_button", "toggle_icon"):
        return lambda root, owner, item: RuntimeValueBinding(root, owner)
    return None


def _dispose_binding(binding):
    try:
        binding.dispose()
    except Exception:
        logging.getLogger("script_toolbox").exception("Value binding disposal failed")


def _register_value_widget(self, item_id, binding):
    if not callable(getattr(binding, "sync", None)) or not callable(getattr(binding, "dispose", None)):
        raise TypeError("Value binding must provide sync(item) and dispose().")
    if not hasattr(self, "value_widgets"):
        self.value_widgets = {}
    item_id = text_type(item_id)
    previous = self.value_widgets.get(item_id)
    if previous is binding:
        return binding
    if previous is not None:
        _dispose_binding(previous)
    self.value_widgets[item_id] = binding
    return binding


def _sync_runtime_value(self, key):
    item = self.find_item(key)
    if item is None:
        binding = getattr(self, "value_widgets", {}).pop(text_type(key), None)
        if binding is not None:
            _dispose_binding(binding)
        return False

    item_id = text_type(item.get("id", ""))
    binding = getattr(self, "value_widgets", {}).get(item_id)
    if binding is None:
        # Field refresh is also used without a rendered value binding.
        definition = ITEM_TYPES.get(item.get("kind"))
        if definition is not None and definition.has_capability("field_widget"):
            self.refresh_field_widget(item_id)
            return True
        return False
    if getattr(binding, "active", True) is False:
        del self.value_widgets[item_id]
        return False
    guard = getattr(self, "_value_sync_guard", None)
    if guard is None:
        guard = self._value_sync_guard = set()
    if item_id in guard:
        return False
    guard.add(item_id)
    try:
        return bool(binding.sync(item))
    except Exception:
        logging.getLogger("script_toolbox").exception("Value binding sync failed for %s", item_id)
        if self.value_widgets.get(item_id) is binding:
            del self.value_widgets[item_id]
        _dispose_binding(binding)
        return False
    finally:
        guard.discard(item_id)


class RuntimeValueMixin(object):
    def register_value_widget(self, item_id, binding):
        return _register_value_widget(self, item_id, binding)

    def clear_value_widgets(self):
        bindings = getattr(self, "value_widgets", {})
        self.value_widgets = {}
        for binding in bindings.values():
            _dispose_binding(binding)

    def sync_runtime_value(self, key):
        return _sync_runtime_value(self, key)


def _copy_renderer_markers(target, source):
    try:
        target.__dict__.update(getattr(source, "__dict__", {}))
    except Exception:
        pass


def _value_renderer_wrapper(renderer, factory):
    def render_with_value_registration(owner, item, compact=False):
        root = renderer(owner, item, compact=compact)
        if root is not None:
            try:
                binding = factory(root, owner, item)
                owner.toolbox.register_value_widget(item["id"], binding)
            except Exception:
                root.deleteLater()
                raise
        return root

    _copy_renderer_markers(render_with_value_registration, renderer)
    setattr(render_with_value_registration, _VALUE_RENDERER_MARKER, True)
    return render_with_value_registration


def synchronize_runtime_value_renderers(registry):
    """Decorate newly registered has-value renderers exactly once."""
    register_builtin_items()
    for definition in ITEM_TYPES.all():
        if not definition.has_capability("has_value"):
            continue
        factory = definition.value_binding_factory
        if factory is None:
            continue
        renderer = registry.renderer_for(definition.kind)
        if renderer is None:
            continue
        if getattr(renderer, _VALUE_RENDERER_MARKER, False):
            continue
        registry.register(
            definition.kind,
            _value_renderer_wrapper(renderer, factory),
            replace=True
        )
    return registry



__all__ = ["ValueBinding", "RuntimeValueBinding", "RuntimeValueMixin",
           "builtin_value_binding_factory", "synchronize_runtime_value_renderers"]

