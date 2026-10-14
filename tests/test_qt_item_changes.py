from test_qt_lifecycle import run_qt, pytestmark as qt_mark

pytestmark = qt_mark


def test_item_set_updates_existing_widgets_events_and_expressions(tmp_path):
    run_qt('''
from script_toolbox.model.items import create_item, normalize_document
image = create_item('image', {'name': 'preview'})
check = create_item('checkbox', {'name': 'switch'})
menu = create_item('menu', {'name': 'shots', 'props': {'items': ['a', 'b'], 'value': 'a'}})
number = create_item('integer', {'name': 'amount', 'props': {'value': 50, 'max': 100}})
floating = create_item('float', {'name': 'ratio', 'props': {'value': 0.5, 'min': 0, 'max': 1, 'show_slider': True}})
button = create_item('button', {'name': 'next', 'ui': {
    'enabled_expression_enabled': True, 'enabled_expression': 'switch'}})
folders = [create_item('folder', {'name': 'first', 'props': {'folder_type': 'tabs'}}),
           create_item('folder', {'name': 'second', 'props': {'folder_type': 'tabs'},
             'items': [image, check, menu, number, floating, button]})]
w.config = normalize_document({'sections': folders})
w.rebuild()
w.show()
tabs = w.content.findChild(QtGui.QTabWidget)
tabs.setCurrentIndex(1)
pump()
surface = w.runtime_surface
manager = surface.context.conditions
roots = dict((item['name'], manager.widgets[item['id']][0]) for item in [image, check, menu, number, floating, button])
handle = w.item('preview')
events = []
w._run_on_change = lambda item, old, new: events.append((item['name'], old, new))
for color in ('red', 'blue'):
    path = os.path.join(os.path.expanduser('~'), color + '.png')
    pixmap = NativeGui.QPixmap(12, 12)
    pixmap.fill(QtGui.QColor(color))
    assert pixmap.save(path)
    change = handle.set(source=path, width=100, height=60, tooltip=color)
    assert change.changed
    root = roots['preview']
    assert root.image_label.pixmap().toImage().pixelColor(0, 0).name() == QtGui.QColor(color).name()
    assert root.image_label.width() == 100 and root.image_label.height() == 60
    assert root.toolTip() == color
    assert root.filename_label.text() == color + '.png'
    assert not root.filename_label.isHidden()
    assert w.runtime_surface is surface and tabs.currentIndex() == 1
handle.set(source='/missing/image.png')
assert roots['preview'].image_label.text() == 'Image' and roots['preview'].image_label.pixmap().isNull()
handle.set(show_filename=False)
assert roots['preview'].filename_label.isHidden()
assert roots['preview'].height() == 60 + 24
handle.set(source='', show_filename=True)
assert roots['preview'].filename_label.isHidden()
handle.set(source='C:/previews/very_long_name_' + 'x' * 100 + '.png')
assert roots['preview'].filename_label.filename.startswith('very_long_name_')
assert len(roots['preview'].filename_label.text()) < len(roots['preview'].filename_label.filename)
assert not events
w.item('switch').set(value=True, label='Show preview')
assert roots['switch'].isChecked()
assert roots['switch'].text() == 'Show preview'
assert roots['next'].isEnabled()
assert len(events) == 1
assert not w.item('switch').set(value=True).changed
assert len(events) == 1
w.item('next').set(enabled=False)
assert w.find_item('next')['ui']['enabled_expression_enabled'] is True
assert roots['next'].isEnabled()  # enabled expression evaluates to true
w.item('next').set(enabled_expression_enabled=False)
assert not roots['next'].isEnabled()
combo = roots['shots'].findChild(QtGui.QComboBox)
w.item('shots').set(items=['c', 'd'], value='d')
assert combo.currentText() == 'd' and combo.count() == 2
assert manager.widgets[menu['id']][0] is roots['shots']
spin = roots['amount'].findChild(QtGui.QSpinBox)
w.item('amount').set(max=20)
assert spin.maximum() == 20 and spin.value() == 20
assert ('amount', 50, 20) in events
w.item('ratio').set(max=10)
slider = roots['ratio'].findChild(QtGui.QSlider)
assert slider is not None
slider.setValue(5000)
assert w.item('ratio').value == 5.0
before = w.item('amount').value
try:
    w.item('amount').set(value='bad', label='Broken')
    assert False
except ValueError:
    pass
assert w.item('amount').value == before
assert w.item('amount').label != 'Broken'
checkbox = roots['switch']
count = len(events)
checkbox.setChecked(False)
assert w.item('switch').value is False and len(events) == count + 1
assert w.runtime_surface is surface and tabs.currentIndex() == 1
w.close()
w.deleteLater()
pump()
''', tmp_path)


def test_targeted_replacement_and_handle_survive_runtime_rebuild(tmp_path):
    run_qt('''
from script_toolbox.model.items import create_item, normalize_document
field = create_item('string', {'name': 'text'})
other = create_item('image', {'name': 'other'})
w.config = normalize_document({'sections': [create_item('folder', {'items': [field, other]})]})
w.rebuild()
w.show()
pump()
surface = w.runtime_surface
handle = w.item('text')
other_root = surface.context.conditions.widgets[other['id']][0]
old = surface.context.conditions.widgets[field['id']][0]
handle.set(show_label=False)
pump()
new = surface.context.conditions.widgets[field['id']][0]
assert old is not new and w.runtime_surface is surface
assert surface.context.conditions.widgets[other['id']][0] is other_root
handle.set(value='after replacement')
assert new.findChild(QtGui.QLineEdit).text() == 'after replacement'
w.rebuild()
handle.set(value='after rebuild')
assert handle.value == 'after rebuild'
events = []
def changed(item, old, new):
    events.append(new)
    if new == 'first':
        w.item('text').set(value='second')
w._run_on_change = changed
handle.set(value='first')
assert events == ['first', 'second'] and handle.value == 'second'
w.close()
w.deleteLater()
pump()
''', tmp_path)


def test_image_filename_property_editor_and_mouse_binding(tmp_path):
    run_qt('''
from script_toolbox.model.items import create_item, normalize_document
from script_toolbox.ui.image_item import ImagePropertyEditor
image = create_item('image', {'name': 'preview', 'props': {'source': 'C:\\\\shots\\\\view.png'}})
editor = ImagePropertyEditor()
editor.load_specific(image['props'])
assert editor.show_filename.isChecked()
editor.show_filename.setChecked(False)
props = dict(image['props'])
editor.write_specific(props)
assert props['show_filename'] is False
w.config = normalize_document({'sections': [create_item('folder', {'items': [image]})]})
w.rebuild()
w.show()
pump()
root = w.runtime_surface.context.conditions.widgets[image['id']][0]
assert root.filename_label.filename == 'view.png'
assert root.image_label._script_toolbox_binding_item == image['id']
assert root.filename_label._script_toolbox_binding_item == image['id']
w.item('preview').set(show_filename=False)
assert root.filename_label.isHidden()
editor.deleteLater()
w.close()
w.deleteLater()
pump()
''', tmp_path)
