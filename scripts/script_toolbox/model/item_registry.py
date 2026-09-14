# -*- coding: utf-8 -*-
from __future__ import print_function

from ..pycompat import text_type


_UNSET = object()


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
        normalize_props=None,
        default_bindings=None,
        renderer=None,
        inspector=None
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
        self.normalize_props_hook = normalize_props
        self.default_bindings_hook = default_bindings
        self.renderer = renderer
        self.inspector = inspector

    def has_capability(self, name):
        return text_type(name or "") in self.capabilities

    @property
    def is_container(self):
        return self.has_capability("container")

    @property
    def is_layout(self):
        return self.has_capability("layout")

    @property
    def is_bindable(self):
        return bool(self.events)

    def normalize_props(self, raw_props=None):
        raw_props = raw_props if isinstance(raw_props, dict) else {}
        normalized = {}
        for name, field in self.fields.items():
            normalized[name] = field.normalize(raw_props.get(name))
        if self.normalize_props_hook is not None:
            normalized = self.normalize_props_hook(normalized, raw_props)
            if not isinstance(normalized, dict):
                raise TypeError(
                    "normalize_props for {0!r} must return dict.".format(
                        self.kind
                    )
                )
        return normalized

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
    "bind_item_ui",
    "get_item_type",
    "register_item_type",
]
