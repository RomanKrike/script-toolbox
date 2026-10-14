# -*- coding: utf-8 -*-
"""Spreadsheet presentation reusing authored Item renderers for typed cells."""
from __future__ import print_function

import copy

from ..compat import QtCore, QtGui
from ..core.item_changes import Item, resolve_item, update_item
from ..core.event_bindings import dispatch_item_event
from ..model.table import cell_value, column_item, MAX_ROWS, MAX_CELLS
from ..model.item_registry import ITEM_TYPES
from ..style import metrics
from .runtime import RuntimeControlFactory


class CellToolbox(object):
    """One cell's lifetime and value/event route; no document Item duplication."""
    def __init__(self, table, row_id, column_id):
        self.table = table
        self.row_id = row_id
        self.column_id = column_id
        self.binding = None
        self.alive = True
        self._binding_widget_click_suppression = set()

    def can_edit(self):
        return (self.alive and self.table is not None and not self.table.loading and
                (self.table.preview or (not self.table.context.disposed and self.table.context.active)))

    def current_item(self):
        table = self.table.current_item()
        column = copy.deepcopy(column_item(table, self.column_id))
        column['id'] = self.row_id + ':' + self.column_id
        column['ui']['show_label'] = column['kind'] in ('button', 'label', 'icon')
        column['ui']['visible_expression_enabled'] = False
        column['ui']['enabled_expression_enabled'] = False
        if ITEM_TYPES.get(column['kind']).has_capability('has_value'):
            column['props']['value'] = cell_value(table, self.row_id, self.column_id)
        return column

    def dispose(self, *args):
        self.alive = False
        if self.binding is not None:
            self.binding.dispose()
        self.binding = None
        self.table = None

    def register_value_widget(self, key, binding):
        self.binding = binding

    def register_item_widget(self, *args):
        pass

    def register_condition_widget(self, item, widget, apply=None):
        column = column_item(self.table.current_item(), self.column_id)
        widget.setVisible(column['ui'].get('visible', True))
        widget.setEnabled(column['ui'].get('enabled', True))

    def get_value(self, key, default=None):
        if not self.alive or (not self.table.preview and self.table.context.disposed):
            return default
        return self.current_item()['props'].get('value', default)

    def store_value(self, key, value):
        if not self.can_edit():
            return False
        if self.table.current_item().get("_preset_reference"):
            return False
        old = self.get_value(key)
        self.table.handle().set_cell(self.row_id, self.column_id, value)
        current = self.get_value(key)
        if old != current:
            self.dispatch_binding_event(self.current_item(), 'value_changed', value=current, old_value=old)
        return True

    def run_item(self, key):
        if not self.can_edit():
            return None
        if key in self._binding_widget_click_suppression:
            self._binding_widget_click_suppression.discard(key)
            return None
        return self.dispatch_binding_event(self.current_item(), 'click', mouse_button='left', modifiers=[])

    def dispatch_binding_event(self, item, event, **kwargs):
        if not self.alive or self.table.loading or self.table.preview:
            return []
        context = self.table.context
        if context.disposed or not context.active:
            return []
        handle = self.table.handle()
        data = self.table.current_item()
        row_index = next(index for index, row in enumerate(data['props']['rows']) if row['id'] == self.row_id)
        column = column_item(data, self.column_id)
        namespace = {'table': handle, 'row': handle.row(self.row_id), 'row_id': self.row_id,
                     'row_index': row_index, 'column': column['name']}
        return dispatch_item_event(context._window, self.current_item(), event,
                                   parent=context._window, extra_namespace=namespace, **kwargs)


class CellOwner(RuntimeControlFactory):
    def __init__(self, toolbox, content):
        self.toolbox = toolbox
        self.content = content


class CellFocus(QtCore.QObject):
    def __init__(self, grid, row, column, parent):
        QtCore.QObject.__init__(self, parent)
        self.grid, self.row, self.column = grid, row, column

    def eventFilter(self, watched, event):
        if event.type() in (QtCore.QEvent.FocusIn, QtCore.QEvent.MouseButtonPress):
            self.grid.setCurrentCell(self.row, self.column)
        return False


class Spreadsheet(QtGui.QWidget):
    def __init__(self, context, item, parent=None, preview=False):
        QtGui.QWidget.__init__(self, parent)
        self.setObjectName('RuntimeTable')
        self.context = context
        self.item_id = item['id']
        self.preview = preview
        self.loading = False
        self.cells = {}
        self.row_ids = []
        self.column_ids = []
        self._column_signature = None
        self._registered_columns = set()
        layout = QtGui.QVBoxLayout(self)
        layout.setContentsMargins(*metrics.MARGINS_NONE)
        layout.setSpacing(metrics.RUNTIME_PARAMETER_SPACING)
        self.title = QtGui.QLabel()
        self.title.setObjectName('PaneTitle')
        layout.addWidget(self.title)
        self.grid = QtGui.QTableWidget()
        self.grid.setObjectName('Spreadsheet')
        self.grid.setAlternatingRowColors(True)
        self.grid.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.grid.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.grid.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.grid.setSortingEnabled(False)
        self.grid.horizontalHeader().setStretchLastSection(True)
        self.grid.horizontalHeader().setMinimumSectionSize(metrics.TABLE_MIN_COLUMN_WIDTH)
        layout.addWidget(self.grid, 1)
        buttons = QtGui.QHBoxLayout()
        self.add_button = QtGui.QPushButton('+ Add row')
        self.remove_button = QtGui.QPushButton('Remove row')
        self.count_label = QtGui.QLabel()
        self.count_label.setObjectName('HintText')
        buttons.addWidget(self.add_button)
        buttons.addWidget(self.remove_button)
        buttons.addStretch(1)
        buttons.addWidget(self.count_label)
        layout.addLayout(buttons)
        self.add_button.clicked.connect(self.add_row)
        self.remove_button.clicked.connect(self.remove_row)
        self.grid.currentCellChanged.connect(lambda *args: self.update_actions())
        self.destroyed.connect(self.dispose_cells)
        self.refresh()

    def current_item(self):
        return resolve_item(self.context.config, self.item_id)

    def handle(self):
        owner = self.context if self.preview else self.context._window
        return Item(owner, self.item_id).table()

    def dispose_cells(self, *args):
        for cell in self.cells.values():
            cell.dispose()
        self.cells = {}

    def update_actions(self):
        readonly = bool(self.current_item().get("_preset_reference"))
        self.remove_button.setEnabled(not readonly and self.grid.currentRow() >= 0 and bool(self.row_ids))
        self.add_button.setEnabled(not readonly and len(self.row_ids) < MAX_ROWS and
                                   (len(self.row_ids) + 1) * len(self.column_ids) <= MAX_CELLS)

    def refresh(self):
        data = self.current_item()
        columns = data.get('items', [])
        rows = data['props']['rows']
        row_ids = [row['id'] for row in rows]
        column_ids = [column['id'] for column in columns]
        signature = copy.deepcopy(columns)
        rebuild = row_ids != self.row_ids or column_ids != self.column_ids or signature != self._column_signature
        old_widths = dict((key, self.grid.columnWidth(index)) for index, key in enumerate(self.column_ids))
        selected = self.row_ids[self.grid.currentRow()] if 0 <= self.grid.currentRow() < len(self.row_ids) else None
        self.loading = True
        try:
            self.title.setText(data['ui']['label'])
            self.title.setVisible(data['ui'].get('show_label', True))
            self.grid.setFixedHeight(data['props']['height'])
            self.grid.verticalHeader().setVisible(data['props']['show_row_numbers'])
            self.add_button.setVisible(data['props']['allow_add_rows'])
            self.remove_button.setVisible(data['props']['allow_remove_rows'])
            if rebuild:
                self.dispose_cells()
                self.grid.clear()
                self.grid.setRowCount(len(rows))
                self.grid.setColumnCount(len(columns))
                self.grid.setHorizontalHeaderLabels([column['ui']['label'] or column['name'] for column in columns])
                self.row_ids, self.column_ids = row_ids, column_ids
                header = self.grid.horizontalHeader()
                resize = getattr(header, 'setSectionResizeMode', None) or header.setResizeMode
                any_stretch = any(column['ui']['width_mode'] == 'stretch' for column in columns)
                header.setStretchLastSection(bool(columns and not any_stretch and columns[-1]['ui']['width_mode'] != 'fixed'))
                for column_index, column in enumerate(columns):
                    width_mode = column['ui']['width_mode']
                    resize(column_index, QtGui.QHeaderView.Fixed if width_mode == 'fixed' else
                           QtGui.QHeaderView.Stretch if width_mode == 'stretch' else QtGui.QHeaderView.Interactive)
                    width = column['ui']['width'] if width_mode == 'fixed' else old_widths.get(column['id'], metrics.TABLE_DEFAULT_COLUMN_WIDTH)
                    if column['kind'] == 'color':
                        width = max(width, metrics.APPEARANCE_COLOR_FIELD_WIDTH)
                    self.grid.setColumnWidth(column_index, width)
                    self.grid.setColumnHidden(column_index, not column['ui'].get('visible', True))
                    if not self.preview:
                        self.context.register_item_widget(column, self, None)
                        if column['id'] not in self._registered_columns:
                            self.context.register_condition_widget(column, self.grid,
                                lambda visible, enabled, key=column['id']: self.apply_column_state(key, visible, enabled))
                            self._registered_columns.add(column['id'])
                    for row_index, row in enumerate(rows):
                        entry = QtGui.QTableWidgetItem('')
                        entry.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
                        self.grid.setItem(row_index, column_index, entry)
                        cell = CellToolbox(self, row['id'], column['id'])
                        owner = CellOwner(cell, self.grid.viewport())
                        if column['kind'] == 'reference':
                            widget = QtGui.QLabel('Column source unavailable')
                            widget.setToolTip(column['ui'].get('tooltip', ''))
                            widget.setEnabled(False)
                        else:
                            widget = owner.build_runtime_widget(cell.current_item(), compact=True)
                        self.cells[(row['id'], column['id'])] = cell
                        widget.destroyed.connect(cell.dispose)
                        holder = QtGui.QWidget()
                        holder_layout = QtGui.QHBoxLayout(holder)
                        holder_layout.setContentsMargins(*metrics.TABLE_CELL_MARGINS)
                        holder_layout.addWidget(widget)
                        if column['ui']['width_mode'] != 'fixed':
                            minimum = widget.minimumSizeHint().width() + sum(metrics.TABLE_CELL_MARGINS[::2])
                            self.grid.setColumnWidth(column_index, max(self.grid.columnWidth(column_index), minimum))
                        self.grid.setCellWidget(row_index, column_index, holder)
                        for control in [widget] + widget.findChildren(QtGui.QWidget):
                            focus = CellFocus(self.grid, row_index, column_index, control)
                            control.installEventFilter(focus)
                            control._table_cell_focus = focus
                self._column_signature = signature
                if selected in row_ids:
                    self.grid.setCurrentCell(row_ids.index(selected), 0)
            else:
                for cell in self.cells.values():
                    if cell.binding is not None:
                        cell.binding.sync(cell.current_item())
            for row_index in range(len(rows)):
                self.grid.setRowHeight(row_index, data['props']['row_height'])
            self.count_label.setText('{0} rows / {1} columns'.format(len(rows), len(columns)))
            self.update_actions()
        finally:
            self.loading = False

    def apply_column_state(self, key, visible, enabled):
        if key not in self.column_ids:
            return
        column_index = self.column_ids.index(key)
        self.grid.setColumnHidden(column_index, not visible)
        for index in range(len(self.row_ids)):
            widget = self.grid.cellWidget(index, column_index)
            if widget is not None:
                column = column_item(self.current_item(), key)
                readonly_value = bool(self.current_item().get("_preset_reference")) and ITEM_TYPES.get(column["kind"]).has_capability("has_value")
                widget.setEnabled(enabled and not readonly_value)

    def apply_item_change(self, item, change):
        self.refresh()
        return True

    def add_row(self):
        if self.current_item().get('_preset_reference') or not self.current_item()['props']['allow_add_rows']:
            return
        row_id = self.handle().add_row()
        if self.row_ids and self.column_ids:
            self.grid.setCurrentCell(self.row_ids.index(row_id), 0)

    def remove_row(self):
        index = self.grid.currentRow()
        if index >= 0 and not self.current_item().get('_preset_reference') and self.current_item()['props']['allow_remove_rows']:
            self.handle().remove_row(self.row_ids[index])


class PreviewTableContext(object):
    """Isolated initial-data editor: no saves and no execution of user scripts."""
    def __init__(self, item):
        self.config = {'sections': [{'kind': 'folder', 'items': [copy.deepcopy(item)]}]}
        self.widget = None

    def change_item(self, key, props):
        item = resolve_item(self.config, key)
        change = update_item(item, props)
        if change.changed and self.widget is not None:
            self.widget.refresh()
        return change


def render_table(owner, item, compact=False):
    return Spreadsheet(owner.toolbox, item)
