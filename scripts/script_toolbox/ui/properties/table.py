# -*- coding: utf-8 -*-
from __future__ import print_function

import copy

from ...compat import QtGui
from ...model.table import new_row, MAX_ROWS, MAX_CELLS
from .base import PropertyEditorBase


class TablePropertyEditor(PropertyEditorBase):
    def __init__(self, toolbox=None, parent=None):
        PropertyEditorBase.__init__(self, toolbox, parent)
        self.rows = []
        self.row_count = QtGui.QSpinBox()
        self.row_count.setRange(0, MAX_ROWS)
        self.row_height = QtGui.QSpinBox()
        self.row_height.setRange(28, 200)
        self.height = QtGui.QSpinBox()
        self.height.setRange(80, 2000)
        self.show_row_numbers = QtGui.QCheckBox()
        self.allow_add_rows = QtGui.QCheckBox()
        self.allow_remove_rows = QtGui.QCheckBox()
        self.edit_rows_button = QtGui.QPushButton('Edit initial rows…')
        self.content_section.addRow('Initial rows', self.row_count)
        self.content_section.addWidget(self.edit_rows_button)
        self.appearance_section.addRow('Row height', self.row_height)
        self.appearance_section.addRow('Table height', self.height)
        self.appearance_section.addRow('Row numbers', self.show_row_numbers)
        self.behavior_section.addRow('Add rows', self.allow_add_rows)
        self.behavior_section.addRow('Remove rows', self.allow_remove_rows)
        hint = QtGui.QLabel('Add child Items under Table in Existing Parameters. Each child defines one column. '
                           'Use its normal inspector for the type, defaults, range and events; use Label for the header.')
        hint.setWordWrap(True)
        hint.setObjectName('HintText')
        self.content_section.addWidget(hint)
        self.add_stretch()
        for widget in (self.row_count, self.row_height, self.height):
            widget.valueChanged.connect(self._control_changed)
        for widget in (self.show_row_numbers, self.allow_add_rows, self.allow_remove_rows):
            widget.toggled.connect(self._control_changed)
        self.edit_rows_button.clicked.connect(self.edit_rows)

    def load_specific(self, props):
        self.row_count.setMaximum(min(MAX_ROWS, MAX_CELLS // max(1, len(self.item.get("items", [])))))
        self.rows = copy.deepcopy(props.get('rows', []))
        self.row_count.setValue(len(self.rows))
        self.row_height.setValue(props.get('row_height', 36))
        self.height.setValue(props.get('height', 260))
        self.show_row_numbers.setChecked(props.get('show_row_numbers', True))
        self.allow_add_rows.setChecked(props.get('allow_add_rows', True))
        self.allow_remove_rows.setChecked(props.get('allow_remove_rows', True))

    def write_specific(self, props):
        count = self.row_count.value()
        rows = copy.deepcopy(self.rows[:count])
        while len(rows) < count:
            rows.append(new_row())
        self.rows = rows
        props.update(rows=copy.deepcopy(rows), row_height=self.row_height.value(), height=self.height.value(),
                     show_row_numbers=self.show_row_numbers.isChecked(), allow_add_rows=self.allow_add_rows.isChecked(),
                     allow_remove_rows=self.allow_remove_rows.isChecked())

    def edit_rows(self):
        from ..table_runtime import Spreadsheet, PreviewTableContext
        from ...qt_compat import qt_exec
        self.write_to_item()
        if not self.item.get('items'):
            QtGui.QMessageBox.information(self, 'Table', 'Add column Items under Table first.')
            return
        dialog = QtGui.QDialog(self)
        dialog.setWindowTitle('Table — initial rows')
        dialog.resize(760, 420)
        layout = QtGui.QVBoxLayout(dialog)
        item = copy.deepcopy(self.item)
        item['props']['allow_add_rows'] = True
        item['props']['allow_remove_rows'] = True
        context = PreviewTableContext(item)
        context.widget = Spreadsheet(context, item, dialog, preview=True)
        layout.addWidget(context.widget)
        buttons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if qt_exec(dialog) == QtGui.QDialog.Accepted:
            self.rows = copy.deepcopy(context.widget.current_item()['props']['rows'])
            self.loading = True
            self.row_count.setValue(len(self.rows))
            self.loading = False
            self._control_changed()
        dialog.deleteLater()
