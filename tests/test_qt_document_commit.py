import pytest
from test_qt_lifecycle import run_qt, QT_AVAILABLE

pytestmark = pytest.mark.skipif(not QT_AVAILABLE, reason="Requires real Qt")

SETUP = '''
from script_toolbox.model import create_item
from script_toolbox.core.config import load_config, save_config
w.config['sections'][0]['items'] = [create_item('string', {'id':'v', 'name':'v', 'props':{'value':'old'}})]
w.rebuild()
w.save()
w.open_interface_editor()
e = w.editor_window
'''


def test_apply_preserves_saved_runtime_values(tmp_path):
    run_qt(SETUP + '''
w.store_value('v', 'new')
w.flush_pending_save()
assert e.apply_changes()
assert w.get_value('v') == 'new'
assert load_config()['sections'][0]['items'][0]['props']['value'] == 'new'
e.close()
w.close()
''', tmp_path)


def test_apply_merges_after_reload_of_external_edits(tmp_path):
    run_qt(SETUP + '''
other = load_config()
other['sections'][0]['items'][0]['props']['value'] = 'external'
save_config(other)
w.reload_config()
assert e.apply_changes()
assert w.get_value('v') == 'external'
e.close()
w.close()
''', tmp_path)


def test_failed_apply_keeps_active_document_widgets_and_store(tmp_path):
    run_qt(SETUP + '''
old_config, old_store = w.config, w.config_store.document
e.document_controller.find_by_id('v')['props']['value'] = 'edited'
e.populate_tree()
real_writer = w.config_store.writer
def fail(*args, **kwargs):
    raise OSError('disk full')
w.config_store.writer = fail
errors = []
QtGui.QMessageBox.critical = lambda *a, **kw: errors.append(a[2])
assert e.apply_changes() is False
assert errors
assert w.config is old_config
assert w.config_store.document is old_store
assert w.get_value('v') == 'old'
assert w.value_widgets['v'].root.findChildren(QtGui.QLineEdit)[0].text() == 'old'
assert e.document_controller.find_by_id('v')['props']['value'] == 'edited'
w.config_store.writer = real_writer
e.close()
w.close()
''', tmp_path)


def test_competing_editor_value_reports_conflict_and_keeps_runtime(tmp_path):
    run_qt(SETUP + '''
e.document_controller.find_by_id('v')['props']['value'] = 'editor'
e.populate_tree()
w.store_value('v', 'runtime')
w.flush_pending_save()
warnings = []
QtGui.QMessageBox.warning = lambda *a, **kw: warnings.append(a[2])
assert e.apply_changes() is False
assert warnings
assert w.get_value('v') == 'runtime'
assert e.document_controller.find_by_id('v')['props']['value'] == 'editor'
e.close()
w.close()
''', tmp_path)


def test_external_disk_conflict_keeps_runtime_and_editor_candidate(tmp_path):
    run_qt(SETUP + '''
other = load_config()
other['sections'][0]['items'][0]['props']['value'] = 'external'
save_config(other)
e.document_controller.find_by_id('v')['ui']['label'] = 'edited'
e.populate_tree()
old_config = w.config
errors = []
QtGui.QMessageBox.critical = lambda *a, **kw: errors.append(a[2])
assert e.apply_changes() is False
assert errors
assert w.config is old_config
assert load_config()['sections'][0]['items'][0]['props']['value'] == 'external'
assert e.document_controller.find_by_id('v')['ui']['label'] == 'edited'
e.close()
w.close()
''', tmp_path)
