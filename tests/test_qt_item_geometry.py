"""Rendered item geometry, including the String/Color regression."""
from test_qt_lifecycle import run_qt, pytestmark as qt_mark

pytestmark = qt_mark


def test_inline_items_share_height_and_centerline(tmp_path):
    run_qt('''
from script_toolbox.model.items import create_item
from script_toolbox.style.metrics import SINGLE_LINE_CONTROL_HEIGHT
from script_toolbox.style.metrics import RUNTIME_ICON_CHROME_SIZE
from script_toolbox.ui.color_control import ColorControl
kinds = ('string', 'integer', 'float', 'menu', 'color', 'button',
         'toggle_button', 'checkbox', 'label', 'icon', 'toggle_icon', 'field')
rows = []
for kind in kinds:
    props = {'display_mode': 'single', 'multiple': False} if kind == 'field' else {}
    if kind == 'color':
        props = {'show_rgb': False, 'show_hex': True}
    children = [create_item('string', {'name': 'reference_' + kind, 'ui': {'show_label': False, 'width_mode': 'stretch'}}),
                create_item(kind, {'name': 'subject_' + kind, 'ui': {'show_label': False, 'width_mode': 'stretch'}, 'props': props})]
    rows.append(create_item('row', {'name': 'row_' + kind, 'props': {'vertical_alignment': 'top'}, 'items': children}))
w.config['sections'][0]['items'] = rows
w.rebuild()
w.resize(900, 700)
w.show()
pump()
for kind in kinds:
    reference = w.value_widgets[w.find_item('reference_' + kind)['id']].root.findChild(QtGui.QLineEdit)
    row = reference.parentWidget().parentWidget()
    # Row always contains the reference and subject root, in that order.
    root = row.layout().itemAt(1).widget()
    assert root.height() == reference.height() == SINGLE_LINE_CONTROL_HEIGHT, (kind, root.height(), reference.height())
    if kind == 'color':
        color = root.findChild(ColorControl)
        for field in (color.swatch, color.hex_edit):
            assert field.height() == reference.height(), (field.objectName(), field.height(), reference.height())
            assert field.mapTo(w, QtCore.QPoint(0, 0)).y() == reference.mapTo(w, QtCore.QPoint(0, 0)).y()
        color.configure(True, '0-255', True)
        pump()
        for field in color.channels:
            assert field.height() == reference.height(), (field.objectName(), field.height(), reference.height())
    if kind in ('icon', 'toggle_icon'):
        target = root.findChild(QtGui.QWidget, 'RuntimeIconFeedback')
        assert target.height() == SINGLE_LINE_CONTROL_HEIGHT, (kind, target.height())
# Explicit tall artwork and multiline content still own their size.
large = create_item('icon', {'name': 'large_icon', 'props': {'height': 64, 'width': 64}})
text = create_item('text', {'name': 'multiline', 'props': {'text': 'one\\ntwo\\nthree'}})
image = create_item('image', {'name': 'preview', 'props': {'height': 120}})
w.config['sections'][0]['items'] = [large, text, image]
w.rebuild()
pump()
assert any(label.height() == 64 + RUNTIME_ICON_CHROME_SIZE for label in w.findChildren(QtGui.QLabel))
w.close()
w.deleteLater()
pump()
''', tmp_path)
