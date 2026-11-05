"""Houdini crash breadcrumbs survive abrupt process termination."""
import os
import subprocess
import sys
from xml.etree import ElementTree

from script_toolbox.integrations.houdini import HoudiniAdapter


def test_trace_survives_abrupt_exit(tmp_path):
    scripts = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts")
    environment = dict(os.environ)
    environment["PYTHONPATH"] = scripts
    environment["SCRIPT_TOOLBOX_HOUDINI_TRACE_DIR"] = str(tmp_path)
    result = subprocess.run(
        [sys.executable, "-c", "import os; from script_toolbox.houdini_trace import trace; "
         "trace('before_native_crash'); os._exit(17)"],
        env=environment,
        timeout=10,
    )
    assert result.returncode == 17
    logs = list(tmp_path.glob("script-toolbox-houdini-pane-*.log"))
    assert len(logs) == 1
    assert "before_native_crash" in logs[0].read_text(encoding="utf-8")


def test_generated_panel_traces_creation_before_runtime_import():
    script = ElementTree.fromstring(HoudiniAdapter._panel_content()).find(
        ".//script"
    ).text
    assert script.index("panel.script_loaded") < script.index("def onCreateInterface")
    assert "panel.create_enter" in script
    assert "panel.import_container_begin" in script
    assert "panel.create_return" in script
