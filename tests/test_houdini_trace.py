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


def test_watchdog_dumps_stack_when_event_loop_stops(tmp_path):
    scripts = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts")
    environment = dict(os.environ)
    environment["PYTHONPATH"] = scripts
    environment["SCRIPT_TOOLBOX_HOUDINI_TRACE_DIR"] = str(tmp_path)
    program = """
import os
import time
from script_toolbox import houdini_trace as diagnostics
diagnostics._HANG_TIMEOUT_SECONDS = 0.2
class Signal(object):
    def connect(self, callback):
        self.callback = callback
class Timer(object):
    def __init__(self, parent):
        self.timeout = Signal()
    def setInterval(self, value):
        pass
    def start(self):
        pass
class Core(object):
    QTimer = Timer
diagnostics.start_hang_watchdog(Core, None)
time.sleep(0.8)
os._exit(0)
"""
    result = subprocess.run(
        [sys.executable, "-c", program], env=environment, timeout=10
    )
    assert result.returncode == 0
    logs = list(tmp_path.glob("script-toolbox-houdini-pane-*.log"))
    assert len(logs) == 1
    content = logs[0].read_text(encoding="utf-8")
    assert "crash_handler." in content
    assert "watchdog.armed" in content
    assert "Timeout" in content

def test_freeze_excludes_initial_cycle_without_collecting(tmp_path):
    scripts = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts")
    environment = dict(os.environ)
    environment["PYTHONPATH"] = scripts
    environment["SCRIPT_TOOLBOX_HOUDINI_TRACE_DIR"] = str(tmp_path)
    program = """
import gc
import os
import weakref
from script_toolbox.houdini_trace import freeze_initial_gc_objects
class Cycle(object):
    pass
gc.collect()
obj = Cycle()
obj.link = obj
ref = weakref.ref(obj)
del obj
gc.disable()
flags = gc.get_debug()
before = gc.get_freeze_count()
assert freeze_initial_gc_objects()
assert gc.get_debug() == flags
assert not gc.isenabled()
assert gc.get_freeze_count() > before
assert not gc.garbage
assert freeze_initial_gc_objects()
gc.enable()
gc.collect()
assert ref() is not None
os._exit(0)
"""
    result = subprocess.run(
        [sys.executable, "-c", program], env=environment, timeout=10
    )
    assert result.returncode == 0
    logs = list(tmp_path.glob("script-toolbox-houdini-pane-*.log"))
    assert len(logs) == 1
    content = logs[0].read_text(encoding="utf-8")
    assert "gc.freeze_begin" in content
    assert "gc.freeze_done" in content
