# -*- coding: utf-8 -*-
"""Authored links and resolved runtime Items share the existing Item pipeline."""
from __future__ import print_function

import copy

from ..model import create_item, ITEM_TYPES
from ..model.items import new_id
from ..pycompat import text_type
from .preset_sync import SyncService
from .references import rewrite_subtree_references

RUNTIME_LINK = "_preset_reference"
REFERENCE_CONFIG_VERSION = 22


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

    def __init__(self, registry):
        self.registry = registry
        self.packages = {}
        self.sources = dict((source["id"], source) for source in registry.sources())
        service = SyncService(registry)
        for source_id in self.sources:
            package = service.installed(source_id)
            if package is not None:
                self.packages[source_id] = package

    def target(self, source_id, preset_id, parameter_id):
        if source_id not in self.sources:
            raise ValueError("Source not configured.")
        package = self.packages.get(source_id)
        if package is None:
            raise ValueError("No valid local cache is installed.")
        for preset in package["presets"]:
            if preset["id"] == preset_id:
                for target in iter_targets(preset["root"]):
                    if target["id"] == parameter_id:
                        return copy.deepcopy(target)
        raise ValueError("Target parameter not found.")

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
        replacements = {old_id: target["id"]}
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
