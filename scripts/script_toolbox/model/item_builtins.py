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
from .item_definitions import builtin_extension_definitions
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
    multiple = bool(props.get("multiple", True))

    if value is None:
        value = ""
    elif isinstance(value, (list, tuple)):
        value = [text_type(entry) for entry in value]
    else:
        value = text_type(value)

    if not multiple and isinstance(value, list):
        value = value[0] if value else ""

    props["value"] = value
    if not multiple:
        props["display_mode"] = "single"
    return props


def _definition(
    kind,
    title,
    category,
    order,
    fields=None,
    events=None,
    internal_events=None,
    capabilities=None,
    creatable=True,
    default_label=None,
    ui_defaults=None,
    normalize_props=None,
    default_bindings=None,
    description="",
    renderer_path=None,
    inspector_path=None
):
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
        ui_defaults=ui_defaults,
        normalize_props=normalize_props,
        default_bindings=default_bindings,
        renderer_path=renderer_path,
        inspector_path=inspector_path,
    )


def _standard_item_definitions():
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
            capabilities=("container", "section"),
            default_label="Folder",
            description="Container: Collapsible, Simple, Tabs or Radio.",
            renderer_path=".runtime_renderers:_render_folder",
            inspector_path=".properties.folder:FolderPropertyEditor",
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
            description="Horizontal layout for compact controls and buttons.",
            renderer_path=".row_layout:render_row",
            inspector_path=".properties.row:RowPropertyEditor",
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
            ui_defaults={"width_mode": "stretch"},
            description="Vertical layout for stacking controls, Rows and Columns.",
            renderer_path=".column_layout:render_column",
            inspector_path=".properties.column:ColumnPropertyEditor",
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
            capabilities=("bindable", "native_button"),
            default_label="New Button",
            default_bindings=_default_click_script,
            description="Run Python or the active host native script language.",
            renderer_path=".runtime_renderers:_render_button",
            inspector_path=".properties.button:ButtonPropertyEditor",
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
            capabilities=("bindable", "has_value", "state_toggle", "native_button"),
            default_label="New Toggle Button",
            normalize_props=_normalize_toggle,
            default_bindings=_default_click_toggle,
            description="Stateful ON/OFF action with internal or scripted state.",
            renderer_path=".toggle_button_runtime:render_toggle_button",
            inspector_path=".properties.toggle_button:ToggleButtonPropertyEditor",
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
            ui_defaults={"show_label": False},
            description="Standalone icon with optional event bindings.",
            renderer_path=".runtime_renderers:_render_icon",
            inspector_path=".properties.icon:IconPropertyEditor",
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
            ui_defaults={"show_label": False},
            normalize_props=_normalize_toggle,
            default_bindings=_default_click_toggle,
            description="Stateful ON/OFF icon with independent images and actions.",
            renderer_path=".toggle_icon_runtime:render_toggle_icon",
            inspector_path=".properties.toggle_icon:ToggleIconPropertyEditor",
        ),
        _definition(
            "string", "String", "Controls", 40,
            fields={"value": TextField(default="")},
            events=value_events,
            capabilities=("bindable", "has_value", "supports_compact"),
            default_label="String",
            description="Editable text value.",
            renderer_path=".runtime_renderers:_render_string",
            inspector_path=".properties.basic:StringPropertyEditor",
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
            description="Integer value with min, max and step.",
            renderer_path=".runtime_renderers:_render_integer",
            inspector_path=".properties.basic:IntegerPropertyEditor",
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
            description="Floating-point value with range and precision.",
            renderer_path=".runtime_renderers:_render_float",
            inspector_path=".properties.basic:FloatPropertyEditor",
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
            description="Boolean on/off value.",
            renderer_path=".runtime_renderers:_render_checkbox",
            inspector_path=".properties.basic:CheckboxPropertyEditor",
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
            description="Choose one value from a list.",
            renderer_path=".runtime_renderers:_render_menu",
            inspector_path=".properties.basic:MenuPropertyEditor",
        ),
        _definition(
            "color", "Color", "Controls", 90,
            fields={"value": ColorField(default=[0.25, 0.25, 0.25])},
            events=("value_changed", "click", "double_click"),
            capabilities=("bindable", "has_value", "supports_compact"),
            default_label="Color",
            description="RGB color value.",
            renderer_path=".runtime_renderers:_render_color",
            inspector_path=".properties.basic:ColorPropertyEditor",
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
            capabilities=(
                "bindable",
                "has_value",
                "supports_compact",
                "field_widget",
            ),
            default_label="Field",
            normalize_props=_normalize_field,
            description="Manual value or live DCC selection.",
            renderer_path=".runtime_renderers:_render_field",
            inspector_path=".properties.field:FieldPropertyEditor",
        ),
        _definition(
            "label", "Label", "Display", 20,
            fields={},
            events=mouse,
            capabilities=("bindable",),
            default_label="Label",
            description="Static text for headings and notes.",
            renderer_path=".runtime_renderers:_render_label",
            inspector_path=".properties.basic:LabelPropertyEditor",
        ),
        _definition(
            "text", "Text", "Display", 30,
            fields={"text": TextField(default="Text")},
            capabilities=(),
            default_label="Text",
            ui_defaults={"show_label": False},
            description="Multiline static explanatory text with word wrapping.",
            renderer_path=".text_runtime:render_text",
            inspector_path=".properties.text:TextPropertyEditor",
        ),
        _definition(
            "separator", "Separator", "Display", 40,
            fields={},
            capabilities=("divider",),
            default_label="Separator",
            description="Visual divider between parameter groups.",
            renderer_path=".runtime_renderers:_render_separator",
            inspector_path=".properties.separator:SeparatorPropertyEditor",
        ),
    )


def builtin_item_definitions():
    return _standard_item_definitions() + builtin_extension_definitions()


def register_builtin_items():
    for definition in builtin_item_definitions():
        if ITEM_TYPES.get(definition.kind) is None:
            ITEM_TYPES.register(definition)
    return ITEM_TYPES


__all__ = [
    "builtin_item_definitions",
    "register_builtin_items",
]
