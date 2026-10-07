# -*- coding: utf-8 -*-

import os

from script_toolbox.core import standalone_update
from script_toolbox.core import update_transaction


def test_standalone_apply_script_waits_replaces_and_restarts():
    script = standalone_update.render_apply_script()

    assert "Wait-Process -Id $ParentProcessId" in script
    assert "Restore-Previous" in script
    assert "Write-JsonAtomic" in script
    assert "$lock.Lock(0, 1)" in script
    assert "foreach ($entry in $plan.entries)" in script
    assert '"ScriptToolbox.exe"' in script
    assert "[Diagnostics.Process]::Start($start)" in script
    assert "SCRIPT_TOOLBOX_RESTART_TOKEN" in script
    assert 'restart="failed"' in script


def test_standalone_validator_accepts_legacy_destination_without_marker(
    tmp_path
):
    root = tmp_path / "portable"
    runtime = root / "runtime"
    runtime.mkdir(parents=True)
    (runtime / "python311.dll").write_bytes(b"dll")
    (root / "ScriptToolbox.exe").write_bytes(b"exe")

    standalone_dir = root / "standalone"
    standalone_dir.mkdir()
    (standalone_dir / "bootstrap.py").write_text("# bootstrap")

    package = root / "scripts" / "script_toolbox"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("# package")

    assert standalone_update._validate_portable_root(
        str(root),
        require_marker=False
    ) is True


def test_transaction_dispatches_standalone_package(monkeypatch):
    captured = {}

    def fake_install(release, token=None, timeout=30):
        captured["release"] = release
        captured["token"] = token
        captured["timeout"] = timeout
        return {
            "installed": True,
            "restart_required": True,
        }

    monkeypatch.setattr(
        standalone_update,
        "install_release",
        fake_install
    )

    release = {
        "package_kind": "standalone",
        "version": "1.0.1-dev.404",
    }

    result = update_transaction.install_release(
        release,
        token="token",
        timeout=17
    )

    assert result["installed"] is True
    assert result["restart_required"] is True
    assert captured["release"] is release
    assert captured["token"] == "token"
    assert captured["timeout"] == 17


def test_main_window_exits_for_external_standalone_update():
    root = os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
    path = os.path.join(
        root,
        "scripts",
        "script_toolbox",
        "ui",
        "main_window.py"
    )
    source = open(path, "r").read()

    assert 'result.get("restart_required", False)' in source
    assert '"external_restart_scheduled"' in source
    assert "def exit_for_standalone_update" in source
    assert "application.quit()" in source



def test_standalone_update_uses_short_windows_staging_paths():
    root = os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
    path = os.path.join(
        root,
        "scripts",
        "script_toolbox",
        "core",
        "standalone_update.py"
    )
    source = open(path, "r").read()

    assert 'prefix="sbt_u_"' in source
    assert '"x"' in source
    assert "script_toolbox_standalone_update_" not in source
