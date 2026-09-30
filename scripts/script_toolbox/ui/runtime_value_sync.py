# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtGui
from ..model.fields import ColorField
from ..model.item_builtins import register_builtin_items
from ..model.item_registry import ITEM_TYPES
from ..pycompat import text_type


_VALUE_RENDERER_MARKER = "_script_toolbox_runtime_value_renderer"


def _controls(root, control_class):
    result = []

    if root is None:
        return result

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


class RuntimeValueBinding(object):
    """Synchronize one has-value Item with its already-created Qt controls."""

    def __init__(self, root, owner):
        self.root = root
        self.owner = owner

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
                slider.setValue(int(values[index]))
        return True

    def sync(self, item):
        props = item.get("props", {}) or {}
        previous = _block_signals(self._signal_controls())
        try:
            if self._sync_numeric(props, is_float=True):
                return True
            if self._sync_numeric(props, is_float=False):
                return True

            checkboxes = _controls(self.root, QtGui.QCheckBox)
            if checkboxes:
                value = bool(props.get("value", False))
                for control in checkboxes:
                    control.setChecked(value)
                return True

            combos = _controls(self.root, QtGui.QComboBox)
            if combos:
                value = text_type(props.get("value", "") or "")
                for control in combos:
                    index = control.findText(value)
                    if index >= 0:
                        control.setCurrentIndex(index)
                return True

            lines = _controls(self.root, QtGui.QLineEdit)
            if lines:
                value = text_type(props.get("value", "") or "")
                for control in lines:
                    control.setText(value)
                return True

            definition = ITEM_TYPES.get(item.get("kind"))
            value_field = (
                definition.fields.get("value")
                if definition is not None
                else None
            )
            if isinstance(value_field, ColorField):
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


def _register_value_widget(self, item_id, binding):
    if not hasattr(self, "value_widgets"):
        self.value_widgets = {}
    self.value_widgets[text_type(item_id)] = binding
    return binding


def _sync_runtime_value(self, key):
    item = self.find_item(key)
    if item is None:
        return False

    register_builtin_items()
    definition = ITEM_TYPES.get(item.get("kind"))
    if definition is not None and definition.has_capability("field_widget"):
        self.refresh_field_widget(item["id"])
        return True

    item_id = text_type(item.get("id", ""))
    binding = getattr(self, "value_widgets", {}).get(item_id)
    if binding is None:
        return False

    try:
        return bool(binding.sync(item))
    except Exception:
        try:
            del self.value_widgets[item_id]
        except Exception:
            pass
        return False


class RuntimeValueMixin(object):
    def register_value_widget(self, item_id, binding):
        return _register_value_widget(self, item_id, binding)

    def sync_runtime_value(self, key):
        return _sync_runtime_value(self, key)


def _copy_renderer_markers(target, source):
    try:
        target.__dict__.update(getattr(source, "__dict__", {}))
    except Exception:
        pass


def _value_renderer_wrapper(renderer):
    def render_with_value_registration(owner, item, compact=False):
        root = renderer(owner, item, compact=compact)
        if root is not None:
            owner.toolbox.register_value_widget(
                item["id"],
                RuntimeValueBinding(root, owner)
            )
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
        renderer = registry.renderer_for(definition.kind)
        if renderer is None:
            continue
        if getattr(renderer, _VALUE_RENDERER_MARKER, False):
            continue
        registry.register(
            definition.kind,
            _value_renderer_wrapper(renderer),
            replace=True
        )
    return registry



__all__ = ["RuntimeValueBinding", "RuntimeValueMixin", "synchronize_runtime_value_renderers"]
