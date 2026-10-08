import pytest
from test_qt_lifecycle import run_qt, QT_AVAILABLE

pytestmark = pytest.mark.skipif(not QT_AVAILABLE, reason="Requires real Qt")


def test_renderer_replace_keeps_icon_presentation_without_stacking(tmp_path):
    run_qt('''
from types import SimpleNamespace
from script_toolbox.model import create_item
from script_toolbox.ui import runtime_renderers as rr
item = create_item('icon', {'id':'icon', 'name':'icon'})
owner = SimpleNamespace(toolbox=w)
registry = rr.get_runtime_renderer_registry()
first = registry.render(owner, item)
target = first.findChildren(QtGui.QLabel)[0]
assert target.objectName() == 'RuntimeIconFeedback'
dimensions = (target.width(), target.height())
for i in range(3):
    rr.register_runtime_renderer('icon', rr._render_icon, replace=True)
    widget = registry.render(owner, item)
    target = widget.findChildren(QtGui.QLabel)[0]
    assert target.objectName() == 'RuntimeIconFeedback'
    assert (target.width(), target.height()) == dimensions
    widget.deleteLater()
first.deleteLater()
w.close()
''', tmp_path)


def test_library_status_does_not_block_gui_and_discards_stale_result(tmp_path):
    run_qt('''
from script_toolbox.ui.managed_presets import PresetLibraryPage
from script_toolbox.core.preset_sources import SourceRegistry
import threading
registry = SourceRegistry()
registry.put({'id':'studio', 'name':'Studio', 'remote_path':'/unused'})
page = PresetLibraryPage()
gui_thread = threading.current_thread().ident
threads = []
def slow_status(source_id):
    threads.append(threading.current_thread().ident)
    time.sleep(0.2)
    return {'state':'offline', 'last_sync':None, 'using_cache':False, 'error':'fixture'}
page.service.status = slow_status
started = time.monotonic()
page.list.setCurrentRow(1)
assert time.monotonic() - started < 0.1
heartbeats = []
QtCore.QTimer.singleShot(10, lambda: heartbeats.append(True))
pump(0.05)
assert heartbeats
page.list.setCurrentRow(0)
pump(0.3)
assert threads and threads[0] != gui_thread
assert page.detail.text().startswith('Default')
page.deleteLater()
w.close()
''', tmp_path)


def test_window_close_stops_library_scheduler(tmp_path):
    run_qt('''
w.show()
pump(0.02)
assert w.preset_source_scheduler.timer.isActive()
assert w.close()
assert not w.preset_source_scheduler.timer.isActive()
assert not w.preset_source_scheduler.active
w.deleteLater()
pump()
''', tmp_path)


def test_application_shutdown_waits_for_publication_commit(tmp_path):
    run_qt('''
from script_toolbox.ui.managed_presets import BackgroundJob, publication_jobs
import threading
started, release, finished = threading.Event(), threading.Event(), threading.Event()
def publish():
    started.set()
    release.wait(2)
    finished.set()
job = BackgroundJob(publish, durable=True)
assert started.wait(2)
threading.Timer(0.1, release.set).start()
publication_jobs().shutdown()
assert finished.is_set()
assert not job.thread.is_alive()
w.close()
''', tmp_path)
