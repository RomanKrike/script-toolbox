# -*- coding: utf-8 -*-
from __future__ import print_function

import ast
import sys
import token as token_module
import tokenize

from ..model.layouts import is_container_kind
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

    if original[index:index + 3] in ("'''", "\"\"\""):
        quote = original[index:index + 3]
    elif original[index] in ("'", "\""):
        quote = original[index]
    else:
        return _token_text(repr(text_type(value)), encoded)

    prefix = original[:index]
    escaped = text_type(value).replace("\\", "\\\\")

    if quote == "'":
        escaped = escaped.replace("'", "\\'")
    elif quote == "\"":
        escaped = escaped.replace("\"", "\\\"")
    elif quote == "'''":
        escaped = escaped.replace("'''", "\\'\\'\\'")
    else:
        escaped = escaped.replace("\"\"\"", "\\\"\\\"\\\"")

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


def _normalized_replacements(replacements):
    normalized = {}
    for old_value, new_value in (replacements or {}).items():
        old_value = text_type(old_value or "")
        new_value = text_type(new_value or "")
        if old_value and old_value != new_value:
            normalized[old_value] = new_value
    return normalized


def _ast_text_value(node, names=None):
    names = names or {}

    constant = getattr(ast, "Constant", None)
    if constant is not None:
        if isinstance(node, constant):
            if isinstance(node.value, text_type):
                return text_type(node.value)
            return None
    else:
        string_node = getattr(ast, "Str", None)
        if string_node is not None and isinstance(node, string_node):
            return text_type(node.s)

    if isinstance(node, ast.Name):
        return names.get(text_type(node.id))

    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _ast_text_value(node.left, names)
        right = _ast_text_value(node.right, names)
        if left is not None and right is not None:
            return left + right

    return None


def _unresolved_python_references(source, replacements):
    """Return conservative unresolved Script Toolbox references.

    Detection is deliberately narrower than a Python refactoring engine. It
    recognizes direct toolbox aliases and simple string values/concatenations
    only when they are used as the first argument of a managed API method.
    Comments and unrelated string literals never participate in the result.
    """
    normalized = _normalized_replacements(replacements)
    if not source or not normalized:
        return []

    try:
        tree = ast.parse(text_type(source))
    except (SyntaxError, TypeError, ValueError):
        return []

    aliases = set(["toolbox"])
    string_names = {}
    unresolved = []

    class Visitor(ast.NodeVisitor):

        def _visit_nested_scope(self, body):
            saved_aliases = set(aliases)
            saved_names = dict(string_names)
            try:
                for statement in body:
                    self.visit(statement)
            finally:
                aliases.clear()
                aliases.update(saved_aliases)
                string_names.clear()
                string_names.update(saved_names)

        def visit_FunctionDef(self, node):
            self._visit_nested_scope(node.body)

        def visit_ClassDef(self, node):
            self._visit_nested_scope(node.body)

        def visit_Assign(self, node):
            value = node.value
            alias_value = (
                isinstance(value, ast.Name) and
                text_type(value.id) in aliases
            )
            text_value = _ast_text_value(value, string_names)

            for target in node.targets:
                if not isinstance(target, ast.Name):
                    continue
                name = text_type(target.id)
                if alias_value:
                    aliases.add(name)
                elif name != "toolbox":
                    aliases.discard(name)

                if text_value is not None:
                    string_names[name] = text_value
                else:
                    string_names.pop(name, None)

            self.generic_visit(node)

        def visit_Call(self, node):
            function = node.func
            if not isinstance(function, ast.Attribute):
                self.generic_visit(node)
                return

            receiver = function.value
            if not isinstance(receiver, ast.Name):
                self.generic_visit(node)
                return

            receiver_name = text_type(receiver.id)
            method = text_type(function.attr)
            if receiver_name not in aliases or method not in REFERENCE_METHODS:
                self.generic_visit(node)
                return

            if not node.args:
                self.generic_visit(node)
                return

            value = _ast_text_value(node.args[0], string_names)
            if value not in normalized:
                self.generic_visit(node)
                return

            argument = node.args[0]
            constant = getattr(ast, "Constant", None)
            if constant is not None:
                is_direct_literal = (
                    isinstance(argument, constant) and
                    isinstance(argument.value, text_type)
                )
            else:
                string_node = getattr(ast, "Str", None)
                is_direct_literal = (
                    string_node is not None and
                    isinstance(argument, string_node)
                )

            # A direct toolbox literal is the supported rewrite shape. If it
            # still exists here, the tokenizer could not rewrite it safely, so
            # report it as unresolved rather than silently pretending success.
            kind = "literal"
            if receiver_name != "toolbox":
                kind = "alias"
            elif isinstance(argument, ast.Name):
                kind = "dynamic_name"
            elif not is_direct_literal:
                kind = "computed"

            unresolved.append({
                "name": value,
                "method": method,
                "receiver": receiver_name,
                "line": int(getattr(node, "lineno", 0) or 0),
                "kind": kind,
            })
            self.generic_visit(node)

    Visitor().visit(tree)
    return unresolved


def rewrite_python_references_result(source, replacements):
    """Rewrite supported references and report conservative unresolved ones."""
    source = text_type(source or "")
    normalized = _normalized_replacements(replacements)

    if not source or not normalized:
        return {
            "source": source,
            "changed": False,
            "unresolved": [],
        }

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

    if replacements_by_line:
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
            result = result.decode("utf-8")
    else:
        result = source

    return {
        "source": result,
        "changed": result != source,
        "unresolved": _unresolved_python_references(
            result,
            normalized
        ),
    }


def rewrite_python_references(source, replacements):
    """Backward-compatible source-only reference rewrite helper."""
    return rewrite_python_references_result(
        source,
        replacements
    )["source"]


def python_script_keys(item):
    """Return flat item payload keys whose contents are Python scripts."""
    kind = text_type(item.get("kind", ""))
    result = []

    for key in item.keys():
        key_text = text_type(key)
        if not key_text.endswith("_script"):
            continue

        if key_text == "state_get_script":
            result.append(key)
            continue

        if key_text == "state_on_script":
            if text_type(
                item.get("state_on_language", "python")
            ).lower() == "python":
                result.append(key)
            continue

        if key_text == "state_off_script":
            if text_type(
                item.get("state_off_language", "python")
            ).lower() == "python":
                result.append(key)
            continue

        # Compatibility for direct legacy payloads before normalization.
        language = text_type(
            item.get("language", "python")
        ).lower()
        if kind != "button" or language == "python":
            result.append(key)

    return result


def binding_script_indexes(item):
    result = []

    for index, binding in enumerate(
        item.get("bindings", []) or []
    ):
        if not isinstance(binding, dict):
            continue
        if binding.get("handler", "script") != "script":
            continue
        if text_type(
            binding.get("language", "python")
        ).lower() != "python":
            continue
        if not text_type(
            binding.get("script") or ""
        ).strip():
            continue
        result.append(index)

    return result


def _append_unresolved(target, references, location):
    for reference in references:
        entry = dict(reference)
        entry.update(location)
        target.append(entry)


def rewrite_item_references_result(item, replacements):
    """Rewrite one item and retain locations of unresolved references."""
    changed = False
    unresolved = []

    for key in python_script_keys(item):
        source = text_type(item.get(key) or "")
        result = rewrite_python_references_result(
            source,
            replacements
        )
        if result["changed"]:
            item[key] = result["source"]
            changed = True
        _append_unresolved(
            unresolved,
            result["unresolved"],
            {"script_key": text_type(key)}
        )

    bindings = item.get("bindings")
    if isinstance(bindings, list):
        for index in binding_script_indexes(item):
            binding = bindings[index]
            source = text_type(
                binding.get("script") or ""
            )
            result = rewrite_python_references_result(
                source,
                replacements
            )
            if result["changed"]:
                binding["script"] = result["source"]
                changed = True
            _append_unresolved(
                unresolved,
                result["unresolved"],
                {
                    "binding_index": index,
                    "binding_id": text_type(binding.get("id", "")),
                }
            )

    # Compatibility for schema-17 objects passed directly to editor helpers.
    callbacks = item.get("callbacks")
    if isinstance(callbacks, dict):
        for event, source in list(callbacks.items()):
            source = text_type(source or "")
            result = rewrite_python_references_result(
                source,
                replacements
            )
            if result["changed"]:
                callbacks[event] = result["source"]
                changed = True
            _append_unresolved(
                unresolved,
                result["unresolved"],
                {"callback_event": text_type(event)}
            )

    return {
        "changed": changed,
        "unresolved": unresolved,
    }


def rewrite_item_references(item, replacements):
    """Backward-compatible boolean item rewrite helper."""
    return rewrite_item_references_result(
        item,
        replacements
    )["changed"]


def _walk_subtree(item):
    if not isinstance(item, dict):
        return

    yield item

    if is_container_kind(item.get("kind")):
        for child in item.get("items", []) or []:
            for nested in _walk_subtree(child):
                yield nested


def rewrite_subtree_references_result(item, replacements):
    changed_ids = set()
    unresolved_items = []

    for candidate in _walk_subtree(item):
        result = rewrite_item_references_result(
            candidate,
            replacements
        )
        item_id = text_type(candidate.get("id", ""))
        if result["changed"] and item_id:
            changed_ids.add(item_id)
        if result["unresolved"]:
            unresolved_items.append({
                "id": item_id,
                "name": text_type(candidate.get("name", "")),
                "label": text_type(candidate.get("label", "")),
                "references": result["unresolved"],
            })

    return {
        "changed_ids": changed_ids,
        "unresolved_items": unresolved_items,
    }


def rewrite_subtree_references(item, replacements):
    """Backward-compatible changed-ID subtree rewrite helper."""
    return rewrite_subtree_references_result(
        item,
        replacements
    )["changed_ids"]


def rewrite_document_references_result(document, replacements):
    changed_ids = set()
    unresolved_items = []

    for section in (document or {}).get("sections", []) or []:
        result = rewrite_subtree_references_result(
            section,
            replacements
        )
        changed_ids.update(result["changed_ids"])
        unresolved_items.extend(result["unresolved_items"])

    return {
        "changed_ids": changed_ids,
        "unresolved_items": unresolved_items,
    }


def rewrite_document_references(document, replacements):
    """Backward-compatible changed-ID document rewrite helper."""
    return rewrite_document_references_result(
        document,
        replacements
    )["changed_ids"]


__all__ = [
    "REFERENCE_METHODS",
    "binding_script_indexes",
    "python_script_keys",
    "rewrite_document_references",
    "rewrite_document_references_result",
    "rewrite_item_references",
    "rewrite_item_references_result",
    "rewrite_python_references",
    "rewrite_python_references_result",
    "rewrite_subtree_references",
    "rewrite_subtree_references_result",
]
