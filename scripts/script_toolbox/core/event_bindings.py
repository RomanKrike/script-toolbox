# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import HOST
from ..model.bindings import binding_display_name
from ..model.bindings import matching_bindings
from ..pycompat import text_type
from .executor import execute_script_result


def event_payload(
    event,
    binding=None,
    mouse_button=None,
    modifiers=None
):
    payload = {
        "name": text_type(event or ""),
        "type": "mouse" if mouse_button else "semantic",
        "mouse_button": text_type(mouse_button or ""),
        "modifiers": list(modifiers or []),
    }

    if binding is not None:
        payload["binding_id"] = text_type(
            binding.get("id", "")
        )
        payload["binding_label"] = binding_display_name(
            binding
        )

    return payload


def _binding_guard(toolbox):
    guard = getattr(
        toolbox,
        "_binding_guard",
        None
    )
    if guard is None:
        guard = set()
        setattr(
            toolbox,
            "_binding_guard",
            guard
        )
    return guard


def execute_binding(
    toolbox,
    item,
    binding,
    event,
    value=None,
    old_value=None,
    mouse_button=None,
    modifiers=None,
    parent=None
):
    handler = text_type(
        binding.get("handler", "script")
    )

    payload = event_payload(
        event,
        binding=binding,
        mouse_button=mouse_button,
        modifiers=modifiers
    )

    if handler == "state_toggle":
        callback = getattr(
            toolbox,
            "run_state_binding",
            None
        )
        if callback is None:
            return None
        return callback(
            item,
            binding=binding,
            event=payload
        )

    source = text_type(
        binding.get("script") or ""
    )
    if not source.strip():
        return None

    language = text_type(
        binding.get("language", "python")
    ).lower()
    item_id = text_type(
        item.get("id", "")
    )
    binding_id = text_type(
        binding.get("id", "")
    )
    guard_key = (
        item_id,
        binding_id
    )
    guard = _binding_guard(toolbox)

    if guard_key in guard:
        return None

    guard.add(guard_key)
    try:
        return execute_script_result(
            source,
            language=language,
            toolbox=toolbox,
            parent=parent or toolbox,
            extra_namespace={
                "toolbox": toolbox,
                "item": item,
                "value": value,
                "old_value": old_value,
                "event": payload,
                "host": HOST,
            },
            context="binding:{0}:{1}".format(
                item.get("name", item_id),
                binding_display_name(binding)
            ),
            notify=True
        )
    finally:
        guard.discard(
            guard_key
        )


def dispatch_item_event(
    toolbox,
    item_or_id,
    event,
    value=None,
    old_value=None,
    mouse_button=None,
    modifiers=None,
    parent=None
):
    item = (
        item_or_id
        if isinstance(item_or_id, dict)
        else toolbox.find_item(item_or_id)
    )
    if item is None:
        return []

    bindings = matching_bindings(
        item,
        event,
        mouse_button=mouse_button or "left",
        modifiers=modifiers or []
    )
    results = []

    for binding in bindings:
        result = execute_binding(
            toolbox,
            item,
            binding,
            event,
            value=value,
            old_value=old_value,
            mouse_button=mouse_button,
            modifiers=modifiers,
            parent=parent
        )
        results.append(result)

    return results


__all__ = [
    "dispatch_item_event",
    "event_payload",
    "execute_binding",
]
