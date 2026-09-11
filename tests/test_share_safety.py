# -*- coding: utf-8 -*-

from script_toolbox.share.safety import contains_executable_content
from script_toolbox.share.safety import shared_import_allowed


def test_safe_shared_content_does_not_require_confirmation():
    data = {
        "kind": "text",
        "name": "note",
        "text": "Review the Python script before publishing.",
        "bindings": [],
    }
    confirmations = []

    assert shared_import_allowed(
        data,
        lambda: confirmations.append(True)
    ) is True
    assert confirmations == []
    assert contains_executable_content(data) is False


def test_binding_script_is_detected_recursively():
    data = {
        "sections": [
            {
                "kind": "folder",
                "items": [
                    {
                        "kind": "button",
                        "bindings": [
                            {
                                "event": "click",
                                "language": "python",
                                "script": "print('run')",
                            }
                        ],
                    }
                ],
            }
        ],
    }

    assert contains_executable_content(data) is True


def test_state_and_legacy_script_fields_are_detected():
    assert contains_executable_content({
        "kind": "toggle_button",
        "state_get_script": "state = True",
    }) is True
    assert contains_executable_content({
        "kind": "button",
        "click_script": "print('legacy')",
    }) is True


def test_callback_payload_is_detected():
    assert contains_executable_content({
        "kind": "field",
        "callback": "refresh_scene()",
    }) is True
    assert contains_executable_content({
        "callbacks": [
            {
                "event": "changed",
                "command": "refresh_scene()",
            }
        ],
    }) is True


def test_generic_python_or_mel_code_payload_is_detected():
    assert contains_executable_content({
        "language": "python",
        "code": "print('run')",
    }) is True
    assert contains_executable_content({
        "language": "mel",
        "command": "polyCube;",
    }) is True
    assert contains_executable_content({
        "language": "plain_text",
        "code": "not executable",
    }) is False


def test_executable_shared_content_defaults_to_cancel():
    data = {
        "script": "print('run')",
    }

    assert shared_import_allowed(data) is False


def test_executable_shared_content_requires_explicit_confirmation():
    data = {
        "script": "print('run')",
    }
    calls = []

    assert shared_import_allowed(
        data,
        lambda: calls.append("cancel") or False
    ) is False
    assert calls == ["cancel"]

    assert shared_import_allowed(
        data,
        lambda: calls.append("allow") or True
    ) is True
    assert calls == ["cancel", "allow"]
