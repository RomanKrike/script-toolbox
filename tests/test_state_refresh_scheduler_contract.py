# -*- coding: utf-8 -*-

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _source(relative_path):
    return (ROOT / relative_path).read_text(
        encoding="utf-8"
    )


def test_runtime_uses_bounded_state_refresh_timer():
    source = _source(
        "scripts/script_toolbox/ui/debounced_main_window.py"
    )

    assert "STATE_REFRESH_INTERVAL_MS = 100" in source
    assert "self.state_refresh_timer.setSingleShot" in source
    assert "self.state_refresh_timer.timeout.connect" in source
    assert "self.state_refresh_queue.request()" in source
    assert "self.state_refresh_queue.consume()" in source


def test_runtime_value_changes_request_scheduled_refresh():
    source = _source(
        "scripts/script_toolbox/ui/debounced_main_window.py"
    )

    store_start = source.index("    def store_value(")
    scheduler_start = source.index("    # State refresh scheduling")
    store_block = source[store_start:scheduler_start]

    assert "self.request_state_refresh()" in store_block
    assert "self.refresh_state_buttons()" not in store_block


def test_selection_polling_is_scheduled_but_rebuild_is_immediate():
    source = _source(
        "scripts/script_toolbox/ui/debounced_main_window.py"
    )

    assert "self._selection_refresh_in_progress" in source
    assert "if self._rebuilding_runtime:" in source
    assert "self.request_state_refresh()" in source
    assert (
        "base_main_window.ScriptToolbox.refresh_state_buttons(\n"
        "            self\n"
        "        )"
        in source
    )


def test_explicit_refresh_cancels_pending_scheduled_pass():
    source = _source(
        "scripts/script_toolbox/ui/debounced_main_window.py"
    )

    refresh_start = source.index("    def refresh_state_buttons(self):")
    selection_start = source.index("    def refresh_selection_fields(")
    refresh_block = source[refresh_start:selection_start]

    assert "self.cancel_scheduled_state_refresh()" in refresh_block
    assert "base_main_window.ScriptToolbox.refresh_state_buttons" in refresh_block
