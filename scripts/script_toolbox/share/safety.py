# -*- coding: utf-8 -*-
from __future__ import print_function

from ..pycompat import text_type


_DIRECT_EXECUTABLE_KEYS = (
    "callback",
    "callbacks",
    "script",
)


def _is_nonempty(value):
    if isinstance(value, text_type):
        return bool(value.strip())

    if isinstance(value, bytes):
        try:
            return bool(value.decode("utf-8").strip())
        except Exception:
            return bool(value)

    return value is not None and value != ""


def _is_executable_key(key):
    key = text_type(key or "").strip().lower()
    return (
        key in _DIRECT_EXECUTABLE_KEYS or
        key.endswith("_script") or
        key.endswith("_callback")
    )


def contains_executable_content(value):
    """Return True when shared data contains executable script/callback data.

    Detection runs on the decoded raw share payload, before model
    normalization can discard legacy or unknown script fields.
    """
    if isinstance(value, dict):
        language = text_type(
            value.get(
                "language",
                value.get("script_language", "")
            ) or ""
        ).strip().lower()

        for key, child in value.items():
            normalized_key = text_type(
                key or ""
            ).strip().lower()

            if _is_executable_key(normalized_key):
                if isinstance(child, (dict, list, tuple)):
                    if child:
                        return True
                elif _is_nonempty(child):
                    return True

            # Support generic action payloads that store Python/MEL code under
            # a code/command field instead of the current `script` key.
            if (
                normalized_key in ("code", "command") and
                language in ("python", "mel") and
                _is_nonempty(child)
            ):
                return True

            if contains_executable_content(child):
                return True

        return False

    if isinstance(value, (list, tuple)):
        for child in value:
            if contains_executable_content(child):
                return True

    return False


def shared_import_allowed(
    data,
    confirm_executable=None
):
    """Gate a decoded shared payload before any import-side mutation.

    Safe payloads pass without prompting. Executable payloads default to a
    deny decision unless the caller supplies a confirmation callback that
    explicitly returns True.
    """
    if not contains_executable_content(
        data
    ):
        return True

    if confirm_executable is None:
        return False

    return bool(
        confirm_executable()
    )


__all__ = [
    "contains_executable_content",
    "shared_import_allowed",
]
