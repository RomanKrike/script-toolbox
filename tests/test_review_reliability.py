# -*- coding: utf-8 -*-
import json
import os
import subprocess
import sys

import pytest

from script_toolbox.core import config, preferences, standalone_update, update_transaction
from script_toolbox.core.config_store import ConfigStore
from script_toolbox.core.file_lock import FileLock, FileLockError


def test_atomic_preferences_failure_preserves_previous_file(tmp_path, monkeypatch):
    path = str(tmp_path / "preferences.json")
    preferences.save_preferences({"marker": "old"}, path)
    original = (tmp_path / "preferences.json").read_bytes()

    def fail_replace(*args):
        raise OSError("simulated disk failure")

    monkeypatch.setattr(preferences, "_replace_file", fail_replace)
    with pytest.raises(OSError):
        preferences.save_preferences({"marker": "new"}, path)
    assert (tmp_path / "preferences.json").read_bytes() == original
    assert not list(tmp_path.glob("*.tmp"))


def test_stale_preferences_merge_only_local_changes(tmp_path):
    path = str(tmp_path / "preferences.json")
    preferences.save_preferences({"marker": "old"}, path)
    a, b = preferences.load_preferences(path), preferences.load_preferences(path)
    a["proxy"] = {"enabled": True}
    b["update_channel"] = "development"
    preferences.save_preferences(a, path)
    preferences.save_preferences(b, path)
    current = preferences.load_preferences(path)
    assert current["proxy"] == {"enabled": True}
    assert current["update_channel"] == "development"


def test_preferences_recover_preserves_corrupt_file(tmp_path):
    path = str(tmp_path / "preferences.json")
    preferences.save_preferences({"marker": "old"}, path)
    preferences.save_preferences({"marker": "new"}, path)
    (tmp_path / "preferences.json").write_text("broken")
    with pytest.warns(RuntimeWarning):
        restored = preferences.load_preferences(path)
    assert restored["marker"] == "old"
    assert next(tmp_path.glob("preferences.json.corrupt-*")).read_text() == "broken"


def test_preferences_without_backup_do_not_silently_reset(tmp_path):
    path = tmp_path / "preferences.json"
    path.write_text("broken")
    with pytest.raises(RuntimeError):
        preferences.load_preferences(str(path))
    assert path.read_text() == "broken"


@pytest.mark.parametrize("use_store", [False, True])
def test_stale_config_is_saved_as_conflict_copy(tmp_path, use_store):
    path = str(tmp_path / "toolbox.json")
    config.save_config({}, path)
    a, b = config.load_config(path), config.load_config(path)
    store_a, store_b = ConfigStore(a, path), ConfigStore(b, path)
    a["sections"][0]["ui"]["label"] = "a"
    b["sections"][0]["ui"]["label"] = "b"
    if use_store:
        store_a.save(a)
    else:
        config.save_config(a, path)
    with pytest.raises(config.ConfigConflictError) as error:
        if use_store:
            store_b.save(b)
        else:
            config.save_config(b, path)
    assert config.load_config(path)["sections"][0]["ui"]["label"] == "a"
    assert config.load_config(error.value.copy_path)["sections"][0]["ui"]["label"] == "b"
    if use_store:
        assert store_b.dirty


def test_lock_blocks_another_process_and_releases_after_crash(tmp_path):
    path = str(tmp_path / "shared.lock")
    script = "from script_toolbox.core.file_lock import FileLock; import os; " \
             "lock=FileLock(%r); lock.__enter__(); print('locked', flush=True); " \
             "os.read(0, 1)" % path
    environment = dict(os.environ, PYTHONPATH=os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts"))
    child = subprocess.Popen([sys.executable, "-c", script], env=environment,
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        assert child.stdout.readline().strip() == b"locked"
        with pytest.raises(FileLockError):
            with FileLock(path):
                pass
    finally:
        child.kill()
        child.wait()
    with FileLock(path):
        pass


def test_update_lock_prevents_recovery_of_active_transaction(tmp_path, monkeypatch):
    monkeypatch.setattr(update_transaction, "repository_root", lambda: str(tmp_path))
    called = []
    monkeypatch.setattr(update_transaction, "_install_release_locked", lambda *a, **k: called.append(True))
    with FileLock(str(tmp_path / ".script_toolbox_update.lock")):
        with pytest.raises(update_transaction.UpdateError, match="already running"):
            update_transaction.install_release({})
    assert called == []


def test_portable_manifest_only_removes_owned_files(tmp_path):
    source, destination = tmp_path / "source", tmp_path / "destination"
    source.mkdir()
    destination.mkdir()
    (source / "README.md").write_text("new")
    (destination / "README.md").write_text("old")
    (destination / "user_notes.txt").write_text("keep")
    (destination / "standalone-manifest.json").write_text(json.dumps({"README.md": "unused", "docs/obsolete.txt": "unused"}))
    (source / "standalone-manifest.json").write_text(json.dumps(standalone_update.package_manifest(str(source))))
    transaction = standalone_update._prepare_apply_plan(str(source), str(destination), "1.0.2")
    plan = json.loads(open(os.path.join(transaction, "plan.json")).read())
    assert "user_notes.txt" not in {entry["path"] for entry in plan["entries"]}
    assert next(entry for entry in plan["entries"] if entry["path"] == "docs/obsolete.txt")["sha256"] is None


def test_portable_rejects_manifest_traversal(tmp_path):
    (tmp_path / "standalone-manifest.json").write_text(json.dumps({"../outside": "bad"}))
    with pytest.raises(standalone_update.UpdateError, match="Unsafe"):
        standalone_update._safe_manifest(str(tmp_path))


def test_live_nuke_sync_ignores_other_active_profile(monkeypatch):
    import importlib.util
    import types
    from script_toolbox.integrations.nuke import NukeAdapter
    import script_toolbox

    fake_nuke = types.SimpleNamespace(NUKE_VERSION_STRING="12.0v1")
    monkeypatch.setitem(sys.modules, "nuke", fake_nuke)
    monkeypatch.setitem(sys.modules, "script_toolbox.compat",
                        types.SimpleNamespace(HOST=types.SimpleNamespace(key="nuke"), nuke=fake_nuke))
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts", "script_toolbox", "nuke_integration.py")
    spec = importlib.util.spec_from_file_location("script_toolbox.nuke_integration", path)
    runtime = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runtime)
    monkeypatch.setattr(script_toolbox, "nuke_integration", runtime, raising=False)
    monkeypatch.setitem(sys.modules, "script_toolbox.nuke_integration", runtime)
    calls = []
    runtime._current_settings = lambda **kw: {"main_menu": True, "auto_open": False}
    runtime.register_menu = lambda: calls.append(True)
    runtime.apply_current_integration("profile-a", activate_profile=True)
    calls[:] = []
    adapter = NukeAdapter()
    assert not adapter._sync_live_nuke(types.SimpleNamespace(version="12.0", profile_id="profile-b"))
    assert calls == []
    assert adapter._sync_live_nuke(types.SimpleNamespace(version="12.0", profile_id="profile-a"))
    assert calls == [True]
