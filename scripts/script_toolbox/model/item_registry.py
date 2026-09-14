# -*- coding: utf-8 -*-
from __future__ import print_function

from ..pycompat import text_type
from .fields import FieldValidationError


_UNSET = object()


class ItemValidationError(ValueError):
    """Structured validation error for one universal Item field."""

    def __init__(
        self,
        kind,
        field=None,
        value=None,
        reason="Invalid value",
        item_id=None,
        item_name=None
    ):
        self.kind = text_type(kind or "")
        self.field = text_type(field) if field is not None else None
        self.value = value
        self.reason = text_type(reason or "Invalid value")
        self.item_id = text_type(item_id) if item_id is not None else None
        self.item_name = (
            text_type(item_name) if item_name is not None else None
        )

        target = self.kind or "item"
        if self.item_name:
            target += " name={0!r}".format(self.item_name)
        if self.item_id:
            target += " id={0!r}".format(self.item_id)
        if self.field:
            target += " field={0!r}".format(self.field)
        message = "Invalid {0}: {1}; value={2!r}".format(
            target,
            self.reason,
            self.value
        )
        ValueError.__init__(self, message)


class LayoutSpec(object):
    """Explicit semantic contract for a layout Item type."""

    def __init__(
        self,
        axis=None,
        distribution_field=None,
        cross_alignment_field=None,
        equal_size_field=None
    ):
        self.axis = (
            text_type(axis).strip().lower()
            if axis is not None
            else None
        )
        self.distribution_field = (
            text_type(distribution_field).strip()
            if distribution_field
            else None
        )
        self.cross_alignment_field = (
            text_type(cross_alignment_field).strip()
            if cross_alignment_field
            else None
        )
        self.equal_size_field = (
            text_type(equal_size_field).strip()
            if equal_size_field
            else None
        )


class SectionSpec(object):
    """Explicit semantic contract for a top-level/nested section Item."""

    def __init__(self, mode_field=None):
        self.mode_field = (
            text_type(mode_field).strip()
            if mode_field
            else None
        )


class ItemTypeDefinition(object):
    def __init__(
        self,
        kind,
        title,
        category="Controls",
        description="",
        order=1000,
        fields=None,
        events=None,
        internal_events=None,
        capabilities=None,
        creatable=True,
        default_label=None,
        ui_defaults=None,
        normalize_props=None,
        default_bindings=None,
        renderer=None,
        inspector=None,
        renderer_path=None,
        inspector_path=None,
        layout=None,
        section=None
    ):
        self.kind = text_type(kind or "").strip().lower()
        if not self.kind:
            raise ValueError("Item kind must not be empty.")
        self.title = text_type(title or self.kind.title())
        self.category = text_type(category or "Other")
        self.description = text_type(description or "")
        self.order = int(order)
        self.fields = dict(fields or {})
        self.events = tuple(events or ())
        self.internal_events = tuple(internal_events or ())
        self.capabilities = frozenset(capabilities or ())
        self.creatable = bool(creatable)
        self.default_label = text_type(
            default_label if default_label is not None else self.title
        )
        self.ui_defaults = dict(ui_defaults or {})
        self.normalize_props_hook = normalize_props
        self.default_bindings_hook = default_bindings
        self.renderer = renderer
        self.inspector = inspector
        self.renderer_path = (
            text_type(renderer_path).strip()
            if renderer_path
            else None
        )
        self.inspector_path = (
            text_type(inspector_path).strip()
            if inspector_path
            else None
        )
        if layout is not None and not isinstance(layout, LayoutSpec):
            raise TypeError("layout must be LayoutSpec or None.")
        if section is not None and not isinstance(section, SectionSpec):
            raise TypeError("section must be SectionSpec or None.")
        self.layout = layout
        self.section = section

    def has_capability(self, name):
        return text_type(name or "") in self.capabilities

    @property
    def is_container(self):
        return self.has_capability("container")

    @property
    def is_layout(self):
        return self.has_capability("layout")

    @property
    def is_section(self):
        return self.has_capability("section")

    @property
    def is_bindable(self):
        return bool(self.events)

    @property
    def layout_spec(self):
        return self.layout if self.is_layout else None

    @property
    def section_spec(self):
        return self.section if self.is_section else None

    @property
    def layout_axis(self):
        spec = self.layout_spec
        return spec.axis if spec is not None else None

    def _item_error(
        self,
        field,
        value,
        reason,
        item_id=None,
        item_name=None
    ):
        return ItemValidationError(
            kind=self.kind,
            field=field,
            value=value,
            reason=reason,
            item_id=item_id,
            item_name=item_name
        )

    def validate_props(self, raw_props=None):
        """Return per-field errors after applying supported coercion rules."""
        if raw_props is None:
            raw_props = {}
        if not isinstance(raw_props, dict):
            return {"__props__": "Expected props mapping"}

        errors = {}
        for name, field in self.fields.items():
            raw_value = raw_props.get(name)
            try:
                value = field.normalize(raw_value)
            except FieldValidationError as exc:
                errors[name] = exc.reason
                continue
            except Exception as exc:
                errors[name] = text_type(exc)
                continue
            if not field.validate(value):
                errors[name] = "Final validation failed"
        return errors

    def normalize_props(
        self,
        raw_props=None,
        item_id=None,
        item_name=None
    ):
        if raw_props is None:
            raw_props = {}
        if not isinstance(raw_props, dict):
            raise self._item_error(
                None,
                raw_props,
                "Expected props mapping",
                item_id=item_id,
                item_name=item_name
            )

        normalized = {}
        for name, field in self.fields.items():
            raw_value = raw_props.get(name)
            try:
                value = field.normalize(raw_value)
            except FieldValidationError as exc:
                raise self._item_error(
                    name,
                    raw_value,
                    exc.reason,
                    item_id=item_id,
                    item_name=item_name
                )
            except Exception as exc:
                raise self._item_error(
                    name,
                    raw_value,
                    text_type(exc),
                    item_id=item_id,
                    item_name=item_name
                )
            if not field.validate(value):
                raise self._item_error(
                    name,
                    value,
                    "Final field validation failed",
                    item_id=item_id,
                    item_name=item_name
                )
            normalized[name] = value

        if self.normalize_props_hook is not None:
            try:
                normalized = self.normalize_props_hook(normalized, raw_props)
            except ItemValidationError:
                raise
            except Exception as exc:
                raise self._item_error(
                    None,
                    raw_props,
                    "Cross-field normalization failed: {0}".format(exc),
                    item_id=item_id,
                    item_name=item_name
                )
            if not isinstance(normalized, dict):
                raise self._item_error(
                    None,
                    normalized,
                    "normalize_props hook must return dict",
                    item_id=item_id,
                    item_name=item_name
                )

        for name, field in self.fields.items():
            if name not in normalized:
                continue
            value = normalized[name]
            if not field.validate(value):
                raise self._item_error(
                    name,
                    value,
                    "Final field validation failed after cross-field normalization",
                    item_id=item_id,
                    item_name=item_name
                )
        return normalized

    def section_mode(self, props=None):
        spec = self.section_spec
        if spec is None or not spec.mode_field:
            return None
        field = self.fields.get(spec.mode_field)
        if field is None:
            raise self._item_error(
                spec.mode_field,
                None,
                "SectionSpec mode_field is not declared in fields"
            )
        props = props if isinstance(props, dict) else {}
        return field.normalize(props.get(spec.mode_field))

    def default_bindings(self):
        if self.default_bindings_hook is None:
            return []
        value = self.default_bindings_hook()
        return list(value or [])


class ItemTypeRegistry(object):
    def __init__(self):
        self._definitions = {}

    def register(self, definition, replace=False):
        if not isinstance(definition, ItemTypeDefinition):
            raise TypeError("Expected ItemTypeDefinition.")
        kind = definition.kind
        if kind in self._definitions and not replace:
            raise ValueError(
                "Item type already registered: {0}".format(kind)
            )
        self._definitions[kind] = definition
        return definition

    def unregister(self, kind):
        return self._definitions.pop(
            text_type(kind or "").lower(),
            None
        )

    def get(self, kind, required=False):
        kind = text_type(kind or "").lower()
        definition = self._definitions.get(kind)
        if definition is None and required:
            raise ValueError(
                "Unsupported Script Toolbox item kind: {0!r}".format(kind)
            )
        return definition

    def all(self):
        return tuple(
            sorted(
                self._definitions.values(),
                key=lambda definition: (
                    definition.category.lower(),
                    definition.order,
                    definition.title.lower(),
                    definition.kind,
                )
            )
        )

    def creatable(self):
        return tuple(
            definition
            for definition in self.all()
            if definition.creatable
        )

    def kinds(self):
        return tuple(
            definition.kind
            for definition in self.all()
        )

    def bind_ui(
        self,
        kind,
        renderer=_UNSET,
        inspector=_UNSET
    ):
        definition = self.get(kind, required=True)
        if renderer is not _UNSET:
            definition.renderer = renderer
        if inspector is not _UNSET:
            definition.inspector = inspector
        return definition


ITEM_TYPES = ItemTypeRegistry()


def register_item_type(definition, replace=False):
    return ITEM_TYPES.register(definition, replace=replace)


def get_item_type(kind, required=False):
    return ITEM_TYPES.get(kind, required=required)


def bind_item_ui(kind, renderer=_UNSET, inspector=_UNSET):
    return ITEM_TYPES.bind_ui(
        kind,
        renderer=renderer,
        inspector=inspector
    )


__all__ = [
    "ITEM_TYPES",
    "ItemTypeDefinition",
    "ItemTypeRegistry",
    "ItemValidationError",
    "LayoutSpec",
    "SectionSpec",
    "bind_item_ui",
    "get_item_type",
    "register_item_type",
]
