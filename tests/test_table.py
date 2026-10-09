"""Typed spreadsheet storage and mutation must not create document cell Items."""
import copy

import pytest

from script_toolbox.model import create_item
from script_toolbox.model.table import cell_value, new_row
from script_toolbox.model.item_registry import ItemValidationError
from script_toolbox.core.item_changes import Item, update_item
from script_toolbox.core.editor_document import EditorDocumentController


def sample_table():
    columns = [create_item('string', {'name': 'name'}),
               create_item('integer', {'name': 'count', 'props': {'min': 0, 'max': 10}}),
               create_item('button', {'name': 'open'})]
    return create_item('table', {'name': 'shots', 'items': columns})


class Owner:
    def __init__(self, table):
        self.config = {'version': 21, 'sections': [create_item('folder', {'items': [table]})]}

    def change_item(self, key, values):
        from script_toolbox.core.item_changes import resolve_item
        return update_item(resolve_item(self.config, key), values)


def test_table_api_typed_values_and_stable_rows():
    owner = Owner(sample_table())
    api = Item(owner, 'shots').table()
    row = api.add_row({'name': 'sh010', 'count': 20})
    assert api.columns == ['name', 'count', 'open']
    assert api.get_cell(row, 'count') == 10
    assert api.row(0) == {'name': 'sh010', 'count': 10, 'open': None}
    api.set_cell(row, 'count', 4)
    assert api.get_cell(0, 1) == 4
    assert Item(owner, 'shots').rows[0]['id'] == row
    api.remove_row(row)
    assert api.rows == []


def test_invalid_rows_do_not_partially_mutate():
    table = sample_table()
    saved = copy.deepcopy(table)
    with pytest.raises(ItemValidationError):
        update_item(table, {'rows': [new_row({'missing': 4})]})
    assert table == saved
    with pytest.raises(ItemValidationError):
        update_item(table, {'rows': [new_row({table['items'][1]['id']: 'bad number'})]})
    assert table == saved
    with pytest.raises(ValueError):
        Item(Owner(table), 'shots').table().add_row({'open': 'invalid value'})


def test_table_rejects_container_columns_and_duplicate_row_ids():
    with pytest.raises(ItemValidationError):
        create_item('table', {'items': [create_item('row')]})
    row = new_row()
    with pytest.raises(ItemValidationError):
        create_item('table', {'props': {'rows': [row, row]}})


def test_clone_preserves_cell_values_under_new_column_ids():
    table = sample_table()
    table['props']['rows'] = [new_row({table['items'][0]['id']: 'sh010'})]
    controller = EditorDocumentController({'sections': [create_item('folder', {'items': [table]})]})
    clone = controller.clone_subtree(table)
    assert clone['items'][0]['id'] != table['items'][0]['id']
    assert clone['props']['rows'][0]['id'] != table['props']['rows'][0]['id']
    assert cell_value(clone, 0, 0) == 'sh010'
    assert clone['props']['rows'][0]['cells'] == {clone['items'][0]['id']: 'sh010'}


def test_table_config_round_trip(tmp_path):
    from script_toolbox.core.config import save_config, load_config
    table = sample_table()
    table['props']['rows'] = [new_row({table['items'][0]['id']: 'sh010'})]
    owner = Owner(table)
    path = str(tmp_path / 'table.json')
    save_config(owner.config, path)
    loaded = load_config(path)
    assert Item(type('Reader', (), {'config': loaded})(), 'shots').table().get_cell(0, 'name') == 'sh010'


def test_authored_reference_columns_preserve_row_data_until_resolved():
    reference = create_item('reference', {'name': 'count', 'props': {
        'source': 'studio', 'preset': 'shots', 'parameter': 'count', 'target_kind': 'integer'}})
    table = create_item('table', {'items': [reference], 'props': {
        'rows': [new_row({reference['id']: 500})]}})
    assert table['props']['rows'][0]['cells'][reference['id']] == 500
    reference['props']['target_kind'] = 'folder'
    with pytest.raises(ItemValidationError):
        create_item('table', {'items': [reference]})
