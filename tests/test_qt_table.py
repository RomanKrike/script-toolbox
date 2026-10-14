"""Real Qt spreadsheet controls share normal renderers, events and theme scope."""
from test_qt_lifecycle import run_qt, pytestmark as qt_mark

pytestmark = qt_mark


def test_table_cells_api_events_and_row_lifetime(tmp_path):
    run_qt('''
from script_toolbox.model import create_item
from script_toolbox.model.table import new_row
from script_toolbox.ui.table_runtime import Spreadsheet
columns = [create_item('string', {'name': 'shot', 'ui': {'label': 'Shot'}}),
           create_item('integer', {'name': 'count', 'props': {'min': 0, 'max': 100}}),
           create_item('color', {'name': 'tint', 'props': {'show_rgb': False}}),
           create_item('checkbox', {'name': 'enabled'}),
           create_item('button', {'name': 'open', 'bindings': [{'event': 'click', 'handler': 'script',
             'script': 'toolbox._table_test_event = (row_id, row_index, column, row["shot"])'}]})]
table = create_item('table', {'name': 'shots', 'items': columns,
                            'props': {'rows': [new_row({columns[0]['id']: 'sh010'})]}})
w.config['sections'][0]['items'] = [table]
w.rebuild()
w.show()
pump()
view = w.content.findChild(Spreadsheet)
assert view and view.grid.rowCount() == 1 and view.grid.columnCount() == 5
first_cell = view.grid.cellWidget(0, 0).findChild(QtGui.QLineEdit)
first_cell.setText('sh020')
first_cell.editingFinished.emit()
assert w.item('shots').table().get_cell(0, 'shot') == 'sh020'
assert first_cell is view.grid.cellWidget(0, 0).findChild(QtGui.QLineEdit)
api = w.item('shots').table()
api.set_cell(0, 'count', 42)
assert view.grid.cellWidget(0, 1).findChild(QtGui.QSpinBox).value() == 42
button = view.grid.cellWidget(0, 4).findChild(QtGui.QPushButton)
button.click()
assert w._table_test_event == (table['props']['rows'][0]['id'], 0, 'open', 'sh020')
old_id = table['props']['rows'][0]['id']
view.add_button.click()
pump()
assert view.grid.rowCount() == 2
assert table['props']['rows'][0]['id'] == old_id
view.grid.setCurrentCell(0, 0)
view.remove_button.click()
pump()
assert view.grid.rowCount() == 1 and table['props']['rows'][0]['id'] != old_id
assert len(w.value_widgets) == 0, w.value_widgets
w.close()
w.deleteLater()
pump()
''', tmp_path)


def test_table_editor_column_tree_and_initial_rows_are_isolated(tmp_path):
    run_qt('''
from script_toolbox.model import create_item
from script_toolbox.model.table import new_row
from script_toolbox.ui.table_runtime import Spreadsheet, PreviewTableContext
from script_toolbox.ui.properties.table import TablePropertyEditor
column = create_item('string', {'name': 'shot'})
table = create_item('table', {'name': 'shots', 'items': [column], 'props': {'rows': [new_row()]}})
w.config['sections'][0]['items'] = [table]
w.rebuild()
w.open_interface_editor()
pump()
e = w.editor_window
node = e.tree_item_by_id(table['id'])
assert node.childCount() == 1 and node.child(0).childCount() == 0
e.tree.setCurrentItem(node)
pump()
assert isinstance(e.current_property_editor, TablePropertyEditor)
e.tree.setCurrentItem(e.tree_item_by_id(column['id']))
pump()
inspector = e.current_property_editor
assert inspector.row_width_mode.isEnabled()
inspector.row_width_mode.setCurrentIndex(2)
inspector.row_width.setValue(180)
inspector.write_to_item()
assert e.document_controller.find_by_id(column['id'])['ui']['width'] == 180
context = PreviewTableContext(table)
context.widget = Spreadsheet(context, table, preview=True)
context.widget.handle().set_cell(0, 'shot', 'edited')
context.widget.add_button.click()
assert len(context.widget.current_item()['props']['rows']) == 2
assert len(table['props']['rows']) == 1
assert w.item('shots').table().get_cell(0, 'shot') == ''
context.widget.deleteLater()
e.close()
w.close()
w.deleteLater()
pump()
''', tmp_path)


def test_table_column_delete_undo_theme_and_column_updates(tmp_path):
    run_qt('''
from script_toolbox.model import create_item
from script_toolbox.model.table import new_row
from script_toolbox.ui.table_runtime import Spreadsheet
from script_toolbox.core import themes
from script_toolbox.style.themes import controller
columns = [create_item('string', {'name': 'shot'}), create_item('integer', {'name': 'count'})]
table = create_item('table', {'name': 'shots', 'items': columns,
    'props': {'rows': [new_row({columns[0]['id']: 'sh010', columns[1]['id']: 20})]}})
w.config['sections'][0]['items'] = [table]
w.rebuild()
w.show()
pump()
view = w.content.findChild(Spreadsheet)
controller().apply(themes.theme('Custom', dict(themes.DEFAULT_COLORS, input='#202020')))
pump()
assert view.grid.palette().color(QtGui.QPalette.Base).name() == '#202020'
line = view.grid.cellWidget(0, 0).findChild(QtGui.QLineEdit)
assert line.palette().color(QtGui.QPalette.Base).name() == '#202020'
w.item('count').set(max=10)
pump()
assert w.item('shots').table().get_cell(0, 'count') == 10
assert view.grid.cellWidget(0, 1).findChild(QtGui.QSpinBox).value() == 10
w.item('count').set(enabled=False)
pump()
assert not view.grid.cellWidget(0, 1).isEnabled()
w.item('count').set(enabled=True)
w.open_interface_editor()
pump()
e = w.editor_window
e.tree.setCurrentItem(e.tree_item_by_id(columns[0]['id']))
e.delete_selected()
pump()
staged = e.document_controller.find_by_id(table['id'])
assert len(staged['items']) == 1
assert columns[0]['id'] not in staged['props']['rows'][0]['cells']
e.undo()
pump()
staged = e.document_controller.find_by_id(table['id'])
assert staged['props']['rows'][0]['cells'][columns[0]['id']] == 'sh010'
e.close()
w.close()
w.deleteLater()
pump()
''', tmp_path)
