import pytest
from test_qt_lifecycle import run_qt, QT_AVAILABLE

pytestmark = pytest.mark.skipif(not QT_AVAILABLE, reason="Requires real Qt")

SETUP = '''
from script_toolbox.core.preset_sources import SourceRegistry
from script_toolbox.core.preset_library import publish_presets
from script_toolbox.core.preset_sync import SyncService
from script_toolbox.core.config import config_path, load_config
from script_toolbox.model import create_item
from script_toolbox.ui import preset_snapshot_jobs
registry = SourceRegistry()
remote = os.path.join(os.path.dirname(config_path()), 'snapshot-fixture')
preset = {'id':'p', 'label':'P', 'root':create_item('string', {'id':'target', 'name':'target'})}
publish_presets([preset], remote, 'studio', 'Studio')
registry.put({'id':'studio', 'name':'Studio', 'remote_path':remote})
SyncService(registry).check('studio', True)
original = preset_snapshot_jobs.load_preset_snapshot
import threading
threads = []
def slow(*args, **kwargs):
    threads.append(threading.current_thread())
    time.sleep(0.25)
    return original(*args, **kwargs)
preset_snapshot_jobs.load_preset_snapshot = slow
ticks = []
heartbeat = QtCore.QTimer(w)
heartbeat.setInterval(10)
heartbeat.timeout.connect(lambda: ticks.append(time.monotonic()))
heartbeat.start()
def wait(owner):
    until = time.monotonic() + 5
    while owner.preset_snapshot_loader.busy and time.monotonic() < until:
        pump(0.02)
    assert not owner.preset_snapshot_loader.busy
'''


def test_runtime_and_editor_load_without_blocking_gui(tmp_path):
    run_qt(SETUP + '''
w.reload_config()
assert w._preset_snapshot_loading
wait(w)
assert len(ticks) >= 10
assert threads and all(t is not threading.current_thread() for t in threads)
assert w.preset_resolver.target('studio', 'p', 'target')['id'] == 'target'
start = time.monotonic()
w.open_interface_editor()
assert time.monotonic() - start < 0.2
e = w.editor_window
assert not e.preset_palette.isEnabled()
wait(e)
assert e.preset_palette.isEnabled()
assert e.preset_resolver.target('studio', 'p', 'target')['id'] == 'target'
assert max(b-a for a,b in zip(ticks, ticks[1:])) < 0.2
e.close()
w.close()
''', tmp_path)


def test_async_apply_merges_runtime_values_and_accept_waits(tmp_path):
    run_qt(SETUP + '''
w.config['sections'][0]['items'] = [create_item('string', {'id':'v','name':'v'})]
w.rebuild()
w.save()
w.flush_pending_save()
w.open_interface_editor()
e = w.editor_window
wait(e)
e.document_controller.find_by_id('v')['ui']['label'] = 'edited'
e.populate_tree()
ticks[:] = []
assert e.apply_changes() is None
assert e._apply_pending and not e.isEnabled()
w.store_value('v', 'runtime during load')
assert e.apply_changes() is None
wait(e)
assert e.last_apply_result is True and e.isEnabled()
assert w.get_value('v') == 'runtime during load'
assert w.find_item('v')['ui']['label'] == 'edited'
assert len(ticks) >= 10
e.accept_changes()
assert e.isVisible()
wait(e)
assert not e.isVisible() and e.last_apply_result is True
w.close()
''', tmp_path)


def test_close_during_apply_discards_result_and_preserves_disk(tmp_path):
    run_qt(SETUP + '''
from pathlib import Path
w.open_interface_editor()
e = w.editor_window
wait(e)
w.save()
w.flush_pending_save()
before = Path(config_path()).read_bytes()
assert e.apply_changes() is None
e.close()
e.deleteLater()
w.close()
w.deleteLater()
pump(0.6)
assert Path(config_path()).read_bytes() == before
''', tmp_path)


def test_changed_sources_and_cache_discard_stale_results(tmp_path):
    run_qt(SETUP + '''
w.request_preset_snapshot()
source = registry.get('studio')
registry.remove('studio')
wait(w)
assert 'studio' not in w.preset_resolver.sources
registry.put(source)
calls = []
def racing(registry_arg, previous=None):
    snapshot = original(registry_arg, previous)
    calls.append(snapshot)
    if len(calls) == 1:
        changed = dict(preset)
        changed['root'] = create_item('string', {'id':'target','name':'target','ui':{'label':'new generation'}})
        publish_presets([changed], remote, 'studio', 'Studio')
        SyncService(registry_arg).check('studio', True)
    return snapshot
preset_snapshot_jobs.load_preset_snapshot = racing
w.request_preset_snapshot()
wait(w)
assert len(calls) >= 2
assert w.preset_resolver.target('studio','p','target')['ui']['label'] == 'new generation'
w.close()
''', tmp_path)


def test_editor_change_or_disk_conflict_during_prepare_does_not_commit(tmp_path):
    run_qt(SETUP + '''
from pathlib import Path
from script_toolbox.core.config import save_config
w.config['sections'][0]['items'] = [create_item('string', {'id':'v','name':'v'})]
w.rebuild()
w.save()
w.flush_pending_save()
w.open_interface_editor()
e = w.editor_window
wait(e)
w.save()
w.flush_pending_save()
before = Path(config_path()).read_bytes()
e.apply_changes()
e.document_controller.find_by_id('v')['ui']['label'] = 'programmatic edit'
wait(e)
assert e.last_apply_result is False
assert Path(config_path()).read_bytes() == before
e.populate_tree()
errors = []
QtGui.QMessageBox.critical = lambda *a, **kw: errors.append(a[2])
e.apply_changes()
external = load_config()
external['sections'][0]['items'][0]['props']['value'] = 'external'
save_config(external)
wait(e)
assert e.last_apply_result is False and errors
assert load_config()['sections'][0]['items'][0]['props']['value'] == 'external'
assert e.document_controller.find_by_id('v')['ui']['label'] == 'programmatic edit'
e.close()
w.close()
''', tmp_path)
