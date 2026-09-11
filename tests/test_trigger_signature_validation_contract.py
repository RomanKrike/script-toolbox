# -*- coding: utf-8 -*-

import os


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _source(*parts):
    path = os.path.join(ROOT, *parts)
    with open(path, "r") as handle:
        return handle.read()


def test_duplicate_trigger_signature_is_handler_agnostic():
    source = _source(
        "scripts",
        "script_toolbox",
        "ui",
        "properties",
        "trigger_validation.py"
    )

    block = source.split(
        "def _duplicate_signature(",
        1
    )[1].split(
        "def install_trigger_signature_validation():",
        1
    )[0]

    assert "signature = binding_signature(candidate)" in block
    assert "binding_signature(page.write()) == signature" in block
    assert "handler" not in block


def test_trigger_signature_validation_installs_after_toggle_tab_hooks():
    source = _source(
        "scripts",
        "script_toolbox",
        "ui",
        "properties",
        "__init__.py"
    )

    state_pos = source.index("install_integrated_toggle_state_tabs()")
    validation_pos = source.index("install_trigger_signature_validation()")

    assert state_pos < validation_pos
    assert (
        "from .trigger_validation import install_trigger_signature_validation"
        in source
    )
