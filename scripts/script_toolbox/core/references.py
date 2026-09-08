# -*- coding: utf-8 -*-
from __future__ import print_function

import ast
import sys
import token as token_module
import tokenize

from ..model.callbacks import callback_events
from ..pycompat import StringIO
from ..pycompat import text_type


REFERENCE_METHODS = set([
    "find_item",
    "get_value",
    "store_value",
    "set_value",
    "set_result",
    "field_display_values",
    "field_display_text",
    "refresh_field_widget",
    "get_field_selection",
    "add_to_field",
    "remove_from_field",
    "clear_field",
    "field_scene_objects",
    "select_field_objects",
])

_ALWAYS_PYTHON_SCRIPT_KEYS = set([
    "on_change_script",
    "state_get_script",
])

_SKIP_TOKEN_TYPES = set([
    getattr(tokenize, "NL", -1),
    getattr(tokenize, "NEWLINE", -1),
    getattr(tokenize, "INDENT", -1),
    getattr(tokenize, "DEDENT", -1),
    getattr(tokenize, "COMMENT", -1),
    getattr(tokenize, "ENCODING", -1),
])


def _as_text(value):
    if isinstance(value, text_type):
        return value

    try:
        return value.decode("utf-8")
    except Exception:
        return text_type(value)


def _token_text(value, encoded):
    value = _as_text(value)
    if encoded:
        return value.encode("utf-8")
    return value


def _literal_value(token_text):
    try:
        value = ast.literal_eval(token_text)
    except Exception:
        try:
            value = ast.literal_eval(_as_text(token_text))
        except Exception:
            return None

    if isinstance(value, text_type):
        return value

    try:
        return value.decode("utf-8")
    except Exception:
        return None


def _replacement_string_token(token_text, value, encoded):
    original = _as_text(token_text)
    index = 0

    while (
        index < len(original) and
        original[index] in "uUrRbB"
    ):
        index += 1

    if index >= len(original):
        return _token_text(repr(text_type(value)), encoded)

    if original[index:index + 3] in ("'''", '\"\"\"'):
        quote = original[index:index + 3]
    elif original[index] in ("'", '\"'):
        quote = original[index]
    else:
        return _token_text(repr(text_type(value)), encoded)

    prefix = original[:index]
    escaped = text_type(value).replace("\\", "\\\\")

    if quote == "'":
        escaped = escaped.replace("'", "\\'")
    elif quote == '\"':
        escaped = escaped.replace('\"', '\\"')
    elif quote == "'''":
        escaped = escaped.replace("'''", "\\'\\'\\'")
    else:
        escaped = escaped.replace('\"\"\"', '\\\"\\\"\\\"')

    return _token_text(
        prefix + quote + escaped + quote,
        encoded
    )


def _tokens(source):
    encoded = sys.version_info[0] < 3
    token_source = (
        source.encode("utf-8")
        if encoded
        else source
    )
    generator = tokenize.generate_tokens(
        StringIO(token_source).readline
    )
    result = []

    while True:
        try:
            result.append(next(generator))
        except StopIteration:
            break
        except (tokenize.TokenError, IndentationError):
            break

    return result, token_source, encoded


def rewrite_python_references(source, replacements):
    """Rewrite literal Script Toolbox API keys without changing other text.

    Only a literal first argument on calls such as
    ``toolbox.get_value("name")`` is considered a managed reference. Plain
    strings, comments, variables and calls on unrelated objects are left
    untouched.
    """
    source = text_type(source or "")
    normalized = {}

    for old_value, new_value in (replacements or {}).items():
        old_value = text_type(old_value or "")
        new_value = text_type(new_value or "")
        if old_value and old_value != new_value:
            normalized[old_value] = new_value

    if not source or not normalized:
        return source

    tokens, token_source, encoded = _tokens(source)
    significant = [
        token
        for token in tokens
        if token[0] not in _SKIP_TOKEN_TYPES
    ]
    replacements_by_line = {}

    for index in range(len(significant) - 4):
        toolbox_token = significant[index]
        dot_token = significant[index + 1]
        method_token = significant[index + 2]
        open_token = significant[index + 3]
        argument_token = significant[index + 4]

        if (
            toolbox_token[0] != token_module.NAME or
            _as_text(toolbox_token[1]) != "toolbox"
        ):
            continue

        if index:
            previous = significant[index - 1]
            if _as_text(previous[1]) == ".":
                continue

        if (
            _as_text(dot_token[1]) != "." or
            method_token[0] != token_module.NAME or
            _as_text(method_token[1]) not in REFERENCE_METHODS or
            _as_text(open_token[1]) != "(" or
            argument_token[0] != token_module.STRING
        ):
            continue

        current_value = _literal_value(argument_token[1])
        if current_value not in normalized:
            continue

        start = argument_token[2]
        end = argument_token[3]
        if start[0] != end[0]:
            continue

        line_index = start[0] - 1
        replacements_by_line.setdefault(
            line_index,
            []
        ).append((
            start[1],
            end[1],
            _replacement_string_token(
                argument_token[1],
                normalized[current_value],
                encoded
            )
        ))

    if not replacements_by_line:
        return source

    lines = token_source.splitlines(True)

    for line_index, line_replacements in replacements_by_line.items():
        if line_index < 0 or line_index >= len(lines):
            continue

        line = lines[line_index]
        for start, end, replacement in sorted(
            line_replacements,
            key=lambda entry: entry[0],
            reverse=True
        ):
            line = line[:start] + replacement + line[end:]
        lines[line_index] = line

    result = b"".join(lines) if encoded else "".join(lines)
    if encoded:
        return result.decode("utf-8")
    return result


def python_script_keys(item):
    """Return flat item payload keys whose contents are Python scripts."""
    kind = text_type(item.get("kind", ""))
    language = text_type(item.get("language", "python")).lower()
    result = []

    for key in item.keys():
        key_text = text_type(key)
        if not key_text.endswith("_script"):
            continue

        if key_text in _ALWAYS_PYTHON_SCRIPT_KEYS:
            result.append(key)
        elif kind != "button" or language == "python":
            result.append(key)

    return result


def callback_script_keys(item):
    """Return callback event keys that currently contain Python code."""
    callbacks = item.get("callbacks")
    if not isinstance(callbacks, dict):
        return []

    result = []
    for event in callback_events(item.get("kind")):
        if text_type(callbacks.get(event) or "").strip():
            result.append(event)
    return result


def rewrite_item_references(item, replacements):
    changed = False

    for key in python_script_keys(item):
        source = text_type(item.get(key) or "")
        rewritten = rewrite_python_references(
            source,
            replacements
        )
        if rewritten == source:
            continue
        item[key] = rewritten
        changed = True

    callbacks = item.get("callbacks")
    if isinstance(callbacks, dict):
        for event in callback_script_keys(item):
            source = text_type(callbacks.get(event) or "")
            rewritten = rewrite_python_references(
                source,
                replacements
            )
            if rewritten == source:
                continue
            callbacks[event] = rewritten
            changed = True

    return changed


def _walk_subtree(item):
    if not isinstance(item, dict):
        return

    yield item

    if item.get("kind") in ("folder", "row"):
        for child in item.get("items", []) or []:
            for nested in _walk_subtree(child):
                yield nested


def rewrite_subtree_references(item, replacements):
    changed_ids = set()

    for candidate in _walk_subtree(item):
        if not rewrite_item_references(candidate, replacements):
            continue
        item_id = text_type(candidate.get("id", ""))
        if item_id:
            changed_ids.add(item_id)

    return changed_ids


def rewrite_document_references(document, replacements):
    changed_ids = set()

    for section in (document or {}).get("sections", []) or []:
        changed_ids.update(
            rewrite_subtree_references(
                section,
                replacements
            )
        )

    return changed_ids


__all__ = [
    "REFERENCE_METHODS",
    "callback_script_keys",
    "python_script_keys",
    "rewrite_document_references",
    "rewrite_item_references",
    "rewrite_python_references",
    "rewrite_subtree_references",
]
