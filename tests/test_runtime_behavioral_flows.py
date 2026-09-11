# -*- coding: utf-8 -*-

import pytest

from script_toolbox.core.runtime_registry import RuntimeRendererRegistry
from script_toolbox.core.runtime_registry import install_registry_hook_once
from script_toolbox.core.state_toggle import state_toggle_action


@pytest.mark.parametrize("kind", ["toggle_button", "toggle_icon"])
def test_internal_toggle_flow_is_off_on_off_and_selects_scripts(kind):
    item = {
        "kind": kind,
        "state_source": "internal",
        "value": False,
        "state_on_script": "turn_on()",
        "state_on_language": "python",
        "state_off_script": "turn_off()",
        "state_off_language": "mel",
    }

    first = state_toggle_action(item, item["value"])
    assert first["script"] == "turn_on()"
    assert first["language"] == "python"
    assert first["stores_value"] is True
    item["value"] = first["next_state"]
    assert item["value"] is True

    second = state_toggle_action(item, item["value"])
    assert second["script"] == "turn_off()"
    assert second["language"] == "mel"
    item["value"] = second["next_state"]
    assert item["value"] is False


def test_script_driven_toggle_uses_action_scripts_without_internal_storage():
    item = {
        "kind": "toggle_button",
        "state_source": "script",
        "state_on_script": "enable()",
        "state_off_script": "disable()",
    }
    assert state_toggle_action(item, False)["stores_value"] is False
    assert state_toggle_action(item, True)["stores_value"] is False


def test_renderer_hook_install_is_behaviorally_idempotent():
    registry = RuntimeRendererRegistry()
    calls = []

    def renderer(owner, item, compact=False):
        calls.append("render")
        return {"id": item["id"]}

    registry.register("button", renderer)

    def installer(target_registry):
        original = target_registry.renderer_for("button")

        def wrapper(owner, item, compact=False):
            calls.append("hook")
            return original(owner, item, compact=compact)

        target_registry.register("button", wrapper, replace=True)

    assert install_registry_hook_once(
        registry, "_test_hook_installed", installer
    ) is True
    installed = registry.renderer_for("button")
    assert install_registry_hook_once(
        registry, "_test_hook_installed", installer
    ) is False
    assert registry.renderer_for("button") is installed

    assert registry.render(None, {"kind": "button", "id": "x"}) == {"id": "x"}
    assert calls == ["hook", "render"]
