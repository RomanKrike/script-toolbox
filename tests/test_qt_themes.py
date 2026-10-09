"""Real Qt verifies theme previews, rollback, persistence and rebuilt controls."""
from test_qt_lifecycle import run_qt, pytestmark as qt_mark

pytestmark = qt_mark


def test_theme_preview_cancel_and_scoped_widgets(tmp_path):
    run_qt('''
from script_toolbox.core import themes
from script_toolbox.style.themes import controller, color_map
from script_toolbox.style import palette
mapping = color_map(themes.DEFAULT_COLORS)
assert all(source == target for source, target in mapping.items())
changed = dict(themes.DEFAULT_COLORS, input="#202020")
mapping = color_map(changed)
assert mapping[palette.INPUT_BG] == "#202020"
assert mapping[palette.WINDOW_BG] == palette.WINDOW_BG
assert themes.builtins()[0] == themes.theme()
from script_toolbox.ui.settings_dialog import SettingsDialog
from script_toolbox.model import create_item
external = QtGui.QWidget()
external.setStyleSheet('background: #292b2e;')
w.show()
w.open_interface_editor()
d = SettingsDialog(w)
d.category_list.setCurrentRow(1)
d.show()
pump()
p = d.appearance_page
assert p.actions.isVisible()
assert p.actions.mapTo(p, QtCore.QPoint(0, 0)).y() == p.theme_combo.mapTo(p, QtCore.QPoint(0, 0)).y()
assert p.actions.geometry().left() > p.theme_combo.geometry().right()
assert p.theme_section.objectName() == 'SimpleSectionGroupBox'
assert p.colors_section.objectName() == 'SimpleSectionGroupBox'
assert all(p.colors_section.isAncestorOf(control) for control in p.controls.values())
assert len(set(control.width() for control in p.controls.values())) == 1
assert len(set(control.mapTo(p, QtCore.QPoint(0, 0)).x() for control in p.controls.values())) == 1
assert p.theme_combo.currentText() == themes.DEFAULT_NAME
p.controls['input']._commit([32 / 255.0] * 3)
pump()
assert p.theme_combo.currentText() == 'Custom'
assert themes.load_state()[0]['name'] == themes.DEFAULT_NAME
assert '#202020' in w.styleSheet()
assert '#202020' in w.editor_window.styleSheet()
assert external.styleSheet() == 'background: #292b2e;'
w.config['sections'][0]['items'] = [create_item('string', {'name': 'theme_input'})]
w.rebuild()
pump()
field = w.content.findChildren(QtGui.QLineEdit)[0]
assert field is not None
assert field.palette().color(QtGui.QPalette.Base).name() == '#202020', field.palette().color(QtGui.QPalette.Base).name()
p.controls['input']._commit([40 / 255.0] * 3)
pump()
p.controls['input']._commit([32 / 255.0] * 3)
pump()
assert field.palette().color(QtGui.QPalette.Base).name() == '#202020'
d.reject()
pump()
assert controller().active == themes.theme()
assert field.palette().color(QtGui.QPalette.Base).name() == '#27292c'
assert '#202020' not in w.styleSheet()
w.editor_window.close()
w.close()
w.deleteLater()
pump()
''', tmp_path)


def test_theme_save_named_copy_import_export_and_restart(tmp_path):
    run_qt('''
from script_toolbox.core import themes
from script_toolbox.style.themes import controller
from script_toolbox.ui.settings_dialog import SettingsDialog
from script_toolbox.style.builtin_icons import item_type_icon
d = SettingsDialog(w)
p = d.appearance_page
p.controls['text']._commit([0.6, 0.7, 0.8])
original = themes.builtins()[0]
old_get_text = QtGui.QInputDialog.getText
QtGui.QInputDialog.getText = lambda *args, **kwargs: ('My colors', True)
p.add_theme_button.click()
d._save()
QtGui.QInputDialog.getText = old_get_text
active, saved = themes.load_state()
assert active['name'] == 'My colors'
assert saved == [active]
assert themes.builtins()[0] == original
assert controller().active == active
controller().deleteLater()
pump()
del app._script_toolbox_themes
assert controller().active == active
controller().register(w)
d2 = SettingsDialog(w)
p2 = d2.appearance_page
assert p2.theme_combo.currentText() == 'My colors'
icon = item_type_icon('color').pixmap(32, 32).toImage()
opaque = [icon.pixelColor(x, y) for y in range(32) for x in range(32) if icon.pixelColor(x, y).alpha() == 255]
assert opaque and all(c.name() == active['colors']['text'] for c in opaque)
assert [p2.theme_combo.itemText(i) for i in range(p2.theme_combo.count())].count('My colors') == 1
path = os.path.join(os.path.expanduser('~'), 'colors.json')
old_export = QtGui.QFileDialog.getSaveFileName
old_import = QtGui.QFileDialog.getOpenFileName
QtGui.QFileDialog.getSaveFileName = lambda *args: (path, '')
p2.export_theme()
assert themes.read_theme(path) == active
QtGui.QFileDialog.getOpenFileName = lambda *args: (path, '')
p2.import_theme()
assert p2.current['name'] == 'My colors (2)'
assert themes.load_state()[1] == [active]
p2.reset_theme()
assert p2.current == original
d2.reject()
pump()
assert controller().active == active
assert themes.load_state() == (active, [active])
QtGui.QFileDialog.getSaveFileName = old_export
QtGui.QFileDialog.getOpenFileName = old_import
w.close()
w.deleteLater()
pump()
''', tmp_path)


def test_theme_copy_delete_and_cancel_are_staged(tmp_path):
    run_qt('''
from script_toolbox.core import themes
from script_toolbox.style.themes import controller
from script_toolbox.ui.settings_dialog import SettingsDialog
d = SettingsDialog(w)
d.show()
pump()
p = d.appearance_page
assert not p.remove_theme_button.isEnabled()
original = themes.builtins()[0]
old_get_text = QtGui.QInputDialog.getText
QtGui.QInputDialog.getText = lambda *args, **kwargs: ('Studio', True)
p.add_theme_button.click()
assert p.current['name'] == 'Studio'
assert p.remove_theme_button.isEnabled()
assert themes.load_state()[1] == []
assert themes.builtins()[0] == original
d._save()
active, saved = themes.load_state()
assert active['name'] == 'Studio' and saved == [active]
d2 = SettingsDialog(w)
d2.show()
pump()
p2 = d2.appearance_page
assert p2.remove_theme_button.isEnabled()
p2.remove_theme_button.click()
assert p2.current == original
assert not p2.remove_theme_button.isEnabled()
assert themes.load_state() == (active, saved)
d2.reject()
assert controller().active == active
d3 = SettingsDialog(w)
d3.show()
pump()
p3 = d3.appearance_page
QtGui.QInputDialog.getText = lambda *args, **kwargs: ('', False)
p3.add_theme_button.click()
assert p3.current == active and p3.saved == saved
p3.remove_theme_button.click()
d3._save()
assert themes.load_state() == (original, [])
d4 = SettingsDialog(w)
d4.show()
pump()
p4 = d4.appearance_page
p4.controls['input']._commit([32 / 255.0] * 3)
def unexpected_prompt(*args, **kwargs):
    raise AssertionError('Save should not ask for a name; + saves a named copy')
QtGui.QInputDialog.getText = unexpected_prompt
d4._save()
assert themes.load_state()[0]['name'] == 'Custom'
assert themes.load_state()[1] == []
QtGui.QInputDialog.getText = old_get_text
w.close()
w.deleteLater()
pump()
''', tmp_path)
