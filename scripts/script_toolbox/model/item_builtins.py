# -*- coding: utf-8 -*-
from __future__ import print_function

from ..pycompat import text_type
from .fields import AnyField
from .fields import BoolField
from .fields import ChoiceField
from .fields import ColorField
from .fields import FloatField
from .fields import IntField
from .fields import ListField
from .fields import PathField
from .fields import TextField
from .item_registry import ITEM_TYPES
from .item_registry import ItemTypeDefinition


_COMPONENT_LABELS = ("X", "Y", "Z", "W")


def _default_click_script():
    return [{"event": "click", "handler": "script"}]


def _default_click_toggle():
    return [{"event": "click", "handler": "state_toggle"}]


def _normalize_toggle(props, raw):
    if props.get("state_source") != "internal":
        props.pop("value", None)
    return props


def _normalize_menu(props, raw):
    values = props.get("items") or []
    values = [text_type(value) for value in values if text_type(value).strip()]
    if not values:
        values = ["Option 1", "Option 2"]
    props["items"] = values
    if props.get("value") not in values:
        props["value"] = values[0]
    return props


def _normalize_numeric(props, raw, is_float=False):
    minimum = props.get("min")
    maximum = props.get("max")
    if minimum > maximum:
        minimum, maximum = maximum, minimum
    props["min"] = minimum
    props["max"] = maximum

    size = max(1, min(4, int(props.get("size", 1))))
    props["size"] = size

    labels = props.get("component_labels") or []
    labels = [text_type(value).strip() for value in labels]
    props["component_labels"] = [
        labels[index] if index < len(labels) and labels[index]
        else _COMPONENT_LABELS[index]
        for index in range(size)
    ]

    value = raw.get("value", props.get("value", 0.0 if is_float else 0))
    incoming = list(value) if isinstance(value, (list, tuple)) else [value] * size
    result = []
    for index in range(size):
        current = incoming[index] if index < len(incoming) else 0
        try:
            current = float(current) if is_float else int(current)
        except Exception:
            current = 0.0 if is_float else 0
        current = max(minimum, min(maximum, current))
        result.append(current)
    props["value"] = result[0] if size == 1 else result
    return props


def _normalize_integer(props, raw):
    props["step"] = max(1, int(props.get("step", 1)))
    return _normalize_numeric(props, raw, is_float=False)


def _normalize_float(props, raw):
    props["step"] = max(0.000001, float(props.get("step", 0.1)))
    return _normalize_numeric(props, raw, is_float=True)


def _normalize_field(props, raw):
    value = raw.get("value", props.get("value", ""))
    if isinstance(value, tuple):
        value = list(value)
    multiple = bool(props.get("multiple", True))
    if not multiple and isinstance(value, list):
        value = value[0] if value else ""
    props["value"] = value
    if not multiple:
        props["display_mode"] = "single"
    return props


def _definition(kind, title, category, order, fields=None, events=None,
                internal_events=None, capabilities=None, creatable=True,
                default_label=None, normalize_props=None,
                default_bindings=None, description=""):
    return ItemTypeDefinition(
        kind=kind,
        title=title,
        category=category,
        description=description,
        order=order,
        fields=fields,
        events=events,
        internal_events=internal_events,
        capabilities=capabilities,
        creatable=creatable,
        default_label=default_label,
        normalize_props=normalize_props,
        default_bindings=default_bindings,
    )


def builtin_item_definitions():
    mouse = ("click", "double_click")
    value_events = ("value_changed", "editing_finished", "click", "double_click")
    return (
        _definition(
            "folder", "Folder", "Layout", 10,
            fields={
                "folder_type": ChoiceField(
                    ("collapsible", "simple", "tabs", "radio"),
                    default="collapsible"
                ),
                "collapsed": BoolField(default=False),
            },
            internal_events=("opened", "closed"),
            capabilities=("container",),
            default_label="Folder",
        ),
        _definition(
            "row", "Row", "Layout", 20,
            fields={
                "spacing": IntField(default=4, minimum=0, maximum=30),
                "equal_widths": BoolField(default=False),
                "horizontal_distribution": ChoiceField(
                    ("left", "center", "right", "space_between"),
                    default="left"
                ),
                "vertical_alignment": ChoiceField(
                    ("top", "center", "bottom"), default="center"
                ),
            },
            capabilities=("container", "layout"),
            default_label="Row",
        ),
        _definition(
            "column", "Column", "Layout", 30,
            fields={
                "spacing": IntField(default=4, minimum=0, maximum=30),
                "horizontal_alignment": ChoiceField(
                    ("stretch", "left", "center", "right"),
                    default="stretch"
                ),
                "vertical_distribution": ChoiceField(
                    ("top", "center", "bottom", "space_between"),
                    default="top"
                ),
            },
            capabilities=("container", "layout"),
            default_label="Column",
        ),
        _definition(
            "button", "Button", "Controls", 10,
            fields={
                "color": ColorField(default=[0.25, 0.25, 0.25]),
                "icon_path": PathField(default=""),
                "icon_size": IntField(default=18, minimum=8, maximum=256),
                "icon_only": BoolField(default=False),
            },
            events=mouse,
            capabilities=("bindable",),
            default_label="New Button",
            default_bindings=_default_click_script,
        ),
        _definition(
            "toggle_button", "Toggle Button", "Controls", 20,
            fields={
                "state_source": ChoiceField(("internal", "script"), default="internal"),
                "icon_path": PathField(default=""),
                "icon_size": IntField(default=18, minimum=8, maximum=256),
                "icon_only": BoolField(default=False),
                "state_get_script": TextField(default=""),
                "state_get_language": ChoiceField(("python", "mel"), default="python"),
                "state_on_script": TextField(default=""),
                "state_on_language": ChoiceField(("python", "mel"), default="python"),
                "state_off_script": TextField(default=""),
                "state_off_language": ChoiceField(("python", "mel"), default="python"),
                "state_on_label": TextField(default="Toggle"),
                "state_off_label": TextField(default="Toggle"),
                "state_on_color": ColorField(default=[0.22, 0.42, 0.26]),
                "state_off_color": ColorField(default=[0.30, 0.30, 0.30]),
                "value": BoolField(default=False),
            },
            events=mouse,
            capabilities=("bindable", "has_value", "state_toggle"),
            default_label="New Toggle Button",
            normalize_props=_normalize_toggle,
            default_bindings=_default_click_toggle,
        ),
        _definition(
            "icon", "Icon", "Display", 10,
            fields={
                "path": PathField(default=""),
                "width": IntField(default=24, minimum=8, maximum=512),
                "height": IntField(default=24, minimum=8, maximum=512),
                "content_alignment": ChoiceField(
                    ("left", "center", "right"), default="left"
                ),
            },
            events=mouse,
            capabilities=("bindable", "resizable"),
            default_label="Icon",
        ),
        _definition(
            "toggle_icon", "Toggle Icon", "Controls", 30,
            fields={
                "state_source": ChoiceField(("internal", "script"), default="internal"),
                "state_on_path": PathField(default=""),
                "state_off_path": PathField(default=""),
                "width": IntField(default=24, minimum=8, maximum=512),
                "height": IntField(default=24, minimum=8, maximum=512),
                "content_alignment": ChoiceField(
                    ("left", "center", "right"), default="left"
                ),
                "state_get_script": TextField(default=""),
                "state_get_language": ChoiceField(("python", "mel"), default="python"),
                "state_on_script": TextField(default=""),
                "state_on_language": ChoiceField(("python", "mel"), default="python"),
                "state_off_script": TextField(default=""),
                "state_off_language": ChoiceField(("python", "mel"), default="python"),
                "value": BoolField(default=False),
            },
            events=mouse,
            capabilities=("bindable", "has_value", "state_toggle", "resizable"),
            default_label="Toggle Icon",
            normalize_props=_normalize_toggle,
            default_bindings=_default_click_toggle,
        ),
        _definition(
            "string", "String", "Controls", 40,
            fields={"value": TextField(default="")},
            events=value_events,
            capabilities=("bindable", "has_value", "supports_compact"),
            default_label="String",
        ),
        _definition(
            "integer", "Integer", "Controls", 50,
            fields={
                "value": AnyField(default=0),
                "min": IntField(default=-1000000),
                "max": IntField(default=1000000),
                "step": IntField(default=1, minimum=1),
                "size": IntField(default=1, minimum=1, maximum=4),
                "component_labels": ListField(default=[]),
                "show_slider": BoolField(default=False),
            },
            events=value_events,
            capabilities=("bindable", "has_value", "supports_compact"),
            default_label="Integer",
            normalize_props=_normalize_integer,
        ),
        _definition(
            "float", "Float", "Controls", 60,
            fields={
                "value": AnyField(default=0.0),
                "min": FloatField(default=-1000000.0),
                "max": FloatField(default=1000000.0),
                "step": FloatField(default=0.1, minimum=0.000001),
                "decimals": IntField(default=3, minimum=0, maximum=8),
                "size": IntField(default=1, minimum=1, maximum=4),
                "component_labels": ListField(default=[]),
                "show_slider": BoolField(default=False),
            },
            events=value_events,
            capabilities=("bindable", "has_value", "supports_compact"),
            default_label="Float",
            normalize_props=_normalize_float,
        ),
        _definition(
            "checkbox", "Checkbox", "Controls", 70,
            fields={
                "value": BoolField(default=False),
                "label_position": ChoiceField(("left", "right"), default="right"),
            },
            events=("value_changed", "click", "double_click"),
            capabilities=("bindable", "has_value", "supports_compact"),
            default_label="Checkbox",
        ),
        _definition(
            "menu", "Menu", "Controls", 80,
            fields={
                "items": ListField(default=["Option 1", "Option 2"], item_field=TextField()),
                "value": TextField(default=""),
            },
            events=("value_changed", "click", "double_click"),
            capabilities=("bindable", "has_value", "supports_compact"),
            default_label="Menu",
            normalize_props=_normalize_menu,
        ),
        _definition(
            "color", "Color", "Controls", 90,
            fields={"value": ColorField(default=[0.25, 0.25, 0.25])},
            events=("value_changed", "click", "double_click"),
            capabilities=("bindable", "has_value", "supports_compact"),
            default_label="Color",
        ),
        _definition(
            "field", "Field", "Controls", 100,
            fields={
                "source": ChoiceField(("value", "selection"), default="value"),
                "value": AnyField(default=""),
                "placeholder": TextField(default=""),
                "selectable": BoolField(default=True),
                "select_scene": BoolField(default=False),
                "multiple": BoolField(default=True),
                "long_names": BoolField(default=False),
                "display_mode": ChoiceField(("single", "list"), default="list"),
                "visible_rows": IntField(default=4, minimum=1, maximum=20),
            },
            events=("value_changed", "selection_changed", "click", "double_click"),
            capabilities=("bindable", "has_value", "supports_compact"),
            default_label="Field",
            normalize_props=_normalize_field,
        ),
        _definition(
            "label", "Label", "Display", 20,
            fields={},
            events=mouse,
            capabilities=("bindable",),
            default_label="Label",
        ),
        _definition(
            "text", "Text", "Display", 30,
            fields={"text": TextField(default="Text")},
            capabilities=(),
            default_label="Text",
        ),
        _definition(
            "separator", "Separator", "Display", 40,
            fields={},
            capabilities=(),
            default_label="Separator",
        ),
        _definition(
            "image", "Image", "Display", 50,
            fields={
                "source": PathField(default=""),
                "fit": ChoiceField(("contain", "cover", "stretch"), default="contain"),
                "width": IntField(default=200, minimum=8, maximum=4096),
                "height": IntField(default=120, minimum=8, maximum=4096),
            },
            events=mouse,
            capabilities=("bindable", "resizable"),
            default_label="Image",
            description="Display an image from a local file path.",
        ),
    )


def register_builtin_items(registry=None):
    registry = registry or ITEM_TYPES
    for definition in builtin_item_definitions():
        if registry.get(definition.kind) is None:
            registry.register(definition)
    return registry


__all__ = [
    "builtin_item_definitions",
    "register_builtin_items",
]
