# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtGui
from ..core.runtime_registry import RuntimeRendererRegistry
from ..model.items import create_item
from ..pycompat import text_type


_INSTALL_MARKER = "_script_toolbox_runtime_registry_installed"
_LEGACY_BUILD = "_script_toolbox_legacy_build_runtime_widget"
_RUNTIME_MODULE = "_script_toolbox_runtime_module"
_ACTIVE_REGISTRY = None


def _runtime_module(owner):
    return getattr(
        owner.__class__,
        _RUNTIME_MODULE,
        None
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
    return owner._button_widget(item)


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

    return container


def _render_label(owner, item, compact=False):
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


def _render_integer(owner, item, compact=False):
    container, layout = owner._parameter_container(
        item,
        compact=compact
    )
    control = QtGui.QSpinBox()
    control.setRange(
        item["min"],
        item["max"]
    )
    control.setSingleStep(
        item["step"]
    )
    control.setValue(
        item["value"]
    )

    control.valueChanged.connect(
        lambda value, item_id=item["id"]:
        owner.toolbox.store_value(
            item_id,
            int(value)
        )
    )

    layout.addWidget(
        control,
        0
    )
    return container


def _render_float(owner, item, compact=False):
    container, layout = owner._parameter_container(
        item,
        compact=compact
    )
    control = QtGui.QDoubleSpinBox()
    control.setDecimals(
        item["decimals"]
    )
    control.setRange(
        item["min"],
        item["max"]
    )
    control.setSingleStep(
        item["step"]
    )
    control.setValue(
        item["value"]
    )

    control.valueChanged.connect(
        lambda value, item_id=item["id"]:
        owner.toolbox.store_value(
            item_id,
            float(value)
        )
    )

    layout.addWidget(
        control,
        0
    )
    return container


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
