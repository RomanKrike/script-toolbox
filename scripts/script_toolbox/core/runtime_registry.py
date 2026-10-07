# -*- coding: utf-8 -*-
from __future__ import print_function

from ..pycompat import text_type


class RuntimeRendererRegistry(object):
    """Runtime renderer table populated from ItemType definitions on UI bootstrap."""

    def __init__(self):
        self._renderers = {}
        self._sources = {}
        self._decorator = None

    def _kind(self, kind):
        return text_type(kind or "").strip().lower()

    def register(self, kind, renderer, replace=False):
        kind = self._kind(kind)

        if not kind:
            raise ValueError("Renderer kind must not be empty.")

        if not callable(renderer):
            raise TypeError("Renderer for '{0}' must be callable.".format(kind))

        if kind in self._renderers and not replace:
            raise ValueError(
                "Renderer for kind '{0}' is already registered.".format(kind)
            )

        source = (getattr(renderer, "_script_toolbox_raw_renderer", renderer)
                  if self._decorator is not None else renderer)
        prepared = self._decorator(kind, source) if self._decorator is not None else source
        self._sources[kind] = source
        self._renderers[kind] = prepared
        return renderer

    def set_decorator(self, decorator):
        """Build every presentation from its raw source; never stack pipelines."""
        if self._decorator is decorator:
            return self
        prepared = dict((kind, decorator(kind, renderer))
                        for kind, renderer in self._sources.items())
        self._decorator = decorator
        self._renderers = prepared
        return self

    def unregister(self, kind):
        self._sources.pop(self._kind(kind), None)
        return self._renderers.pop(
            self._kind(kind),
            None
        )

    def renderer_for(self, kind):
        return self._renderers.get(
            self._kind(kind)
        )

    def has(self, kind):
        return self.renderer_for(kind) is not None

    def kinds(self):
        return tuple(sorted(self._renderers.keys()))

    def render(self, owner, item, compact=False):
        if not isinstance(item, dict):
            return None

        renderer = self.renderer_for(
            item.get("kind")
        )

        if renderer is None:
            return None

        return renderer(
            owner,
            item,
            compact=compact
        )


def install_registry_hook_once(registry, marker, installer):
    """Run one registry installer once for a registry instance."""
    if getattr(registry, marker, False):
        return False
    installer(registry)
    setattr(registry, marker, True)
    return True


__all__ = [
    "RuntimeRendererRegistry",
    "install_registry_hook_once",
]
