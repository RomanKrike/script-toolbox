# -*- coding: utf-8 -*-
"""Spreadsheet data: authored child Items are columns, never row/cell Items."""
from __future__ import print_function

import copy
import json
import uuid

from ..pycompat import text_type, integer_type
from .fields import Field, FieldValidationError
from .item_registry import ITEM_TYPES, ItemValidationError

CELL_KINDS = ('string', 'integer', 'float', 'checkbox', 'menu', 'color',
              'button', 'label', 'icon')
MAX_ROWS = 1000
MAX_COLUMNS = 64
MAX_CELLS = 10000


class TableRowsField(Field):
    def __init__(self):
        Field.__init__(self, default=[])

    def normalize(self, value):
        if value is None:
            value = []
        if not isinstance(value, list) or len(value) > MAX_ROWS:
            raise FieldValidationError(value, 'Expected at most 1000 rows')
        rows = []
        ids = set()
        for row in value:
            if not isinstance(row, dict) or set(row) != set(('id', 'cells')):
                raise FieldValidationError(row, 'Each row requires id and cells')
            row_id = row['id']
            if not isinstance(row_id, (str, text_type)) or not row_id or row_id in ids:
                raise FieldValidationError(row_id, 'Row IDs must be non-empty and unique')
            if not isinstance(row['cells'], dict):
                raise FieldValidationError(row['cells'], 'Expected cells mapping')
            ids.add(row_id)
            rows.append(copy.deepcopy(row))
        return rows

    def validate(self, value):
        try:
            self.normalize(value)
            return True
        except FieldValidationError:
            return False


def new_row(cells=None):
    return {'id': text_type(uuid.uuid4().hex), 'cells': copy.deepcopy(cells or {})}


def column_item(table, key):
    columns = table.get('items', [])
    if isinstance(key, (int, integer_type)) and not isinstance(key, bool):
        if key < 0 or key >= len(columns):
            raise IndexError('Column index out of range')
        return columns[key]
    for field in ('id', 'name'):
        for column in columns:
            if column[field] == text_type(key):
                return column
    raise KeyError('Table column not found: ' + text_type(key))


def row_item(table, key):
    rows = table['props']['rows']
    if isinstance(key, (int, integer_type)) and not isinstance(key, bool):
        if key < 0 or key >= len(rows):
            raise IndexError('Row index out of range')
        return rows[key]
    for row in rows:
        if row['id'] == text_type(key):
            return row
    raise KeyError('Table row not found: ' + text_type(key))


def cell_value(table, row, column):
    row = row_item(table, row)
    column = column_item(table, column)
    value = copy.deepcopy(row['cells'].get(column['id'], column['props'].get('value')))
    return normalize_cell(column, value) if ITEM_TYPES.get(column['kind']).has_capability('has_value') else value


def normalize_cell(column, value):
    if column['kind'] == 'reference':
        target = ITEM_TYPES.get(column['props'].get('target_kind'))
        if target is None or not target.has_capability('has_value'):
            raise ValueError('This referenced column has no editable value')
        # Authored references do not contain the source's range/options yet.
        # Typed normalization resumes when the resolver supplies the real Item.
        json.dumps(value, allow_nan=False)
        return copy.deepcopy(value)
    definition = ITEM_TYPES.get(column['kind'], required=True)
    if not definition.has_capability('has_value'):
        raise ValueError('This column has no editable value')
    props = copy.deepcopy(column['props'])
    props['value'] = copy.deepcopy(value)
    return definition.normalize_props(props, item_id=column['id'], item_name=column['name'])['value']


def normalize_table(item):
    columns = item.get('items', [])
    if len(columns) > MAX_COLUMNS:
        raise ItemValidationError('table', 'items', columns, 'At most 64 columns', item['id'], item['name'])
    if len(columns) * len(item['props']['rows']) > MAX_CELLS:
        raise ItemValidationError('table', 'rows', len(item['props']['rows']),
                                  'At most 10000 cells per table', item['id'], item['name'])
    for column in columns:
        if column['kind'] == 'reference' and column['props'].get('target_kind') not in CELL_KINDS:
            raise ItemValidationError('table', 'items', column, 'Unsupported referenced column type', item['id'], item['name'])
    by_id = dict((column['id'], column) for column in columns)
    if len(by_id) != len(columns):
        raise ItemValidationError('table', 'items', columns, 'Column IDs must be unique', item['id'], item['name'])
    rows = copy.deepcopy(item['props']['rows'])
    for row in rows:
        for column_id, value in row['cells'].items():
            if column_id not in by_id:
                raise ItemValidationError('table', 'rows', column_id,
                                          'Cell references a missing column', item['id'], item['name'])
            try:
                row['cells'][column_id] = normalize_cell(by_id[column_id], value)
            except (TypeError, ValueError) as exc:
                raise ItemValidationError('table', 'rows', value,
                    'Invalid cell in column {0}: {1}'.format(by_id[column_id]['name'], text_type(exc)), item['id'], item['name'])
    item['props']['rows'] = rows
    return item


def remap_columns(source, clone):
    """Keep cell values attached to columns during copy/paste and duplication."""
    if source.get('kind') != 'table':
        return
    mapping = dict((old['id'], new['id']) for old, new in zip(source.get('items', []), clone.get('items', [])))
    for row in clone.get('props', {}).get('rows', []):
        row['id'] = text_type(uuid.uuid4().hex)
        row['cells'] = dict((mapping[key], value) for key, value in row['cells'].items() if key in mapping)
