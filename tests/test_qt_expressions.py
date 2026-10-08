from test_qt_lifecycle import run_qt, pytestmark as qt_mark

pytestmark = qt_mark


def test_runtime_visibility_enabled_and_api_without_rebuild(tmp_path):
    run_qt('''
from script_toolbox.model.items import create_item, normalize_document
check = create_item('checkbox', {'name': 'use_preview', 'props': {'value': True}})
path = create_item('string', {'name': 'preview_path', 'ui': {
    'enabled_expression_enabled': True, 'enabled_expression': 'use_preview'}})
folder = create_item('folder', {'name': 'tools', 'items': [check, path], 'ui': {
    'visible_expression_enabled': True, 'visible_expression': 'use_preview'}})
w.config = normalize_document({'sections': [folder]})
w.rebuild()
w.show()
pump()
manager = w.runtime_surface.context.conditions
surface = w.runtime_surface
root = manager.widgets[path['id']][0]
folder_root = manager.widgets[folder['id']][0]
checkbox = manager.widgets[check['id']][0].findChild(QtGui.QCheckBox)
if checkbox is None:
    checkbox = manager.widgets[check['id']][0]
checkbox.setChecked(False)
pump()
assert w.get_value('use_preview') is False
assert not root.isEnabled() and folder_root.isHidden()
w.set_value('use_preview', True)
pump()
assert root.isEnabled() and not folder_root.isHidden()
assert w.runtime_surface is surface
w.disable('tools')
assert not root.isEnabled(), ('parent state', folder_root.isEnabled(), w.find_item('tools')['ui']['enabled'])
w.enable('preview_path')
assert not root.isEnabled(), ('parent state', folder_root.isEnabled(), w.find_item('tools')['ui']['enabled'])
w.enable('tools')
assert root.isEnabled()
w.set_visible('preview_path', False)
assert root.isHidden() and w.get_value('preview_path') == ''
w.close()
w.deleteLater()
pump()
''', tmp_path)


def test_expression_inspector_editing_rename_and_reserved_words(tmp_path):
    run_qt('''
from script_toolbox.model.items import create_item, normalize_document
from script_toolbox.ui.properties.registry import create_editor
from script_toolbox.core.editor_document import EditorDocumentController
check = create_item('checkbox', {'name': 'use_preview', 'props': {'value': True}})
path = create_item('string', {'name': 'preview_path'})
w.config = normalize_document({'sections': [create_item('folder', {'name': 'tools', 'items': [check, path]})]})
w.rebuild()
path = w.find_item('preview_path')
panel = create_editor('string', toolbox=w)
panel.expression_document = w.config
panel.bind(path)
panel.show()
control = panel.expression_controls['enabled']
control.editor.setPlainText('use_preview')
control.fx.setChecked(True)
pump()
assert path['ui']['enabled_expression'] == 'use_preview'
assert 'Result: true' == control.result.text()
control.editor.setPlainText('missing')
assert 'Unknown parameter' in control.result.text()
control.fx.setChecked(False)
assert control.editor.isHidden() and control.base.isEnabled()
assert path['ui']['enabled_expression'] == 'missing'
panel.name_edit.setText('IF')
panel._control_changed()
assert path['name'] == 'preview_path'
assert not panel.name_error.isHidden()
panel.name_edit.setText('use_preview')
panel._control_changed()
assert path['name'] == 'preview_path'
panel.name_edit.setText('new_path')
panel._control_changed()
assert path['name'] == 'new_path'
panel.close()
panel.deleteLater()
w.close()
w.deleteLater()
pump()
''', tmp_path)


def test_tab_and_radio_pages_disappear_and_return(tmp_path):
    run_qt('''
from script_toolbox.model.items import create_item, normalize_document
for mode in ('tabs', 'radio'):
    check = create_item('checkbox', {'name': 'use_preview', 'props': {'value': True}})
    controls = create_item('folder', {'name': 'controls', 'items': [check]})
    first = create_item('folder', {'name': 'first', 'props': {'folder_type': mode}, 'ui': {
        'visible_expression_enabled': True, 'visible_expression': 'use_preview'}})
    second = create_item('folder', {'name': 'second', 'props': {'folder_type': mode}})
    w.config = normalize_document({'sections': [controls, first, second]})
    w.rebuild()
    w.show()
    pump()
    if mode == 'tabs':
        tabs = w.content.findChild(QtGui.QTabWidget)
        assert tabs.count() == 2
        second_page = tabs.widget(1)
        tabs.setCurrentIndex(1)
    else:
        stack = w.content.findChild(QtGui.QStackedWidget)
        group = stack.parentWidget().group
    w.set_value('use_preview', False)
    pump()
    if mode == 'tabs':
        assert tabs.count() == 1 and tabs.widget(0) is second_page
    else:
        assert group.button(0).isHidden() and stack.currentIndex() == 1
    w.set_value('use_preview', True)
    if mode == 'tabs':
        assert tabs.count() == 2 and tabs.widget(1) is second_page
        assert tabs.currentWidget() is second_page
    else:
        assert not group.button(0).isHidden()
        w.disable('first')
        w.disable('second')
        assert not stack.isHidden()
        assert not stack.currentWidget().isEnabled()
w.close()
w.deleteLater()
pump()
''', tmp_path)
