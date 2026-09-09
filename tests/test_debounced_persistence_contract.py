# -*- coding: utf-8 -*-

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _source(relative_path):
    return (ROOT / relative_path).read_text(
        encoding="utf-8"
    )


def test_runtime_value_persistence_is_debounced_on_main_thread():
    source = _source(
        "scripts/script_toolbox/ui/debounced_main_window.py"
    )

    assert "SAVE_DEBOUNCE_MS = 500" in source
    assert "self.save_timer.setSingleShot" in source
    assert "self.save_timer.timeout.connect" in source
    assert "self.schedule_save()" in source
    assert "self.config_store.mark_dirty" in source


def test_explicit_save_remains_immediate():
    source = _source(
        "scripts/script_toolbox/ui/debounced_main_window.py"
    )

    assert "return self.config_store.save" in source
    assert "return self.config_store.flush()" in source
    assert "_defer_config_save" not in source


def test_lifecycle_flush_points_are_present():
    source = _source(
        "scripts/script_toolbox/ui/debounced_main_window.py"
    )

    for method_name in (
        "def reload_config(self):",
        "def install_available_update(self):",
        "def hot_reload_after_update(self):",
        "def closeEvent(self, event):",
    ):
        assert method_name in source

    assert source.count("self.flush_pending_save()") >= 5


def test_bootstrap_and_nuke_panel_use_debounced_window():
    bootstrap = _source(
        "scripts/script_toolbox/bootstrap.py"
    )
    nuke = _source(
        "scripts/script_toolbox/nuke_integration.py"
    )

    assert ".ui.debounced_main_window import show" in bootstrap
    assert ".ui.debounced_main_window import close_toolbox" in bootstrap
    assert (
        "script_toolbox.ui.debounced_main_window.ScriptToolbox"
        in nuke
    )


def test_runtime_hooks_are_installed_on_shared_main_window_base():
    source = _source(
        "scripts/script_toolbox/ui/__init__.py"
    )

    assert (
        "install_controls_v2_hooks(\n"
        "    _runtime_module,\n"
        "    _BaseScriptToolbox\n"
        ")"
    ) in source
    assert (
        "install_event_binding_hooks(\n"
        "    get_runtime_renderer_registry(),\n"
        "    _runtime_renderers_module,\n"
        "    _BaseScriptToolbox\n"
        ")"
    ) in source
    assert (
        "install_icon_only_state_refresh(\n"
        "    _BaseScriptToolbox\n"
        ")"
    ) in source
