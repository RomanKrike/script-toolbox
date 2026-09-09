# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtGui
from ..pycompat import text_type


_VALUE_KINDS = (
    "string",
    "integer",
    "float",
    "checkbox",
    "toggle",
    "menu",
    "color",
)

_TOOLBOX_INSTALL_MARKER = "_script_toolbox_runtime_value_sync_installed"
_REBUILD_INSTALL_MARKER = "_script_toolbox_runtime_value_rebuild_installed"
_RENDERER_INSTALL_MARKER = "_script_toolbox_runtime_value_renderers_installed"


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
            control.blockSignals(
                was_blocked
            )
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


def _float_slider_position(
    value,
    minimum,
    maximum
):
    if maximum <= minimum:
        return 0

    ratio = (
        (float(value) - float(minimum)) /
        float(maximum - minimum)
    )
    return max(
        0,
        min(
            10000,
            int(round(ratio * 10000.0))
        )
    )


class RuntimeValueBinding(object):
    """Connect one document value item to its already-created Qt controls."""

    def __init__(
        self,
        kind,
        root,
        owner
    ):
        self.kind = text_type(
            kind or ""
        ).strip().lower()
        self.root = root
        self.owner = owner

    def _signal_controls(self):
        if self.kind == "string":
            return _controls(
                self.root,
                QtGui.QLineEdit
            )

        if self.kind in (
            "checkbox",
            "toggle",
        ):
            return _controls(
                self.root,
                QtGui.QCheckBox
            )

        if self.kind == "integer":
            return (
                _controls(
                    self.root,
                    QtGui.QSpinBox
                ) +
                _controls(
                    self.root,
                    QtGui.QSlider
                )
            )

        if self.kind == "float":
            return (
                _controls(
                    self.root,
                    QtGui.QDoubleSpinBox
                ) +
                _controls(
                    self.root,
                    QtGui.QSlider
                )
            )

        if self.kind == "menu":
            return _controls(
                self.root,
                QtGui.QComboBox
            )

        if self.kind == "color":
            return _controls(
                self.root,
                QtGui.QPushButton
            )

        return []

    def _sync_string(self, item):
        value = text_type(
            item.get("value", "") or ""
        )

        for control in _controls(
            self.root,
            QtGui.QLineEdit
        ):
            control.setText(value)

    def _sync_checkbox(self, item):
        value = bool(
            item.get("value", False)
        )

        for control in _controls(
            self.root,
            QtGui.QCheckBox
        ):
            control.setChecked(value)

    def _sync_integer(self, item):
        spins = _controls(
            self.root,
            QtGui.QSpinBox
        )
        values = _numeric_values(
            item.get("value", 0),
            len(spins)
        )

        for index, control in enumerate(spins):
            control.setValue(
                int(values[index])
            )

        sliders = _controls(
            self.root,
            QtGui.QSlider
        )

        for index, slider in enumerate(sliders):
            if index >= len(values):
                break
            slider.setValue(
                int(values[index])
            )

    def _sync_float(self, item):
        spins = _controls(
            self.root,
            QtGui.QDoubleSpinBox
        )
        values = _numeric_values(
            item.get("value", 0.0),
            len(spins)
        )

        for index, control in enumerate(spins):
            control.setValue(
                float(values[index])
            )

        sliders = _controls(
            self.root,
            QtGui.QSlider
        )
        minimum = float(
            item.get("min", 0.0)
        )
        maximum = float(
            item.get("max", 1.0)
        )

        for index, slider in enumerate(sliders):
            if index >= len(values):
                break
            slider.setValue(
                _float_slider_position(
                    values[index],
                    minimum,
                    maximum
                )
            )

    def _sync_menu(self, item):
        value = text_type(
            item.get("value", "") or ""
        )

        for control in _controls(
            self.root,
            QtGui.QComboBox
        ):
            index = control.findText(value)
            if index >= 0:
                control.setCurrentIndex(index)

    def _sync_color(self, item):
        styler = getattr(
            self.owner,
            "_color_button_style",
            None
        )

        if styler is None:
            return

        for control in _controls(
            self.root,
            QtGui.QPushButton
        ):
            styler(
                control,
                item.get("value")
            )

    def sync(self, item):
        syncer = {
            "string": self._sync_string,
            "integer": self._sync_integer,
            "float": self._sync_float,
            "checkbox": self._sync_checkbox,
            "toggle": self._sync_checkbox,
            "menu": self._sync_menu,
            "color": self._sync_color,
        }.get(self.kind)

        if syncer is None:
            return False

        previous = _block_signals(
            self._signal_controls()
        )
        try:
            syncer(item)
        finally:
            _restore_signals(previous)

        return True


def _register_value_widget(
    self,
    item_id,
    binding
):
    if not hasattr(
        self,
        "value_widgets"
    ):
        self.value_widgets = {}

    self.value_widgets[
        text_type(item_id)
    ] = binding
    return binding


def _sync_runtime_value(
    self,
    key
):
    item = self.find_item(key)

    if item is None:
        return False

    if item.get("kind") == "field":
        self.refresh_field_widget(
            item["id"]
        )
        return True

    value_widgets = getattr(
        self,
        "value_widgets",
        {}
    )
    binding = value_widgets.get(
        text_type(item["id"])
    )

    if binding is None:
        return False

    try:
        return bool(
            binding.sync(item)
        )
    except Exception:
        try:
            del value_widgets[
                text_type(item["id"])
            ]
        except Exception:
            pass
        return False


def _install_toolbox_methods(toolbox_class):
    if not hasattr(
        toolbox_class,
        "register_value_widget"
    ):
        toolbox_class.register_value_widget = _register_value_widget

    if not hasattr(
        toolbox_class,
        "sync_runtime_value"
    ):
        toolbox_class.sync_runtime_value = _sync_runtime_value


def _install_store_wrapper(toolbox_class):
    if toolbox_class.__dict__.get(
        _TOOLBOX_INSTALL_MARKER,
        False
    ):
        return

    original_store_value = toolbox_class.store_value

    def store_value_with_runtime_sync(
        self,
        key,
        value
    ):
        result = original_store_value(
            self,
            key,
            value
        )

        if result:
            self.sync_runtime_value(key)

        return result

    toolbox_class.store_value = store_value_with_runtime_sync
    setattr(
        toolbox_class,
        _TOOLBOX_INSTALL_MARKER,
        True
    )


def _install_rebuild_wrapper(toolbox_class):
    if toolbox_class.__dict__.get(
        _REBUILD_INSTALL_MARKER,
        False
    ):
        return

    original_rebuild = toolbox_class.rebuild

    def rebuild_with_value_registry(self):
        self.value_widgets = {}
        return original_rebuild(self)

    toolbox_class.rebuild = rebuild_with_value_registry
    setattr(
        toolbox_class,
        _REBUILD_INSTALL_MARKER,
        True
    )


def _value_renderer_wrapper(
    kind,
    renderer
):
    def render_with_value_registration(
        owner,
        item,
        compact=False
    ):
        root = renderer(
            owner,
            item,
            compact=compact
        )

        if root is not None:
            binding = RuntimeValueBinding(
                kind,
                root,
                owner
            )
            owner.toolbox.register_value_widget(
                item["id"],
                binding
            )

        return root

    return render_with_value_registration


def _install_renderer_wrappers(registry):
    if getattr(
        registry,
        _RENDERER_INSTALL_MARKER,
        False
    ):
        return

    for kind in _VALUE_KINDS:
        renderer = registry.renderer_for(kind)
        if renderer is None:
            continue

        registry.register(
            kind,
            _value_renderer_wrapper(
                kind,
                renderer
            ),
            replace=True
        )

    setattr(
        registry,
        _RENDERER_INSTALL_MARKER,
        True
    )


def install_runtime_value_sync(
    registry,
    base_toolbox_class,
    store_toolbox_classes=None
):
    """Install runtime value registration and post-store synchronization."""
    _install_toolbox_methods(
        base_toolbox_class
    )
    _install_rebuild_wrapper(
        base_toolbox_class
    )
    _install_renderer_wrappers(
        registry
    )

    classes = [
        base_toolbox_class
    ]

    for toolbox_class in store_toolbox_classes or ():
        if toolbox_class not in classes:
            classes.append(toolbox_class)
        _install_toolbox_methods(
            toolbox_class
        )

    for toolbox_class in classes:
        _install_store_wrapper(
            toolbox_class
        )

    return registry


__all__ = [
    "RuntimeValueBinding",
    "install_runtime_value_sync",
]
