import pytest
from test_qt_lifecycle import run_qt, QT_AVAILABLE

pytestmark = pytest.mark.skipif(not QT_AVAILABLE, reason="Requires real Qt")

SETUP = '''
from script_toolbox.model import create_item
from script_toolbox.model.fields import IntField
from script_toolbox.model.item_registry import ItemTypeDefinition, register_item_type
from script_toolbox.ui.runtime_value_sync import ValueBinding
from script_toolbox.ui import register_runtime_renderer
register_item_type(ItemTypeDefinition('counter_test', 'Counter', fields={'value':IntField(default=0)}, capabilities=('has_value',)))
disposed, created = [], []
class CounterBinding(ValueBinding):
    def __init__(self, root, owner, item):
        ValueBinding.__init__(self, root)
        self.toolbox, self.item_id = owner.toolbox, item['id']
        self.connect(root.button.clicked, self.clicked)
        created.append(self)
    def clicked(self):
        self.toolbox.store_value(self.item_id, self.toolbox.get_value(self.item_id) + 1)
    def sync(self, item):
        self.root.label.setText(str(item['props']['value']))
        return True
    def dispose(self):
        if self.active:
            disposed.append(self)
        ValueBinding.dispose(self)
        self.toolbox = None
def render(owner, item, compact=False):
    root = QtGui.QWidget()
    layout = QtGui.QVBoxLayout(root)
    root.label = QtGui.QLabel(str(item['props']['value']))
    root.button = QtGui.QPushButton('Increment')
    root.distractor = QtGui.QLineEdit('unrelated')
    for control in (root.label, root.button, root.distractor):
        layout.addWidget(control)
    return root
register_runtime_renderer('counter_test', render, value_binding_factory=CounterBinding)
w.config['sections'][0]['items'] = [create_item('counter_test', {'id':'counter', 'name':'counter'})]
w.rebuild()
binding = w.value_widgets['counter']
'''


def test_custom_binding_updates_model_and_ui_without_control_guessing(tmp_path):
    run_qt(SETUP + '''
w.store_value('counter', 12)
assert binding.root.label.text() == '12'
assert binding.root.distractor.text() == 'unrelated'
binding.root.button.click()
assert w.get_value('counter') == 13
assert binding.root.label.text() == '13'
assert len(created) == 1
w.close()
assert binding in disposed and not binding.active
''', tmp_path)


def test_rebuild_replacement_and_close_dispose_owned_connections(tmp_path):
    run_qt(SETUP + '''
old_button = binding.root.button
w.rebuild()
assert disposed == [binding]
old_button.click()
assert w.get_value('counter') == 0
current = w.value_widgets['counter']
current.root.button.click()
assert w.get_value('counter') == 1
register_runtime_renderer('counter_test', render, replace=True, value_binding_factory=CounterBinding)
w.rebuild()
assert disposed == [binding, current]
latest = w.value_widgets['counter']
latest.root.button.click()
assert w.get_value('counter') == 2
w.close()
assert disposed == [binding, current, latest]
''', tmp_path)


def test_replacement_without_factory_does_not_guess_value_controls(tmp_path):
    run_qt(SETUP + '''
roots = []
def replacement(owner, item, compact=False):
    root = QtGui.QLineEdit('display only')
    roots.append(root)
    return root
register_runtime_renderer('counter_test', replacement, replace=True)
w.rebuild()
assert 'counter' not in w.value_widgets
w.store_value('counter', 8)
assert roots[-1].text() == 'display only'
w.close()
''', tmp_path)


def test_sync_error_is_logged_and_binding_is_disposed(tmp_path):
    run_qt(SETUP + '''
import logging
messages = []
class Capture(logging.Handler):
    def emit(self, record):
        messages.append(record.getMessage())
logger = logging.getLogger('script_toolbox')
handler = Capture()
logger.addHandler(handler)
def fail(item):
    raise RuntimeError('broken custom adapter')
binding.sync = fail
w.store_value('counter', 3)
assert w.get_value('counter') == 3
assert 'counter' not in w.value_widgets
assert not binding.active
assert any('Value binding sync failed for counter' in m for m in messages)
logger.removeHandler(handler)
w.close()
''', tmp_path)


def test_destroyed_root_disposes_binding_and_reentrant_sync_is_guarded(tmp_path):
    run_qt(SETUP + '''
calls = []
def sync(item):
    calls.append(item['props']['value'])
    assert w.sync_runtime_value('counter') is False
    return True
binding.sync = sync
w.store_value('counter', 4)
assert calls == [4]
binding.root.deleteLater()
pump()
assert binding in disposed and not binding.active
assert w.sync_runtime_value('counter') is False
assert 'counter' not in w.value_widgets
w.close()
''', tmp_path)


def test_builtin_callbacks_do_not_write_after_rebuild(tmp_path):
    run_qt('''
from script_toolbox.model import create_item
w.config['sections'][0]['items'] = [create_item(kind, {'id':kind, 'name':kind})
    for kind in ('string', 'integer', 'float', 'checkbox', 'menu', 'color')]
w.rebuild()
old = dict(w.value_widgets)
line = old['string'].root.findChildren(QtGui.QLineEdit)[0]
integer = old['integer'].root.findChildren(QtGui.QSpinBox)[0]
floating = old['float'].root.findChildren(QtGui.QDoubleSpinBox)[0]
check = old['checkbox'].root
menu = old['menu'].root.findChildren(QtGui.QComboBox)[0]
w.store_value('integer', 7)
w.store_value('float', 0.5)
w.store_value('color', [0.1, 0.2, 0.3])
assert integer.value() == 7 and floating.value() == 0.5
w.rebuild()
assert all(not binding.active for binding in old.values())
line.setText('stale')
line.editingFinished.emit()
integer.setValue(99)
floating.setValue(99.5)
check.setChecked(True)
menu.setCurrentIndex(1)
assert w.get_value('string') == ''
assert w.get_value('integer') == 7
assert w.get_value('float') == 0.5
assert w.get_value('checkbox') is False
assert w.get_value('menu') == 'Option 1'
w.close()
''', tmp_path)
