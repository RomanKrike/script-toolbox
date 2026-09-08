# -*- coding: utf-8 -*-
from __future__ import print_function

import os

from ..compat import QtCore
from ..compat import QtGui
from ..core.runtime_registry import RuntimeRendererRegistry
from ..model.callbacks import has_callback
from ..model.items import create_item
from ..model.items import safe_component_labels
from ..model.items import safe_numeric_size
from ..pycompat import text_type


_INSTALL_MARKER = "_script_toolbox_runtime_registry_installed"
_LEGACY_BUILD = "_script_toolbox_legacy_build_runtime_widget"
_LEGACY_TOGGLE = "_script_toolbox_legacy_toggle"
_LEGACY_FIELD_DOUBLE_CLICK = "_script_toolbox_legacy_field_double_click"
_RUNTIME_MODULE = "_script_toolbox_runtime_module"
_ACTIVE_REGISTRY = None


def _runtime_module(owner):
    return getattr(
        owner.__class__,
        _RUNTIME_MODULE,
        None
    )


def _expanded_path(value):
    return os.path.expanduser(
        os.path.expandvars(
            text_type(value or "")
        )
    )


def _invoke_callback(
    toolbox,
    item,
    event,
    value=None,
    old_value=None
):
    callback = getattr(
        toolbox,
        "run_item_callback",
        None
    )
    if callback is None:
        return None
    return callback(
        item,
        event,
        value=value,
        old_value=old_value
    )


def _render_folder(owner, item, compact=False):
    runtime_module = _runtime_module(owner)
    if runtime_module is None:
        return None

    return runtime_module.RuntimeFolder(
        owner.toolbox,
        item,
        owner.content
    )


def _render_row(owner, item, compact=False):
    return owner._row_widget(item)


def _render_button(owner, item, compact=False):
    button = owner._button_widget(item)
    icon_path = _expanded_path(
        item.get("icon_path")
    )
    icon_size = int(
        item.get("icon_size", 18)
    )

    if icon_path:
        button.setIcon(
            QtGui.QIcon(icon_path)
        )
        button.setIconSize(
            QtCore.QSize(
                icon_size,
                icon_size
            )
        )

    if item.get("icon_only", False):
        button.setText("")

    button.clicked.connect(
        lambda checked=False, current=item:
        _invoke_callback(
            owner.toolbox,
            current,
            "on_click"
        )
    )
    return button


def _render_icon(owner, item, compact=False):
    width = int(item.get("width", 24))
    height = int(item.get("height", 24))
    path = _expanded_path(item.get("path"))
    clickable = bool(item.get("clickable", False))

    if clickable:
        icon_widget = QtGui.QToolButton()
        icon_widget.setAutoRaise(True)
        icon_widget.setFixedSize(width, height)
        icon_widget.setIconSize(
            QtCore.QSize(width, height)
        )
        if path:
            icon_widget.setIcon(
                QtGui.QIcon(path)
            )
        else:
            icon_widget.setText("?")
        icon_widget.clicked.connect(
            lambda checked=False, current=item:
            _invoke_callback(
                owner.toolbox,
                current,
                "on_click"
            )
        )
    else:
        icon_widget = QtGui.QLabel()
        icon_widget.setFixedSize(width, height)
        icon_widget.setAlignment(
            QtCore.Qt.AlignCenter
        )
        pixmap = QtGui.QPixmap(path) if path else QtGui.QPixmap()
        if not pixmap.isNull():
            icon_widget.setPixmap(
                pixmap.scaled(
                    width,
                    height,
                    QtCore.Qt.KeepAspectRatio,
                    QtCore.Qt.SmoothTransformation
                )
            )
        else:
            icon_widget.setText("?")

    icon_widget.setToolTip(
        item.get("tooltip", "")
    )

    container = QtGui.QWidget()
    layout = QtGui.QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    alignment = item.get("alignment", "left")

    if alignment in ("center", "right"):
        layout.addStretch(1)
    layout.addWidget(icon_widget, 0, QtCore.Qt.AlignVCenter)
    if alignment == "center":
        layout.addStretch(1)

    return container


def _render_toggle(owner, item, compact=False):
    legacy = create_item(
        "toggle",
        item
    )
    return owner._checkbox_widget(
        legacy,
        compact=compact
    )


def _render_checkbox(owner, item, compact=False):
    return owner._checkbox_widget(
        item,
        compact=compact
    )


def _field_selection_changed(toolbox, item, control):
    value = control.selected_values()
    old_value = getattr(
        control,
        "_script_toolbox_callback_selection",
        []
    )
    if old_value == value:
        return
    control._script_toolbox_callback_selection = list(value)
    _invoke_callback(
        toolbox,
        item,
        "on_select",
        value=value,
        old_value=old_value
    )


def _field_double_clicked(toolbox, item, control):
    values = control.selected_values()
    _invoke_callback(
        toolbox,
        item,
        "on_double_click",
        value=values,
        old_value=None
    )


def _render_field(owner, item, compact=False):
    runtime_module = _runtime_module(owner)
    if runtime_module is None:
        return None

    container, layout = owner._parameter_container(
        item,
        compact=compact
    )

    list_mode = (
        item.get("display_mode") == "list" and
        bool(item.get("multiple", True))
    )
    control_class = (
        runtime_module.DisplayFieldList
        if list_mode
        else runtime_module.DisplayField
    )
    control = control_class(
        owner.toolbox,
        item,
        container
    )

    if compact:
        control.setMinimumWidth(100)

    layout.addWidget(
        control,
        1
    )

    owner.toolbox.register_field_widget(
        item["id"],
        control
    )

    if list_mode:
        control._script_toolbox_callback_selection = list(
            control.selected_values()
        )
        control.itemSelectionChanged.connect(
            lambda current=item, widget=control:
            _field_selection_changed(
                owner.toolbox,
                current,
                widget
            )
        )
        control.itemDoubleClicked.connect(
            lambda entry, current=item, widget=control:
            _field_double_clicked(
                owner.toolbox,
                current,
                widget
            )
        )

    return container


def _render_label(owner, item, compact=False):
    if has_callback(item, "on_click"):
        label = QtGui.QToolButton()
        label.setAutoRaise(True)
        label.setText(
            owner._label(item)
        )
        label.clicked.connect(
            lambda checked=False, current=item:
            _invoke_callback(
                owner.toolbox,
                current,
                "on_click"
            )
        )
    else:
        label = QtGui.QLabel(
            owner._label(item)
        )

    label.setToolTip(
        owner._tooltip(item)
    )
    label.setStyleSheet(
        "color:#bdbdbd; padding:2px 3px;"
    )
    return label


def _render_separator(owner, item, compact=False):
    return owner._separator_widget(
        compact=compact
    )


def _render_string(owner, item, compact=False):
    container, layout = owner._parameter_container(
        item,
        compact=compact
    )
    control = QtGui.QLineEdit(
        text_type(
            item.get(
                "value",
                ""
            )
        )
    )

    if compact:
        control.setMinimumWidth(80)

    control.editingFinished.connect(
        lambda item_id=item["id"], widget=control:
        owner.toolbox.store_value(
            item_id,
            text_type(widget.text())
        )
    )

    layout.addWidget(
        control,
        1
    )
    return container


def _numeric_values(item, size):
    value = item.get("value", 0)
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
    ratio = (float(value) - minimum) / float(maximum - minimum)
    return max(0, min(10000, int(round(ratio * 10000.0))))


def _float_slider_value(position, minimum, maximum):
    if maximum <= minimum:
        return minimum
    return minimum + (
        (float(position) / 10000.0) *
        (maximum - minimum)
    )


def _render_numeric(owner, item, compact=False, is_float=False):
    container, layout = owner._parameter_container(
        item,
        compact=compact
    )
    size = safe_numeric_size(
        item.get("size", 1)
    )
    values = _numeric_values(item, size)
    labels = safe_component_labels(
        item.get("component_labels"),
        size
    )
    show_slider = bool(
        item.get("show_slider", False)
    )
    minimum = item["min"]
    maximum = item["max"]

    control_root = QtGui.QWidget()
    if show_slider and size > 1:
        control_layout = QtGui.QVBoxLayout(control_root)
    else:
        control_layout = QtGui.QHBoxLayout(control_root)
    control_layout.setContentsMargins(0, 0, 0, 0)
    control_layout.setSpacing(4)

    spins = []
    sliders = []

    for index in range(size):
        target_layout = control_layout
        if show_slider and size > 1:
            line = QtGui.QWidget()
            line_layout = QtGui.QHBoxLayout(line)
            line_layout.setContentsMargins(0, 0, 0, 0)
            line_layout.setSpacing(4)
            control_layout.addWidget(line)
            target_layout = line_layout

        if size > 1:
            component_label = QtGui.QLabel(
                labels[index]
            )
            component_label.setMinimumWidth(14)
            target_layout.addWidget(component_label)

        if is_float:
            spin = QtGui.QDoubleSpinBox()
            spin.setDecimals(item["decimals"])
            spin.setRange(minimum, maximum)
            spin.setSingleStep(item["step"])
            spin.setValue(float(values[index]))
        else:
            spin = QtGui.QSpinBox()
            spin.setRange(minimum, maximum)
            spin.setSingleStep(item["step"])
            spin.setValue(int(values[index]))

        spins.append(spin)
        target_layout.addWidget(spin, 0)

        slider = None
        if show_slider:
            slider = QtGui.QSlider(QtCore.Qt.Horizontal)
            if is_float:
                slider.setRange(0, 10000)
                slider.setValue(
                    _float_slider_position(
                        values[index],
                        minimum,
                        maximum
                    )
                )
            else:
                slider.setRange(int(minimum), int(maximum))
                slider.setSingleStep(int(item["step"]))
                slider.setValue(int(values[index]))
            target_layout.addWidget(slider, 1)
        sliders.append(slider)

    def store_current():
        result = []
        for spin in spins:
            result.append(
                float(spin.value())
                if is_float
                else int(spin.value())
            )
        owner.toolbox.store_value(
            item["id"],
            result[0] if size == 1 else result
        )

    for index, spin in enumerate(spins):
        slider = sliders[index]

        def spin_changed(
            value,
            current_slider=slider
        ):
            if current_slider is not None:
                current_slider.blockSignals(True)
                try:
                    if is_float:
                        current_slider.setValue(
                            _float_slider_position(
                                value,
                                minimum,
                                maximum
                            )
                        )
                    else:
                        current_slider.setValue(int(value))
                finally:
                    current_slider.blockSignals(False)
            store_current()

        spin.valueChanged.connect(spin_changed)

        if slider is not None:
            def slider_changed(
                position,
                current_spin=spin
            ):
                if is_float:
                    current_spin.setValue(
                        _float_slider_value(
                            position,
                            minimum,
                            maximum
                        )
                    )
                else:
                    current_spin.setValue(int(position))

            slider.valueChanged.connect(slider_changed)

    if compact:
        control_root.setMinimumWidth(100)

    layout.addWidget(
        control_root,
        1 if show_slider or size > 1 else 0
    )
    return container


def _render_integer(owner, item, compact=False):
    return _render_numeric(
        owner,
        item,
        compact=compact,
        is_float=False
    )


def _render_float(owner, item, compact=False):
    return _render_numeric(
        owner,
        item,
        compact=compact,
        is_float=True
    )


def _render_menu(owner, item, compact=False):
    container, layout = owner._parameter_container(
        item,
        compact=compact
    )
    control = QtGui.QComboBox()
    control.addItems(
        item["items"]
    )

    index = control.findText(
        item["value"]
    )
    if index >= 0:
        control.setCurrentIndex(index)

    control.currentIndexChanged.connect(
        lambda index, item_id=item["id"], widget=control:
        owner.toolbox.store_value(
            item_id,
            text_type(
                widget.itemText(index)
            )
        )
    )

    layout.addWidget(
        control,
        1
    )
    return container


def _render_color(owner, item, compact=False):
    container, layout = owner._parameter_container(
        item,
        compact=compact
    )
    control = QtGui.QPushButton(
        "..." if compact else "Choose..."
    )

    owner._color_button_style(
        control,
        item["value"]
    )
    control.clicked.connect(
        lambda checked=False, item_id=item["id"], widget=control:
        owner._choose_runtime_color(
            item_id,
            widget
        )
    )

    layout.addWidget(
        control,
        0
    )
    return container


def build_default_runtime_renderer_registry():
    registry = RuntimeRendererRegistry()

    entries = (
        ("folder", _render_folder),
        ("row", _render_row),
        ("button", _render_button),
        ("icon", _render_icon),
        ("toggle", _render_toggle),
        ("checkbox", _render_checkbox),
        ("field", _render_field),
        ("label", _render_label),
        ("separator", _render_separator),
        ("string", _render_string),
        ("integer", _render_integer),
        ("float", _render_float),
        ("menu", _render_menu),
        ("color", _render_color),
    )

    for kind, renderer in entries:
        registry.register(
            kind,
            renderer
        )

    return registry


def _registry_build_runtime_widget(
    self,
    item,
    compact=False
):
    registry = getattr(
        self.__class__,
        "runtime_renderer_registry",
        None
    )

    if registry is None:
        return None

    return registry.render(
        self,
        item,
        compact=compact
    )


def _install_callback_hooks(runtime_module):
    folder_class = runtime_module.RuntimeFolder
    if not hasattr(folder_class, _LEGACY_TOGGLE):
        setattr(
            folder_class,
            _LEGACY_TOGGLE,
            folder_class.toggle
        )

        def callback_toggle(self):
            old_collapsed = bool(
                self.section.get("collapsed", False)
            )
            result = getattr(
                self.__class__,
                _LEGACY_TOGGLE
            )(self)
            new_collapsed = bool(
                self.section.get("collapsed", False)
            )
            if old_collapsed != new_collapsed:
                _invoke_callback(
                    self.toolbox,
                    self.section,
                    "on_close" if new_collapsed else "on_open",
                    value=not new_collapsed,
                    old_value=not old_collapsed
                )
            return result

        folder_class.toggle = callback_toggle

    field_class = runtime_module.DisplayField
    if not hasattr(field_class, _LEGACY_FIELD_DOUBLE_CLICK):
        setattr(
            field_class,
            _LEGACY_FIELD_DOUBLE_CLICK,
            field_class.mouseDoubleClickEvent
        )

        def callback_double_click(self, event):
            result = getattr(
                self.__class__,
                _LEGACY_FIELD_DOUBLE_CLICK
            )(self, event)
            item = self.toolbox.find_item(
                self.item_id
            )
            if item is not None:
                _invoke_callback(
                    self.toolbox,
                    item,
                    "on_double_click",
                    value=self.selected_values(),
                    old_value=None
                )
            return result

        field_class.mouseDoubleClickEvent = callback_double_click


def install_runtime_renderer_registry(runtime_module):
    """Route active RuntimeFolder rendering through the registry."""
    global _ACTIVE_REGISTRY

    folder_class = runtime_module.RuntimeFolder

    if not hasattr(folder_class, _LEGACY_BUILD):
        setattr(
            folder_class,
            _LEGACY_BUILD,
            folder_class.build_runtime_widget
        )

    registry = build_default_runtime_renderer_registry()

    setattr(
        folder_class,
        _RUNTIME_MODULE,
        runtime_module
    )
    setattr(
        folder_class,
        "runtime_renderer_registry",
        registry
    )
    setattr(
        folder_class,
        "build_runtime_widget",
        _registry_build_runtime_widget
    )
    setattr(
        folder_class,
        _INSTALL_MARKER,
        True
    )

    _install_callback_hooks(
        runtime_module
    )

    _ACTIVE_REGISTRY = registry
    return registry


def get_runtime_renderer_registry():
    return _ACTIVE_REGISTRY


def register_runtime_renderer(
    kind,
    renderer,
    replace=False
):
    if _ACTIVE_REGISTRY is None:
        raise RuntimeError(
            "Runtime renderer registry is not installed."
        )

    return _ACTIVE_REGISTRY.register(
        kind,
        renderer,
        replace=replace
    )


def unregister_runtime_renderer(kind):
    if _ACTIVE_REGISTRY is None:
        return None

    return _ACTIVE_REGISTRY.unregister(kind)


__all__ = [
    "build_default_runtime_renderer_registry",
    "get_runtime_renderer_registry",
    "install_runtime_renderer_registry",
    "register_runtime_renderer",
    "unregister_runtime_renderer",
]
