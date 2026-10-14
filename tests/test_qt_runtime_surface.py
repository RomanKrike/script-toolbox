import pytest
from test_qt_lifecycle import run_qt, QT_AVAILABLE

pytestmark = pytest.mark.skipif(not QT_AVAILABLE, reason="Requires real Qt")

SETUP = '''
from script_toolbox.model import create_item
from script_toolbox.model.fields import IntField
from script_toolbox.model.item_registry import ItemTypeDefinition, register_item_type
from script_toolbox.ui import ValueBinding, register_runtime_renderer
from script_toolbox.core.config import load_config, save_config, config_path
from pathlib import Path
register_item_type(ItemTypeDefinition('surface_test', 'Surface', fields={'value':IntField(default=0)}, capabilities=('has_value',)))
created, rendered, roots, failure = [], [], [], [None]
class Binding(ValueBinding):
    def __init__(self, root, owner, item):
        ValueBinding.__init__(self, root)
        self.toolbox, self.item_id = owner.toolbox, item['id']
        self.connect(root.button.clicked, self.clicked)
        created.append(self)
    def clicked(self):
        self.toolbox.store_value(self.item_id, self.toolbox.get_value(self.item_id) + 1)
    def sync(self, item):
        return True
    def dispose(self):
        ValueBinding.dispose(self)
        self.toolbox = None
def render(owner, item, compact=False):
    rendered.append(item['id'])
    root = QtGui.QWidget(owner.content)
    roots.append(root)
    layout = QtGui.QVBoxLayout(root)
    root.button = QtGui.QPushButton('Change')
    layout.addWidget(root.button)
    if failure[0] == item['id']:
        raise RuntimeError('render failed for ' + item['id'])
    return root
register_runtime_renderer('surface_test', render, value_binding_factory=Binding)
w.config['sections'][0]['items'] = [create_item('surface_test', {'id':'v'+str(i), 'name':'v'+str(i)}) for i in range(3)]
w.rebuild()
w.save()
w.flush_pending_save()
w.open_interface_editor()
e = w.editor_window
e.document_controller.find_by_id('v0')['ui']['label'] = 'edited'
e.populate_tree()
old_config, old_store, old_content = w.config, w.config_store.document, w.content
old_bindings = list(created)
before = Path(config_path()).read_bytes()
errors = []
QtGui.QMessageBox.critical = lambda *args, **kw: errors.append(args[2])
'''


@pytest.mark.parametrize('item_id', ['v0', 'v2'])
def test_failed_renderer_preserves_active_window_and_disk(tmp_path, item_id):
    run_qt(SETUP + "failure[0] = %r\n" % item_id + '''
assert e.apply_changes() is False
assert errors
assert w.config is old_config and w.config_store.document is old_store
assert w.content is old_content and w.content.isEnabled()
assert all(binding.active for binding in old_bindings)
assert all(not binding.active for binding in created[len(old_bindings):])
assert Path(config_path()).read_bytes() == before
assert e.document_controller.find_by_id('v0')['ui']['label'] == 'edited'
failure[0] = None
rendered[:] = []
assert e.apply_changes()
assert rendered == ['v0', 'v1', 'v2']
assert all(not binding.active for binding in old_bindings)
w.value_widgets['v0'].root.button.click()
assert w.get_value('v0') == 1
e.close()
w.close()
''', tmp_path)


def test_failed_writer_disposes_prepared_bindings_and_widgets(tmp_path):
    run_qt(SETUP + '''
from shiboken6 import isValid
writer = w.config_store.writer
def fail(*args, **kwargs):
    raise OSError('disk full')
w.config_store.writer = fail
root_count = len(roots)
assert e.apply_changes() is False
assert w.content is old_content and w.config is old_config
candidate_roots = roots[root_count:]
candidates = created[len(old_bindings):]
assert len(candidates) == 3 and all(not binding.active for binding in candidates)
assert all(binding.active for binding in old_bindings)
assert Path(config_path()).read_bytes() == before
w.config_store.writer = writer
e.close()
w.close()
pump()
assert len(candidate_roots) == 3 and all(not isValid(root) for root in candidate_roots)
''', tmp_path)


def test_activation_failure_reads_latest_disk_without_rollback_write(tmp_path):
    run_qt(SETUP + '''
from script_toolbox.ui import runtime_surface
original = runtime_surface.restore_view_state
def fail(window, state):
    external = load_config()
    external['sections'][0]['items'][0]['props']['value'] = 17
    save_config(external)
    raise RuntimeError('swap failed')
runtime_surface.restore_view_state = fail
assert e.apply_changes() is False
assert errors and 'saved' in errors[-1].lower()
assert w.get_value('v0') == 17
assert w.config_store.document is w.config
assert not w.config_store.dirty
assert not w.content.isEnabled()
assert not w.value_widgets
assert all(not binding.active for binding in created)
assert not w.selection_timer.isActive()
assert e.document_controller.find_by_id('v0')['ui']['label'] == 'edited'
runtime_surface.restore_view_state = original
pump()
w.reload_config()
assert w.content.isEnabled() and w.selection_timer.isActive()
assert w.get_value('v0') == 17
e.close()
w.close()
assert load_config()['sections'][0]['items'][0]['props']['value'] == 17
''', tmp_path)


def test_preparation_rejects_model_writes_and_reentrant_current_change(tmp_path):
    run_qt(SETUP + '''
def writes(owner, item, compact=False):
    owner.toolbox.store_value('v0', 99)
register_runtime_renderer('surface_test', writes, replace=True)
assert e.apply_changes() is False
assert w.get_value('v0') == 0
assert Path(config_path()).read_bytes() == before
def reenters(owner, item, compact=False):
    w.store_value('v0', 7)
    return render(owner, item, compact=compact)
register_runtime_renderer('surface_test', reenters, replace=True, value_binding_factory=Binding)
warnings = []
QtGui.QMessageBox.warning = lambda *args, **kw: warnings.append(args[2])
assert e.apply_changes() is False
assert warnings
assert w.content is old_content and w.get_value('v0') == 7
assert all(not binding.active for binding in created[len(old_bindings):])
e.close()
w.close()
''', tmp_path)


@pytest.mark.parametrize("mode", ["tabs", "radio"])
def test_apply_preserves_tab_by_section_id_and_scroll(tmp_path, mode):
    body = '''
from script_toolbox.model import create_item
sections = [create_item('folder', {'id':'tab'+str(i), 'name':'tab'+str(i), 'props':{'folder_type':'tabs'}}) for i in range(3)]
for section in sections:
    section['items'] = [create_item('string', {'name':section['name']+'_s'+str(i)}) for i in range(30)]
w.config['sections'] = sections
w.rebuild()
w.show()
pump()
tabs = w.content.findChildren(QtGui.QTabWidget)[0]
tabs.setCurrentIndex(2)
pump()
w.scroll.verticalScrollBar().setValue(160)
pump()
position = w.scroll.verticalScrollBar().value()
w.open_interface_editor()
e = w.editor_window
candidate = e.document_controller.snapshot()
candidate['sections'].insert(0, candidate['sections'].pop())
e.document_controller.replace(candidate)
e.populate_tree()
assert e.apply_changes()
pump()
tabs = w.content.findChildren(QtGui.QTabWidget)[0]
assert tabs.currentWidget().section['id'] == 'tab2'
assert w.scroll.verticalScrollBar().value() == position
e.close()
w.close()
# Destroy the large Qt tree while QApplication/event delivery are still alive.
e.deleteLater()
w.deleteLater()
pump()
'''
    if mode == 'radio':
        body = body.replace("'folder_type':'tabs'", "'folder_type':'radio'").replace('QtGui.QTabWidget', 'QtGui.QStackedWidget').replace('tabs.setCurrentIndex(2)', 'tabs.parentWidget().group.button(2).setChecked(True)')
    run_qt(body, tmp_path)


def test_state_scripts_run_only_after_successful_activation(tmp_path):
    run_qt(SETUP + """
toggle = create_item('toggle_button', {'id':'query', 'name':'query',
    'props':{'state_source':'script', 'state_get_script': 'toolbox.query_calls.append(1); state = True'}})
w.query_calls = []
w.config['sections'][0]['items'].append(toggle)
w.rebuild()
w.save()
w.flush_pending_save()
e.close()
w.open_interface_editor()
e = w.editor_window
w.query_calls[:] = []
writer = w.config_store.writer
def fail(*args, **kwargs):
    raise OSError('disk full')
w.config_store.writer = fail
assert e.apply_changes() is False
assert not w.query_calls
w.config_store.writer = writer
assert e.apply_changes()
assert w.query_calls
e.close()
w.close()
""", tmp_path)


def test_container_swap_failure_recovers_and_reload_retries(tmp_path):
    run_qt(SETUP + """
original = w.scroll.setWidget
calls = []
def fail_once(widget):
    calls.append(widget)
    if len(calls) == 1:
        raise RuntimeError('setWidget failed')
    original(widget)
w.scroll.setWidget = fail_once
assert e.apply_changes() is False
assert errors and 'saved' in errors[-1].lower()
assert w.config_store.document is w.config and not w.config_store.dirty
assert not w.content.isEnabled()
assert all(not binding.active for binding in created)
assert load_config()['sections'][0]['items'][0]['ui']['label'] == 'edited'
pump()
w.scroll.setWidget = original
w.reload_config()
assert w.content.isEnabled()
e.close()
w.close()
""", tmp_path)


def test_scroll_frames_remove_inner_borders_with_existing_styles(tmp_path):
    run_qt('''
from script_toolbox.style import STYLE, palette
from script_toolbox.ui.scroll_surface_frames import wrap_scroll_widget
w.open_interface_editor()
e = w.editor_window
e.show()
pump()
for index in range(e.palette_tabs.count()):
    e.palette_tabs.setCurrentIndex(index)
    pump()
    for tree in (e.palette, e.tree, e.preset_palette):
        tree.ensurePolished()
        assert tree.frameWidth() == 0, (tree.objectName(), tree.styleSheet())
        frame = tree._script_toolbox_scroll_surface_frame
        assert frame.frameWidth() == 1
        assert wrap_scroll_widget(tree) is frame
assert "show-decoration-selected: 0" in e.palette.styleSheet()
assert "show-decoration-selected: 0" in e.tree.styleSheet()
# Raw local declarations must also survive adding a selector block.
panel = QtGui.QDialog()
panel.setStyleSheet(STYLE)
layout = QtGui.QVBoxLayout(panel)
control = QtGui.QPlainTextEdit(panel)
control.setStyleSheet("color: " + palette.TEXT_MUTED + "; border: 3px solid " + palette.ACCENT + ";")
layout.addWidget(control)
frame = wrap_scroll_widget(control)
panel.show()
pump()
assert control.frameWidth() == 0
assert control.palette().color(QtGui.QPalette.Text).name() == palette.TEXT_MUTED
assert frame.frameWidth() == 1
panel.close()
panel.deleteLater()
e.reject()
w.close()
w.deleteLater()
pump()
''', tmp_path)
