# -*- coding: utf-8 -*-
"""Authored links and resolved runtime Items share the existing Item pipeline."""
from __future__ import print_function

import copy
import os

from .config import file_revision

from ..model import create_item, ITEM_TYPES
from ..model.items import new_id
from ..pycompat import text_type
from .preset_sync import SyncService
from .references import rewrite_subtree_references

RUNTIME_LINK = "_preset_reference"
REFERENCE_CONFIG_VERSION = 22


def linked_preset(root, clone, source_id, preset_id, resolver):
    """Keep layout local and link controls with one shared dependency scope."""
    pairs = []
    def collect(source, local):
        pairs.append((source, local))
        for child, local_child in zip(source.get("items", []), local.get("items", [])):
            collect(child, local_child)
    collect(root, clone)
    scope = {}
    for source, local in pairs:
        scope[source["id"]] = local["id"]
        scope[source["name"]] = local["name"]
    def convert(source, local):
        definition = ITEM_TYPES.get(source["kind"])
        if definition.is_container:
            local["items"] = [convert(child, local_child) for child, local_child in
                              zip(source.get("items", []), local.get("items", []))]
            return local
        reference = resolver.create_reference(source_id, preset_id, source["id"], local["name"])
        reference["id"] = local["id"]
        reference["props"]["scope"] = copy.deepcopy(scope)
        if definition.has_capability("has_value") and "value" in local.get("props", {}):
            reference["props"]["state"]["value"] = copy.deepcopy(local["props"]["value"])
        return reference
    return convert(root, clone)


def has_references(document):
    def visit(children):
        if not isinstance(children, (list, tuple)):
            return False
        for item in children:
            if not isinstance(item, dict):
                continue
            if item.get("kind") == "reference" or RUNTIME_LINK in item:
                return True
            if visit(item.get("items", []) or []):
                return True
        return False
    return isinstance(document, dict) and visit(document.get("sections", []) or [])


def iter_targets(root):
    definition = ITEM_TYPES.get(root.get("kind"))
    if definition and not definition.is_container:
        yield root
    for child in root.get("items", []):
        for target in iter_targets(child):
            yield target


class PresetResolver(object):
    """Pin verified local packages for the lifetime of an open Toolbox."""

    def __init__(self, registry, packages=None, sources=None):
        self.registry = registry
        self.loading = False
        self.sources = (dict((source["id"], source) for source in registry.sources())
                        if sources is None else dict(sources))
        if packages is None:
            service = SyncService(registry)
            packages = dict((source_id, service.installed(source_id)) for source_id in self.sources)
        self.packages = dict((key, package) for key, package in packages.items() if package is not None)
        self._targets = {}
        for source_id, package in self.packages.items():
            for preset in package["presets"]:
                for target in iter_targets(preset["root"]):
                    self._targets[(source_id, preset["id"], target["id"])] = target

    def target(self, source_id, preset_id, parameter_id):
        if self.loading:
            raise ValueError("Preset snapshot is still loading.")
        if source_id not in self.sources:
            raise ValueError("Source not configured.")
        if source_id not in self.packages:
            raise ValueError("No valid local cache is installed.")
        target = self._targets.get((source_id, preset_id, parameter_id))
        if target is None:
            raise ValueError("Target parameter not found.")
        return copy.deepcopy(target)

    def create_reference(self, source_id, preset_id, parameter_id, name=None):
        target = self.target(source_id, preset_id, parameter_id)
        return create_item("reference", {
            "id": new_id(), "name": name or target["name"],
            "ui": {"label": target["ui"]["label"]},
            "props": {"source": source_id, "preset": preset_id,
                      "parameter": parameter_id, "target_kind": target["kind"],
                      "state": {}},
        })

    def resolve(self, reference):
        props = reference["props"]
        target = self.target(props["source"], props["preset"], props["parameter"])
        if target["kind"] != props["target_kind"]:
            raise ValueError("Target type changed; recreate or convert this reference.")
        old_name, old_id = target["name"], target["id"]
        target["id"] = reference["id"]
        target["name"] = reference["name"]
        replacements = dict(props.get("scope", {}))
        replacements[old_id] = target["id"]
        if old_name != target["name"]:
            replacements[old_name] = target["name"]
        rewrite_subtree_references(target, replacements)
        definition = ITEM_TYPES.get(target["kind"])
        if definition.has_capability("has_value") and "value" in props["state"]:
            candidate = dict(target["props"])
            candidate["value"] = copy.deepcopy(props["state"]["value"])
            target["props"] = definition.normalize_props(candidate,
                                                         item_id=target["id"],
                                                         item_name=target["name"])
        target[RUNTIME_LINK] = copy.deepcopy(reference)
        return target

    def resolve_document(self, document):
        """Resolve in place; keep the ConfigDocument revision and ownership."""
        if self.loading:
            return document
        def visit(children):
            for index, item in enumerate(children):
                if item.get("kind") == "reference":
                    try:
                        children[index] = self.resolve(item)
                    except (ValueError, TypeError, KeyError) as exc:
                        item["ui"]["tooltip"] = text_type(exc)
                    continue
                visit(item.get("items", []))
        visit(document.get("sections", []))
        return document


def authored_document(document):
    """Project a runtime document back to links, never resolved definitions."""
    result = copy.deepcopy(document)

    def visit(children):
        for index, item in enumerate(children):
            link = item.get(RUNTIME_LINK)
            if link is not None:
                reference = copy.deepcopy(link)
                definition = ITEM_TYPES.get(item.get("kind"))
                if definition and definition.has_capability("has_value"):
                    if "value" in item.get("props", {}):
                        reference["props"]["state"]["value"] = copy.deepcopy(item["props"]["value"])
                children[index] = reference
            else:
                visit(item.get("items", []))
    visit(result.get("sections", []))
    return result


def local_copy(reference, resolver):
    result = resolver.resolve(reference)
    result.pop(RUNTIME_LINK, None)
    return result



def load_preset_snapshot(registry, previous=None):
    """Worker-only preparation; callers transfer the completed snapshot once."""
    sources = dict((source['id'], source) for source in registry.sources())
    service = SyncService(registry)
    before = snapshot_cache_tokens(registry, sources)
    packages = {}
    for source_id, source in sources.items():
        package = service.installed(source_id)
        if package is None and previous is not None and previous.sources.get(source_id) == source:
            package = previous.packages.get(source_id)
        if package is not None:
            packages[source_id] = package
    resolver = PresetResolver(registry, packages=packages, sources=sources)
    resolver.cache_tokens = snapshot_cache_tokens(registry, sources)
    resolver.cache_changed = before != resolver.cache_tokens
    return resolver


def snapshot_cache_tokens(registry, sources):
    return dict((source_id, file_revision(os.path.join(registry.cache_path(source_id), 'active.json')))
                for source_id in sources)
