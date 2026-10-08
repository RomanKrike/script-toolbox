# -*- coding: utf-8 -*-
from __future__ import print_function
import re
from ...compat import QtCore, QtGui
from ...core.expressions import (Expression, ExpressionError, ExpressionState,
                                RESERVED_WORDS, tokenize)
from ...model.items import walk_items
from ...model.item_registry import ITEM_TYPES
from ...pycompat import text_type
from ...style import metrics, palette


class ExpressionHighlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, editor):
        QtGui.QSyntaxHighlighter.__init__(self, editor.document())
        self.editor = editor
        self.names = set()

    def highlightBlock(self, text):
        text = text_type(text)
        try:
            tokens = tokenize(text)
        except ExpressionError as exc:
            fmt = QtGui.QTextCharFormat()
            fmt.setUnderlineStyle(QtGui.QTextCharFormat.WaveUnderline)
            fmt.setUnderlineColor(QtGui.QColor(palette.EXPRESSION_ERROR))
            self.setFormat(exc.position, max(1, len(text) - exc.position), fmt)
            return
        for value, start, end in tokens:
            fmt = QtGui.QTextCharFormat()
            color = None
            if value.startswith('"'): color = palette.SYNTAX_STRING
            elif value in ('true', 'false') or re.match(r'^-?\d', value): color = palette.SYNTAX_KEYWORD
            elif value in RESERVED_WORDS: color = palette.TEXT_STRUCTURE_COLUMN
            elif re.match(r'^[A-Za-z_]', value):
                if value in self.names:
                    color = palette.SYNTAX_NUMBER
                else:
                    fmt.setUnderlineStyle(QtGui.QTextCharFormat.WaveUnderline)
                    fmt.setUnderlineColor(QtGui.QColor(palette.EXPRESSION_ERROR))
            if color is not None: fmt.setForeground(QtGui.QColor(color))
            self.setFormat(start, end - start, fmt)


class ExpressionEdit(QtGui.QPlainTextEdit):
    """Compact expression editor with Qt4-compatible native completion."""
    def __init__(self, parent=None):
        QtGui.QPlainTextEdit.__init__(self, parent)
        self.setFixedHeight(metrics.EXPRESSION_EDITOR_HEIGHT)
        self.setTabChangesFocus(True)
        self.setMouseTracking(True)
        self.parameters = {}
        self.highlighter = ExpressionHighlighter(self)
        self.completer = QtGui.QCompleter([], self)
        self.completer.setWidget(self)
        self.completer.activated.connect(self._insert_completion)
        self.textChanged.connect(self._complete)

    def set_names(self, names):
        names = set(names)
        if names == self.highlighter.names:
            return
        self.highlighter.names = names
        model = self.completer.model()
        if isinstance(model, QtCore.QStringListModel):
            model.setStringList(sorted(names))
        else:
            self.completer.setModel(QtCore.QStringListModel(sorted(names), self.completer))
        previous = self.blockSignals(True)
        try:
            self.highlighter.rehighlight()
        finally:
            self.blockSignals(previous)

    def mouseMoveEvent(self, event):
        cursor = self.cursorForPosition(event.pos())
        cursor.select(QtGui.QTextCursor.WordUnderCursor)
        item = self.parameters.get(text_type(cursor.selectedText()))
        if item is not None:
            self.setToolTip('{0} ({1}) = {2}'.format(
                item['name'], item['kind'], item.get('props', {}).get('value')))
        else:
            self.setToolTip('Use parameter names, comparisons, &&, || and !.')
        QtGui.QPlainTextEdit.mouseMoveEvent(self, event)

    def _prefix(self):
        cursor = self.textCursor()
        before = text_type(self.toPlainText())[:cursor.position()]
        match = re.search(r'[A-Za-z_][A-Za-z0-9_]*$', before)
        return match.group() if match else ''

    def _complete(self):
        if not self.hasFocus(): return
        prefix = self._prefix()
        self.completer.setCompletionPrefix(prefix)
        if prefix and self.completer.completionCount():
            self.completer.complete(self.cursorRect())
        else:
            self.completer.popup().hide()

    def _insert_completion(self, value):
        cursor = self.textCursor()
        for unused in self._prefix(): cursor.deletePreviousChar()
        cursor.insertText(text_type(value))
        self.setTextCursor(cursor)
        self.completer.popup().hide()

    def keyPressEvent(self, event):
        if self.completer.popup().isVisible() and event.key() in (
                QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return, QtCore.Qt.Key_Escape,
                QtCore.Qt.Key_Tab, QtCore.Qt.Key_Backtab):
            event.ignore()
            return
        QtGui.QPlainTextEdit.keyPressEvent(self, event)


class ExpressionProperty(QtGui.QWidget):
    changed = QtCore.Signal()

    def __init__(self, prop, owner):
        QtGui.QWidget.__init__(self, owner)
        self.prop, self.owner, self.loading = prop, owner, False
        layout = QtGui.QVBoxLayout(self)
        layout.setContentsMargins(*metrics.MARGINS_NONE)
        layout.setSpacing(metrics.INLINE_CONTROL_SPACING)
        row = QtGui.QHBoxLayout()
        row.setContentsMargins(*metrics.MARGINS_NONE)
        self.base = QtGui.QCheckBox()
        self.base.setChecked(True)
        self.fx = QtGui.QPushButton('fx')
        self.fx.setCheckable(True)
        self.fx.setToolTip('Use an expression; unchecked uses the saved checkbox value.')
        row.addWidget(self.base)
        row.addStretch(1)
        row.addWidget(self.fx)
        layout.addLayout(row)
        self.editor = ExpressionEdit(self)
        self.editor.setToolTip('References use parameter names. Operators: == != > < >= <= && || !\nExample: mode == "preview" && use_custom_path')
        layout.addWidget(self.editor)
        self.result = QtGui.QLabel()
        self.result.setObjectName('HintText')
        self.result.setWordWrap(True)
        layout.addWidget(self.result)
        self.fx.toggled.connect(self._changed)
        self.base.toggled.connect(self._changed)
        self.editor.textChanged.connect(self._changed)
        self.refresh()

    def document(self):
        return getattr(self.owner, 'expression_document', None) or getattr(self.owner.toolbox, 'config', {})

    def load(self, ui):
        self.loading = True
        try:
            self.base.setChecked(bool(ui.get(self.prop, True)))
            self.fx.setChecked(bool(ui.get(self.prop + '_expression_enabled', False)))
            self.editor.setPlainText(text_type(ui.get(self.prop + '_expression', '')))
        finally:
            self.loading = False
        self.refresh()

    def write(self, ui):
        ui[self.prop] = self.base.isChecked()
        ui[self.prop + '_expression_enabled'] = self.fx.isChecked()
        ui[self.prop + '_expression'] = text_type(self.editor.toPlainText())
        try:
            expression = Expression(ui[self.prop + '_expression'])
        except ExpressionError:
            return
        names = {}
        for item in walk_items(self.document(), include_sections=True):
            names.setdefault(item['name'], []).append(item['id'])
        old, refs = ui.get(self.prop + '_references', {}), {}
        for name in expression.dependencies:
            if name in old: refs[name] = old[name]
            elif len(names.get(name, [])) == 1: refs[name] = names[name][0]
        ui[self.prop + '_references'] = refs

    def refresh(self):
        self.base.setEnabled(not self.fx.isChecked())
        self.editor.setVisible(self.fx.isChecked())
        self.result.setVisible(self.fx.isChecked())
        document = self.document()
        parameters = [item for item in walk_items(document, include_sections=True)
                      if ITEM_TYPES.get(item['kind']).has_capability('has_value')]
        names = [item['name'] for item in parameters]
        self.editor.parameters = dict((item['name'], item) for item in parameters)
        self.editor.set_names(names)
        if not self.fx.isChecked() or self.owner.item is None: return
        state = ExpressionState(document)
        item_id = self.owner.item['id']
        if item_id not in state.items:
            self.result.setText('Apply the parameter to evaluate this expression.')
            return
        value = state.evaluate(item_id, self.prop)
        error = state.errors.get((item_id, self.prop))
        self.result.setText(('Error: ' + error + '\nUsing saved checkbox value: ' if error else 'Result: ') + str(value).lower())

    def _changed(self, *args):
        if self.loading: return
        self.changed.emit()
        self.refresh()
