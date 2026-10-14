from test_qt_lifecycle import run_qt, pytestmark as qt_mark

pytestmark = qt_mark


def test_color_runtime_sync_precision_events_ranges_and_dialog(tmp_path):
    run_qt('''
from script_toolbox.model.items import create_item
from PySide6.QtTest import QTest
original = [0.123456789, 0.234567891, 0.345678912]
item = create_item('color', {'name': 'tint', 'props': {'value': original}})
w.config['sections'][0]['items'] = [item]
w.rebuild()
w.show()
pump()
binding = w.value_widgets[item['id']]
root = binding.root
control = root.color_control
surface = w.runtime_surface
events = []
w._run_on_change = lambda item, old, new: events.append((old, new))
assert control.value() == original
assert control.hex_edit.text() == '#1F3C58'
control.hex_edit.editingFinished.emit()
assert w.get_value('tint') == original and not events
w.item('tint').set(rgb_range='0-255')
assert binding.root is root and w.runtime_surface is surface
assert control.channels[0].maximum() == 255
assert control.channels[0].value() == 31
assert w.get_value('tint') == original and not events
control.channels[0].setValue(128)
assert w.get_value('tint') == [128 / 255.0, original[1], original[2]]
assert len(events) == 1
control.hex_edit.setFocus()
control.hex_edit.selectAll()
QTest.keyClicks(control.hex_edit, '#00FF80')
QTest.keyClick(control.hex_edit, QtCore.Qt.Key_Return)
assert w.get_value('tint') == [0, 1, 128 / 255.0]
assert len(events) == 2
control.hex_edit.setText('#GGGGGG')
control.hex_edit.editingFinished.emit()
assert control.hex_edit.text() == '#00FF80' and len(events) == 2
w.item('tint').set(show_rgb=False, show_hex=False)
assert all(spin.isHidden() for spin in control.channels)
assert control.hex_edit.isHidden() and not control.swatch.isHidden()
pump()
from script_toolbox.style.metrics import SINGLE_LINE_CONTROL_HEIGHT
assert control.swatch.height() == SINGLE_LINE_CONTROL_HEIGHT
assert control.swatch.x() < 10
assert root is w.value_widgets[item['id']].root and len(events) == 2
w.item('tint').set(value=original, show_rgb=True, show_hex=True, rgb_range='0-1')
assert control.value() == original and control.channels[0].decimals() == 3
assert len(events) == 3
assert not control.hex_edit.isHidden()
chosen = QtGui.QColor.fromRgbF(0.1, 0.4, 0.9)
calls = []
QtGui.QColorDialog.getColor = lambda initial, parent, title: (calls.append(initial), chosen)[1]
control.swatch.click()
assert w.get_value('tint') == [chosen.redF(), chosen.greenF(), chosen.blueF()]
assert len(calls) == 1 and len(events) == 4
QtGui.QColorDialog.getColor = lambda *args: QtGui.QColor()
control.swatch.click()
assert len(events) == 4
w.item('tint').set(enabled=False)
assert not control.swatch.isEnabled()
assert not control.hex_edit.isEnabled()
# Disposing the old binding must disconnect its compound control too.
old = control
w.rebuild()
old.channels[0].setValue(0.8)
assert len(events) == 4
w.close()
w.deleteLater()
pump()
''', tmp_path)


def test_color_inspector_options_preserve_value(tmp_path):
    run_qt('''
from script_toolbox.model.items import create_item
from script_toolbox.ui.properties.basic import ColorPropertyEditor
item = create_item('color', {'name': 'tint'})
assert item['props']['show_rgb'] and item['props']['show_hex']
assert item['props']['rgb_range'] == '0-1'
original = [0.123456789, 0.234567891, 0.345678912]
item['props']['value'] = original[:]
editor = ColorPropertyEditor()
changes = []
editor.changed.connect(lambda: changes.append(True))
editor.bind(item)
assert not changes
editor.rgb_range_combo.setCurrentIndex(1)
assert item['props']['rgb_range'] == '0-255'
assert item['props']['value'] == original
assert changes == [True]
editor.show_rgb_check.setChecked(False)
editor.show_hex_check.setChecked(False)
assert not item['props']['show_rgb'] and not item['props']['show_hex']
assert not editor.rgb_range_combo.isEnabled()
assert item['props']['value'] == original
editor.bind(item)
assert len(changes) == 3 and editor.color_control.value() == original
editor.show_rgb_check.setChecked(True)
editor.color_control.channels[2].setValue(255)
assert item['props']['value'] == [original[0], original[1], 1]
editor.deleteLater()
w.close()
w.deleteLater()
pump()
''', tmp_path)
