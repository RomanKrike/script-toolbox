"""Real Qt subprocesses: an ownership crash must fail the test process."""
import importlib.util
import os
import subprocess
import sys
import textwrap

import pytest

QT_AVAILABLE = importlib.util.find_spec("PySide6") is not None
pytestmark = pytest.mark.skipif(not QT_AVAILABLE, reason="Real Qt is checked in the dedicated CI job")


def run_qt(body, tmp_path):
    scripts = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts")
    preamble = '''
import time
import os
from PySide6 import QtCore, QtGui as NativeGui, QtWidgets
before = set(dir(NativeGui)), set(dir(QtCore)), set(dir(QtWidgets.QMenu))
from script_toolbox.compat import HOST, QtGui
os.path.expanduser = lambda path: path.replace("~", %r, 1) if path.startswith("~") else path
app = QtGui.QApplication([])
app.setQuitOnLastWindowClosed(False)
from script_toolbox import ui
from script_toolbox.ui import update_ui, debounced_main_window
assert ui.ScriptToolbox is debounced_main_window.ScriptToolbox
assert before == (set(dir(NativeGui)), set(dir(QtCore)), set(dir(QtWidgets.QMenu)))
update_ui.check_for_update = lambda **kw: {"available": False}
def pump(seconds=0.1):
    until = time.monotonic() + seconds
    while time.monotonic() < until:
        app.processEvents()
        QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.DeferredDelete)
        time.sleep(0.005)
w = ui.ScriptToolbox()
w.prompt_telemetry_consent = lambda: None
''' % str(tmp_path)
    result = subprocess.run([sys.executable, "-c", textwrap.dedent(preamble) + textwrap.dedent(body)],
                            env=dict(os.environ, PYTHONPATH=scripts, QT_QPA_PLATFORM="offscreen"),
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr


def test_close_and_delete_with_slow_update_check(tmp_path):
    run_qt('''
update_ui.check_for_update = lambda **kw: (time.sleep(0.3) or {"available": False})
w.check_for_updates()
job = w.update_check_thread
assert job.isRunning()
assert w.close()
w.deleteLater()
pump(0.6)
assert not job.isRunning()
assert not app._script_toolbox_update_jobs.jobs
''', tmp_path)


def test_install_blocks_duplicate_launch_and_close(tmp_path):
    run_qt('''
calls = []
def install(release):
    calls.append(release)
    time.sleep(0.3)
    return {"installed": False, "error": "test failure"}
update_ui.install_release = install
QtGui.QMessageBox.question = lambda *a, **k: QtGui.QMessageBox.Yes
QtGui.QMessageBox.critical = lambda *a, **k: None
w.update_info = {"release": {"version": "test"}}
w.install_available_update()
w.install_available_update()
assert not w.close()
pump(0.6)
assert len(calls) == 1
assert w.close()
w.deleteLater()
pump()
''', tmp_path)


def test_editor_apply_undo_redo_and_reload(tmp_path):
    run_qt('''
from script_toolbox.ui.bootstrap import initialize_ui
assert initialize_ui() is initialize_ui()
w.open_interface_editor()
editor = w.editor_window
assert editor.__class__ is ui.InterfaceEditor
assert editor.document_controller is not None
editor.apply_changes()
editor.undo()
editor.redo()
editor.close()
from script_toolbox.bootstrap import reload_toolbox
new_window = reload_toolbox()
from script_toolbox import ui as fresh_ui
assert type(new_window) is fresh_ui.ScriptToolbox
assert new_window.close()
new_window.deleteLater()
pump()
from script_toolbox.ui.main_window import show as legacy_show
legacy_window = legacy_show()
assert type(legacy_window) is fresh_ui.ScriptToolbox
assert legacy_window.close()
legacy_window.deleteLater()
pump()
''', tmp_path)


def test_slow_dcc_scan_does_not_block_event_loop_or_own_page(tmp_path):
    run_qt('''
from script_toolbox.ui.dcc_integrations import DccIntegrationsPage
class Manager:
    def scan_details(self):
        time.sleep(0.3)
        return {"installations": {}, "roots": {}}
    def adapters(self):
        return []
page = DccIntegrationsPage(manager=Manager())
pump(0.05)
assert page._scan_job.isRunning()
page.deleteLater()
pump(0.6)
assert not app._script_toolbox_update_jobs.jobs
w.close()
''', tmp_path)


def test_runtime_value_sync_and_collapsible_folder(tmp_path):
    run_qt('''
from script_toolbox.model import create_item
from script_toolbox.ui.collapsible_folder import CollapsibleSection
item = create_item("string", {"id": "test_value", "name": "test_value", "props": {"value": "old"}})
w.config["sections"][0]["items"] = [item]
w.rebuild()
w.store_value("test_value", "new")
controls = w.value_widgets["test_value"].root.findChildren(QtGui.QLineEdit)
assert controls[0].text() == "new"
section = w.findChildren(CollapsibleSection)[0]
previous = section.collapsed
section.toggle()
assert section.collapsed != previous
assert w.config["sections"][0]["props"]["collapsed"] == section.collapsed
w.flush_pending_save()
w.close()
''', tmp_path)


def test_declared_editor_structural_history(tmp_path):
    run_qt('''
from script_toolbox.model import create_item
from script_toolbox.ui.composed_editor import InterfaceEditor
from script_toolbox.ui.bootstrap import initialize_ui
w.config["sections"][0]["items"] = [create_item("string", {
    "id": "history_value", "name": "history_value", "props": {"value": "old"}})]
w.open_interface_editor()
e = w.editor_window
assert type(e) is InterfaceEditor is initialize_ui().InterfaceEditor
assert not hasattr(e, "_history_current")
assert [c.__name__ for c in type(e).__mro__[:6]] == [
    "InterfaceEditor", "TelemetryEditorMixin", "TemplateTransferEditorMixin",
    "PresetEditorMixin", "ReferenceWarningEditorMixin", "ControllerEditorMixin"]
e.tree.setCurrentItem(e.tree_item_by_id("history_value"))
e.duplicate_selected()
assert len(e.working["sections"][0]["items"]) == 2
e.undo()
assert len(e.working["sections"][0]["items"]) == 1
e.redo()
assert len(e.working["sections"][0]["items"]) == 2
assert e.apply_changes()
assert len(w.config["sections"][0]["items"]) == 2
e.close()
w.close()
''', tmp_path)


def test_profile_changes_do_not_block_or_own_settings_page(tmp_path):
    run_qt('''
from script_toolbox.ui.dcc_integrations import DccIntegrationsPage
class Manager:
    def scan_details(self):
        return {"installations": {}, "roots": {}}
    def adapters(self):
        return []
page = DccIntegrationsPage(manager=Manager())
pump()
calls = []
def slow():
    calls.append("start")
    time.sleep(0.3)
page._start_profile_change(slow, "test")
page._start_profile_change(slow, "test")
pump(0.05)
assert page._operation_job.isRunning()
assert calls == ["start"]
page.deleteLater()
pump(0.5)
assert not app._script_toolbox_update_jobs.jobs
w.close()
''', tmp_path)


def test_bounded_discovery_cancels_when_settings_page_is_deleted(tmp_path):
    run_qt('''
from script_toolbox.ui.dcc_integrations import DccIntegrationsPage
from script_toolbox.integrations.discovery_process import scan_in_process
from pathlib import Path
import sys
root = Path(os.path.expanduser("~"))
worker = root / "blocked-scan.py"
worker.write_text("import time; time.sleep(30)")
class Manager:
    def scan_details_bounded(self, cancel_event):
        return scan_in_process({}, cancel_event=cancel_event, timeout=10,
                               command=[sys.executable], worker_path=str(worker))
    def adapters(self):
        return []
page = DccIntegrationsPage(manager=Manager())
pump(0.1)
assert page._scan_job.isRunning()
page.deleteLater()
pump(0.4)
assert not app._script_toolbox_update_jobs.jobs
w.close()
''', tmp_path)


def test_standalone_acknowledges_restart_after_showing_window(tmp_path):
    run_qt('''
from pathlib import Path
from script_toolbox.core import updater
from script_toolbox import standalone
root = Path(os.path.expanduser("~"))
updater.repository_root = lambda: str(root)
os.environ["SCRIPT_TOOLBOX_RESTART_TOKEN"] = "b" * 32
assert standalone.main() == 0
assert (root / ".script_toolbox_restart_ack").read_text() == "b" * 32
from script_toolbox.ui.debounced_main_window import close_toolbox
close_toolbox()
pump()
''', tmp_path)

