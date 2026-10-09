# -*- coding: utf-8 -*-
"""Document-scoped Table operations use the same atomic Item.set commit path."""
import copy

from ..model.table import cell_value, column_item, row_item, new_row, normalize_cell


class Table(object):
    def __init__(self, item):
        self.item = item

    @property
    def columns(self):
        return [column['name'] for column in self.item._resolve().get('items', [])]

    @property
    def rows(self):
        table = self.item._resolve()
        return [self.row(row['id']) for row in table['props']['rows']]

    def row(self, key):
        table = self.item._resolve()
        row = row_item(table, key)
        return dict((column['name'], cell_value(table, row['id'], column['id']))
                    for column in table.get('items', []))

    def get_cell(self, row, column):
        return cell_value(self.item._resolve(), row, column)

    def set_cell(self, row, column, value):
        table = self.item._resolve()
        current_row = row_item(table, row)
        current_column = column_item(table, column)
        rows = copy.deepcopy(table['props']['rows'])
        target = next(candidate for candidate in rows if candidate['id'] == current_row['id'])
        target['cells'][current_column['id']] = normalize_cell(current_column, value)
        return self.item.set(rows=rows)

    def add_row(self, values=None):
        table = self.item._resolve()
        cells = {}
        for key, value in (values or {}).items():
            column = column_item(table, key)
            cells[column['id']] = normalize_cell(column, value)
        row = new_row(cells)
        self.item.set(rows=table['props']['rows'] + [row])
        return row['id']

    def remove_row(self, key):
        table = self.item._resolve()
        target = row_item(table, key)
        return self.item.set(rows=[row for row in table['props']['rows'] if row['id'] != target['id']])
