# -*- coding: utf-8 -*-

import os


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


def _read(relative_path):
    path = os.path.join(
        ROOT,
        *relative_path.split("/")
    )
    with open(path, "r") as handle:
        return handle.read()


class _Widget(object):

    def __init__(self, children=None):
        self.children = list(children or [])
        self.signals_blocked = False
        self.emissions = 0
        self.callback = None

    def findChildren(self, control_class):
        result = []

        for child in self.children:
            if isinstance(child, control_class):
                result.append(child)
            result.extend(
                child.findChildren(control_class)
            )

        return result

    def blockSignals(self, blocked):
        previous = self.signals_blocked
        self.signals_blocked = bool(blocked)
        return previous

    def _emit(self):
        if self.signals_blocked:
            return

        self.emissions += 1
        if self.callback is not None:
            self.callback()


class _LineEdit(_Widget):

    def __init__(self, text=""):
        _Widget.__init__(self)
        self.text_value = text

    def setText(self, value):
        self.text_value = value
        self._emit()


class _SpinBox(_Widget):

    def __init__(self, value=0):
        _Widget.__init__(self)
        self.value = value

    def setValue(self, value):
        self.value = value
        self._emit()


class _DoubleSpinBox(_SpinBox):
    pass


class _CheckBox(_Widget):

    def __init__(self, checked=False):
        _Widget.__init__(self)
        self.checked = checked

    def setChecked(self, checked):
        self.checked = bool(checked)
        self._emit()


class _ComboBox(_Widget):

    def __init__(self, items, index=0):
        _Widget.__init__(self)
        self.items = list(items)
        self.index = index

    def findText(self, value):
        try:
            return self.items.index(value)
        except ValueError:
            return -1

    def setCurrentIndex(self, index):
        self.index = index
        self._emit()


class _Slider(_SpinBox):
    pass


class _PushButton(_Widget):
    pass


class _QtGui(object):
    QLineEdit = _LineEdit
    QSpinBox = _SpinBox
    QDoubleSpinBox = _DoubleSpinBox
    QCheckBox = _CheckBox
    QComboBox = _ComboBox
    QSlider = _Slider
    QPushButton = _PushButton


def _runtime_value_sync_namespace():
    source = _read(
        "scripts/script_toolbox/ui/runtime_value_sync.py"
    )
    source = source.replace(
        "from ..compat import QtGui\n",
        ""
    )
    source = source.replace(
        "from ..pycompat import text_type\n",
        ""
    )

    namespace = {
        "QtGui": _QtGui,
        "text_type": str,
        "__name__": "runtime_value_sync_test",
    }
    exec(
        compile(
            source,
            "runtime_value_sync.py",
            "exec"
        ),
        namespace
    )
    return namespace


class _Registry(object):

    def __init__(self):
        self.renderers = {}

    def renderer_for(self, kind):
        return self.renderers.get(kind)

    def register(self, kind, renderer, replace=False):
        if kind in self.renderers and not replace:
            raise ValueError(kind)
        self.renderers[kind] = renderer
        return renderer

    def render(self, kind, owner, item):
        return self.renderers[kind](
            owner,
            item,
            compact=False
        )


class _Toolbox(object):

    def __init__(self):
        self.items = {}
        self.store_calls = 0
        self.state_refresh_calls = 0
        self.rebuild_calls = 0
        self.field_refresh_calls = 0

    def find_item(self, key):
        for item in self.items.values():
            if key in (
                item.get("id"),
                item.get("name"),
                item.get("label"),
            ):
                return item
        return None

    def store_value(self, key, value):
        self.store_calls += 1
        item = self.find_item(key)
        if item is None:
            return False

        item["value"] = value
        self.state_refresh_calls += 1
        return True

    def rebuild(self):
        self.rebuild_calls += 1

    def refresh_field_widget(self, key):
        self.field_refresh_calls += 1


class _DebouncedToolbox(_Toolbox):

    def store_value(self, key, value):
        self.store_calls += 1
        item = self.find_item(key)
        if item is None:
            return False

        item["value"] = value
        self.state_refresh_calls += 1
        return True


class _Owner(object):

    def __init__(self, toolbox, roots=None):
        self.toolbox = toolbox
        self.roots = roots or {}
        self.color_updates = []

    def _color_button_style(self, control, value):
        self.color_updates.append((
            control,
            value
        ))
        control.color = value


def _install(namespace, registry):
    namespace["install_runtime_value_sync"](
        registry,
        _Toolbox,
        store_toolbox_classes=(
            _DebouncedToolbox,
        )
    )


def test_string_runtime_widget_updates_after_store_value_by_name_and_id():
    namespace = _runtime_value_sync_namespace()
    registry = _Registry()
    control = _LineEdit("")
    root = _Widget([control])

    registry.register(
        "string",
        lambda owner, item, compact=False: root
    )
    _install(namespace, registry)

    toolbox = _DebouncedToolbox()
    item = {
        "id": "string_node",
        "name": "houdini_selectable_template_node",
        "kind": "string",
        "value": "",
    }
    toolbox.items[item["id"]] = item
    owner = _Owner(toolbox)

    registry.render(
        "string",
        owner,
        item
    )

    assert toolbox.store_value(
        "houdini_selectable_template_node",
        "/obj/geo1/grid1"
    ) is True
    assert control.text_value == "/obj/geo1/grid1"

    assert toolbox.store_value(
        "string_node",
        "/obj/geo1/grid2"
    ) is True
    assert control.text_value == "/obj/geo1/grid2"
    assert toolbox.rebuild_calls == 0


def test_programmatic_sync_blocks_signals_and_does_not_store_recursively():
    namespace = _runtime_value_sync_namespace()
    registry = _Registry()
    spin = _SpinBox(1)
    root = _Widget([spin])

    registry.register(
        "integer",
        lambda owner, item, compact=False: root
    )
    _install(namespace, registry)

    toolbox = _DebouncedToolbox()
    item = {
        "id": "integer_samples",
        "name": "samples",
        "kind": "integer",
        "value": 1,
        "min": 0,
        "max": 100,
    }
    toolbox.items[item["id"]] = item
    owner = _Owner(toolbox)

    registry.render(
        "integer",
        owner,
        item
    )

    spin.callback = lambda: toolbox.store_value(
        "samples",
        spin.value
    )

    toolbox.store_value(
        "samples",
        12
    )

    assert spin.value == 12
    assert spin.emissions == 0
    assert toolbox.store_calls == 1
    assert spin.signals_blocked is False


def test_integer_float_checkbox_menu_and_color_sync():
    namespace = _runtime_value_sync_namespace()
    binding_class = namespace["RuntimeValueBinding"]
    toolbox = _Toolbox()
    owner = _Owner(toolbox)

    integer_spin = _SpinBox(0)
    integer_slider = _Slider(0)
    integer_root = _Widget([
        integer_spin,
        integer_slider,
    ])
    integer_binding = binding_class(
        "integer",
        integer_root,
        owner
    )
    assert integer_binding.sync({
        "kind": "integer",
        "value": 18,
        "min": 0,
        "max": 100,
    }) is True
    assert integer_spin.value == 18
    assert integer_slider.value == 18

    float_spin = _DoubleSpinBox(0.0)
    float_slider = _Slider(0)
    float_root = _Widget([
        float_spin,
        float_slider,
    ])
    float_binding = binding_class(
        "float",
        float_root,
        owner
    )
    assert float_binding.sync({
        "kind": "float",
        "value": 0.25,
        "min": 0.0,
        "max": 1.0,
    }) is True
    assert float_spin.value == 0.25
    assert float_slider.value == 2500

    checkbox = _CheckBox(False)
    checkbox_binding = binding_class(
        "checkbox",
        checkbox,
        owner
    )
    assert checkbox_binding.sync({
        "kind": "checkbox",
        "value": True,
    }) is True
    assert checkbox.checked is True

    menu = _ComboBox([
        "Draft",
        "Preview",
        "Final",
    ])
    menu_binding = binding_class(
        "menu",
        menu,
        owner
    )
    assert menu_binding.sync({
        "kind": "menu",
        "value": "Final",
    }) is True
    assert menu.index == 2

    color = _PushButton()
    color_binding = binding_class(
        "color",
        color,
        owner
    )
    value = [0.1, 0.2, 0.3]
    assert color_binding.sync({
        "kind": "color",
        "value": value,
    }) is True
    assert color.color == value


def test_original_store_side_effects_and_field_refresh_are_preserved():
    namespace = _runtime_value_sync_namespace()
    registry = _Registry()
    _install(namespace, registry)

    toolbox = _DebouncedToolbox()
    checkbox = _CheckBox(False)
    checkbox_item = {
        "id": "enabled_id",
        "name": "enabled",
        "kind": "checkbox",
        "value": False,
    }
    field_item = {
        "id": "nodes_id",
        "name": "nodes",
        "kind": "field",
        "value": [],
    }
    toolbox.items[checkbox_item["id"]] = checkbox_item
    toolbox.items[field_item["id"]] = field_item

    binding = namespace["RuntimeValueBinding"](
        "checkbox",
        checkbox,
        _Owner(toolbox)
    )
    toolbox.register_value_widget(
        checkbox_item["id"],
        binding
    )

    assert toolbox.store_value(
        "enabled",
        True
    ) is True
    assert checkbox.checked is True
    assert toolbox.state_refresh_calls == 1

    assert toolbox.store_value(
        "nodes",
        ["/obj/geo1"]
    ) is True
    assert toolbox.field_refresh_calls == 1
    assert toolbox.state_refresh_calls == 2


def test_base_and_debounced_store_overrides_are_wrapped_independently():
    namespace = _runtime_value_sync_namespace()
    registry = _Registry()
    _install(namespace, registry)

    marker = namespace["_TOOLBOX_INSTALL_MARKER"]

    assert _Toolbox.__dict__.get(marker) is True
    assert _DebouncedToolbox.__dict__.get(marker) is True
    assert _Toolbox.__dict__["store_value"] is not _DebouncedToolbox.__dict__["store_value"]


def test_ui_installs_sync_for_live_debounced_runtime_after_renderer_hooks():
    source = _read(
        "scripts/script_toolbox/ui/__init__.py"
    )

    value_sync = source.index(
        "install_runtime_value_sync("
    )
    event_hooks = source.index(
        "install_event_binding_hooks("
    )

    assert event_hooks < value_sync
    assert "_debounced_main_window_module._DebouncedScriptToolbox" in source
    assert "store_toolbox_classes=(" in source
