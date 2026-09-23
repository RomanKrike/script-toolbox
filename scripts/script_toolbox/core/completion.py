# -*- coding: utf-8 -*-
from __future__ import print_function

import re

try:
    from ..pycompat import text_type
except (ImportError, ValueError):
    text_type = str


CONTEXT_IDENTIFIER = "identifier"
CONTEXT_TOOLBOX_MEMBER = "toolbox_member"
CONTEXT_ITEM_ARGUMENT = "item_argument"
CONTEXT_NONE = "none"

SOURCE_EDITOR_ITEM = "editor_item"
SOURCE_TOOLBOX_API = "toolbox_api"


class CompletionItem(object):

    def __init__(
        self,
        name,
        label="",
        kind="",
        source="",
        insert_text=None,
        detail="",
        display_text=None,
        cursor_offset=None,
        priority=100
    ):
        self.name = text_type(name or "")
        self.label = text_type(label or "")
        self.kind = text_type(kind or "")
        self.source = text_type(source or "")
        self.insert_text = text_type(
            self.name if insert_text is None else insert_text
        )
        self.detail = text_type(detail or "")
        self.display_text = text_type(
            self.name if display_text is None else display_text
        )
        self.cursor_offset = cursor_offset
        self.priority = int(priority)

    def __repr__(self):
        return "CompletionItem({0!r}, source={1!r})".format(
            self.name,
            self.source
        )


class CompletionContext(object):

    def __init__(
        self,
        kind=CONTEXT_NONE,
        prefix="",
        start=0,
        end=0,
        api_name="",
        manual=False
    ):
        self.kind = text_type(kind or CONTEXT_NONE)
        self.prefix = text_type(prefix or "")
        self.start = int(start)
        self.end = int(end)
        self.api_name = text_type(api_name or "")
        self.manual = bool(manual)


class CompletionContextAnalyzer(object):

    _ITEM_ARGUMENT_RE = re.compile(
        r'(?:^|[^\w])toolbox\.'
        r'(?P<api>[A-Za-z_][A-Za-z0-9_]*)'
        r'\s*\(\s*(?P<quote>["\'])'
        r'(?P<prefix>[^"\'\n\r]*)$'
    )
    _TOOLBOX_MEMBER_RE = re.compile(
        r'(?:^|[^\w])toolbox\.'
        r'(?P<prefix>[A-Za-z_][A-Za-z0-9_]*)?$'
    )
    _IDENTIFIER_RE = re.compile(
        r'(?P<prefix>[A-Za-z_][A-Za-z0-9_]*)$'
    )

    def analyze(
        self,
        text,
        cursor_position=None,
        manual=False
    ):
        text = text_type(text or "")
        if cursor_position is None:
            cursor_position = len(text)

        cursor_position = max(
            0,
            min(
                int(cursor_position),
                len(text)
            )
        )
        before = text[:cursor_position]
        line_start = max(
            before.rfind("\n"),
            before.rfind("\r")
        ) + 1
        line = before[line_start:]

        match = self._ITEM_ARGUMENT_RE.search(line)
        if match is not None:
            prefix = text_type(match.group("prefix") or "")
            return CompletionContext(
                kind=CONTEXT_ITEM_ARGUMENT,
                prefix=prefix,
                start=cursor_position - len(prefix),
                end=cursor_position,
                api_name=text_type(match.group("api") or ""),
                manual=manual
            )

        match = self._TOOLBOX_MEMBER_RE.search(line)
        if match is not None:
            prefix = text_type(match.group("prefix") or "")
            return CompletionContext(
                kind=CONTEXT_TOOLBOX_MEMBER,
                prefix=prefix,
                start=cursor_position - len(prefix),
                end=cursor_position,
                manual=manual
            )

        match = self._IDENTIFIER_RE.search(line)
        if match is not None:
            prefix = text_type(match.group("prefix") or "")
            return CompletionContext(
                kind=CONTEXT_IDENTIFIER,
                prefix=prefix,
                start=cursor_position - len(prefix),
                end=cursor_position,
                manual=manual
            )

        if manual:
            return CompletionContext(
                kind=CONTEXT_IDENTIFIER,
                prefix="",
                start=cursor_position,
                end=cursor_position,
                manual=True
            )

        return CompletionContext(
            kind=CONTEXT_NONE,
            prefix="",
            start=cursor_position,
            end=cursor_position,
            manual=False
        )


_ITEM_ARGUMENT_FILTERS = {
    "find_item": "any",
    "get_value": "value",
    "set_value": "value",
    "set_result": "value",
    "store_value": "value",
    "dispatch_binding_event": "any",
    "field_display_values": "field",
    "field_display_text": "field",
    "refresh_field_widget": "field",
    "get_field_selection": "field",
    "add_to_field": "field",
    "remove_from_field": "field",
    "clear_field": "field",
    "field_scene_objects": "field",
    "select_field_objects": "field",
    "refresh_state_button": "toggle_button",
    "refresh_toggle_icon": "toggle_icon",
}


def _item_compatible(item, filter_kind):
    if filter_kind == "any":
        return True
    if filter_kind == "value":
        return "value" in item
    return text_type(item.get("kind", "")).lower() == filter_kind


class EditorItemsProvider(object):

    priority = 10

    def __init__(self, item_source):
        self.item_source = item_source

    def items(self, context):
        if context.kind not in (
            CONTEXT_IDENTIFIER,
            CONTEXT_ITEM_ARGUMENT,
        ):
            return []

        filter_kind = "any"
        if context.kind == CONTEXT_ITEM_ARGUMENT:
            filter_kind = _ITEM_ARGUMENT_FILTERS.get(
                context.api_name,
                ""
            )
            if not filter_kind:
                return []

        try:
            raw_items = self.item_source() or []
        except Exception:
            raw_items = []

        result = []
        seen = set()
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            if not _item_compatible(item, filter_kind):
                continue

            name = text_type(item.get("name", "") or "").strip()
            if not name or name in seen:
                continue
            seen.add(name)

            kind = text_type(item.get("kind", "item") or "item")
            label = text_type(
                item.get(
                    "label",
                    name
                ) or name
            )
            result.append(
                CompletionItem(
                    name=name,
                    label=label,
                    kind=kind,
                    source=SOURCE_EDITOR_ITEM,
                    insert_text=name,
                    detail=kind.replace("_", " ").title(),
                    display_text=name,
                    priority=self.priority
                )
            )

        return result


_TOOLBOX_API_SPECS = (
    (
        "get_value",
        "get_value(key, default=None)",
        'get_value("")',
        len('get_value("'),
        "Read an item value."
    ),
    (
        "set_value",
        "set_value(key, value)",
        'set_value("", value)',
        len('set_value("'),
        "Set an item value."
    ),
    (
        "find_item",
        "find_item(key)",
        'find_item("")',
        len('find_item("'),
        "Find an item by internal id or script name."
    ),
    (
        "all_items",
        "all_items()",
        "all_items()",
        None,
        "Return all current non-folder items."
    ),
    (
        "set_result",
        "set_result(key, value)",
        'set_result("", value)',
        len('set_result("'),
        "Compatibility alias for set_value."
    ),
    (
        "field_display_values",
        "field_display_values(key)",
        'field_display_values("")',
        len('field_display_values("'),
        "Read normalized Field values."
    ),
    (
        "field_display_text",
        "field_display_text(key)",
        'field_display_text("")',
        len('field_display_text("'),
        "Read a Field as display text."
    ),
    (
        "get_field_selection",
        "get_field_selection(key)",
        'get_field_selection("")',
        len('get_field_selection("'),
        "Read selected values from a Field."
    ),
    (
        "add_to_field",
        "add_to_field(key, values)",
        'add_to_field("", values)',
        len('add_to_field("'),
        "Append values to a Field."
    ),
    (
        "remove_from_field",
        "remove_from_field(key, values=None)",
        'remove_from_field("")',
        len('remove_from_field("'),
        "Remove values from a Field."
    ),
    (
        "clear_field",
        "clear_field(key)",
        'clear_field("")',
        len('clear_field("'),
        "Clear a Field."
    ),
    (
        "field_scene_objects",
        "field_scene_objects(key, values=None)",
        'field_scene_objects("")',
        len('field_scene_objects("'),
        "Resolve Field values to scene objects."
    ),
    (
        "select_field_objects",
        "select_field_objects(key, values=None)",
        'select_field_objects("")',
        len('select_field_objects("'),
        "Select scene objects referenced by a Field."
    ),
    (
        "dispatch_binding_event",
        "dispatch_binding_event(item_or_id, event, ...)",
        'dispatch_binding_event("", "click")',
        len('dispatch_binding_event("'),
        "Dispatch an item event through ScriptToolbox."
    ),
    (
        "refresh_state_button",
        "refresh_state_button(key)",
        'refresh_state_button("")',
        len('refresh_state_button("'),
        "Refresh a Toggle Button state."
    ),
    (
        "refresh_toggle_icon",
        "refresh_toggle_icon(key)",
        'refresh_toggle_icon("")',
        len('refresh_toggle_icon("'),
        "Refresh a Toggle Icon state."
    ),
)


class ScriptToolboxApiProvider(object):

    priority = 20

    def __init__(self, toolbox_source):
        self.toolbox_source = toolbox_source

    def items(self, context):
        if context.kind != CONTEXT_TOOLBOX_MEMBER:
            return []

        try:
            toolbox = self.toolbox_source()
        except Exception:
            toolbox = None

        if toolbox is None:
            return []

        result = []
        for (
            name,
            signature,
            insert_text,
            cursor_offset,
            description
        ) in _TOOLBOX_API_SPECS:
            if not callable(getattr(toolbox, name, None)):
                continue
            if cursor_offset is None:
                cursor_offset = len(insert_text)
            result.append(
                CompletionItem(
                    name=name,
                    label=description,
                    kind="api",
                    source=SOURCE_TOOLBOX_API,
                    insert_text=insert_text,
                    detail="API",
                    display_text=signature,
                    cursor_offset=cursor_offset,
                    priority=self.priority
                )
            )

        return result


class CompletionEngine(object):

    def __init__(self, providers=None, analyzer=None):
        self.providers = list(providers or [])
        self.analyzer = analyzer or CompletionContextAnalyzer()

    def context(
        self,
        text,
        cursor_position=None,
        manual=False
    ):
        return self.analyzer.analyze(
            text,
            cursor_position=cursor_position,
            manual=manual
        )

    def complete(
        self,
        text,
        cursor_position=None,
        manual=False
    ):
        context = self.context(
            text,
            cursor_position=cursor_position,
            manual=manual
        )
        if context.kind == CONTEXT_NONE:
            return context, []

        candidates = []
        for provider in self.providers:
            try:
                candidates.extend(
                    provider.items(context) or []
                )
            except Exception:
                continue

        prefix = context.prefix
        lower_prefix = prefix.lower()

        result = []
        seen = set()
        for candidate in candidates:
            name = text_type(candidate.name or "")
            if lower_prefix and not name.lower().startswith(lower_prefix):
                continue

            key = (
                candidate.source,
                name
            )
            if key in seen:
                continue
            seen.add(key)

            if prefix and name.startswith(prefix):
                match_rank = 0
            elif lower_prefix:
                match_rank = 1
            else:
                match_rank = 0

            result.append((
                candidate.priority,
                match_rank,
                name.lower(),
                name,
                candidate
            ))

        result.sort(
            key=lambda entry: (
                entry[0],
                entry[1],
                entry[2],
                entry[3]
            )
        )
        return context, [
            entry[-1]
            for entry in result
        ]


def apply_completion(
    text,
    cursor_position,
    context,
    item
):
    text = text_type(text or "")
    cursor_position = max(
        0,
        min(
            int(cursor_position),
            len(text)
        )
    )

    start = max(
        0,
        min(
            int(context.start),
            cursor_position
        )
    )
    end = max(
        start,
        min(
            int(context.end),
            len(text)
        )
    )
    insertion = text_type(item.insert_text or "")

    result = (
        text[:start] +
        insertion +
        text[end:]
    )

    if item.cursor_offset is None:
        new_cursor = start + len(insertion)
    else:
        new_cursor = start + max(
            0,
            min(
                int(item.cursor_offset),
                len(insertion)
            )
        )

    return result, new_cursor


__all__ = [
    "CONTEXT_IDENTIFIER",
    "CONTEXT_ITEM_ARGUMENT",
    "CONTEXT_NONE",
    "CONTEXT_TOOLBOX_MEMBER",
    "CompletionContext",
    "CompletionContextAnalyzer",
    "CompletionEngine",
    "CompletionItem",
    "EditorItemsProvider",
    "SOURCE_EDITOR_ITEM",
    "SOURCE_TOOLBOX_API",
    "ScriptToolboxApiProvider",
    "apply_completion",
]
