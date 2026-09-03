# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..compat import QtGui


class LineNumberArea(QtGui.QWidget):

    def __init__(self, editor):
        QtGui.QWidget.__init__(
            self,
            editor
        )
        self.editor = editor

    def sizeHint(self):
        return QtCore.QSize(
            self.editor.line_number_area_width(),
            0
        )

    def paintEvent(self, event):
        self.editor.paint_line_numbers(
            event
        )


class CodeEditor(QtGui.QPlainTextEdit):

    def __init__(self, parent=None):
        QtGui.QPlainTextEdit.__init__(
            self,
            parent
        )

        self.line_numbers = LineNumberArea(
            self
        )

        font = QtGui.QFont(
            "Consolas"
        )
        font.setStyleHint(
            QtGui.QFont.Monospace
        )
        font.setPointSize(10)
        self.setFont(font)

        try:
            self.setTabStopWidth(
                self.fontMetrics().width(" ") * 4
            )
        except Exception:
            pass

        self.setLineWrapMode(
            QtGui.QPlainTextEdit.NoWrap
        )

        self.blockCountChanged.connect(
            self.update_margin
        )
        self.updateRequest.connect(
            self.update_line_numbers
        )
        self.cursorPositionChanged.connect(
            self.highlight_line
        )

        self.update_margin()
        self.highlight_line()

    def line_number_area_width(self):
        digits = len(
            str(
                max(
                    1,
                    self.blockCount()
                )
            )
        )

        return 10 + (
            self.fontMetrics().width("9") *
            digits
        )

    def update_margin(self, *args):
        self.setViewportMargins(
            self.line_number_area_width(),
            0,
            0,
            0
        )

    def update_line_numbers(
        self,
        rect,
        dy
    ):
        if dy:
            self.line_numbers.scroll(
                0,
                dy
            )
        else:
            self.line_numbers.update(
                0,
                rect.y(),
                self.line_numbers.width(),
                rect.height()
            )

        if rect.contains(
            self.viewport().rect()
        ):
            self.update_margin()

    def resizeEvent(self, event):
        QtGui.QPlainTextEdit.resizeEvent(
            self,
            event
        )

        rect = self.contentsRect()

        self.line_numbers.setGeometry(
            QtCore.QRect(
                rect.left(),
                rect.top(),
                self.line_number_area_width(),
                rect.height()
            )
        )

    def paint_line_numbers(
        self,        event
    ):
        painter = QtGui.QPainter(
            self.line_numbers
        )

        painter.fillRect(
            event.rect(),
            QtGui.QColor("#252525")
        )

        painter.setPen(
            QtGui.QColor("#777777")
        )

        block = self.firstVisibleBlock()
        number = block.blockNumber()

        top = int(
            self.blockBoundingGeometry(block)
            .translated(
                self.contentOffset()
            )
            .top()
        )

        bottom = top + int(
            self.blockBoundingRect(
                block
            ).height()
        )

        while (
            block.isValid() and
            top <= event.rect().bottom()
        ):
            if (
                block.isVisible() and
                bottom >= event.rect().top()
            ):
                painter.drawText(
                    0,
                    top,
                    self.line_numbers.width() - 5,
                    self.fontMetrics().height(),
                    QtCore.Qt.AlignRight,
                    str(number + 1)
                )

            block = block.next()
            top = bottom
            bottom = top + int(
                self.blockBoundingRect(
                    block
                ).height()
            )
            number += 1

    def highlight_line(self):
        selection = QtGui.QTextEdit.ExtraSelection()

        selection.format.setBackground(
            QtGui.QColor("#303030")
        )

        selection.format.setProperty(
            QtGui.QTextFormat.FullWidthSelection,
            True
        )

        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()

        self.setExtraSelections(
            [selection]
        )


class ScriptHighlighter(QtGui.QSyntaxHighlighter):

    PYTHON_WORDS = [
        "and", "as", "assert", "break", "class",
        "continue", "def", "del", "elif", "else",
        "except", "exec", "finally", "for", "from",
        "global", "if", "import", "in", "is",
        "lambda", "not", "or", "pass", "print",
        "raise", "return", "try", "while", "with",
        "yield", "True", "False", "None"
    ]

    MEL_WORDS = [
        "if", "else", "for", "while", "switch",
        "case", "break", "continue", "return",
        "global", "proc", "string", "int", "float",
        "vector", "matrix"
    ]

    def __init__(
        self,
        document,
        language="python"
    ):
        QtGui.QSyntaxHighlighter.__init__(
            self,
            document
        )

        self.language = language
        self.rules = []
        self.rebuild()

    def _fmt(
        self,
        color,
        bold=False,
        italic=False
    ):
        result = QtGui.QTextCharFormat()
        result.setForeground(
            QtGui.QColor(color)
        )

        if bold:
            result.setFontWeight(
                QtGui.QFont.Bold
            )

        result.setFontItalic(
            italic
        )
        return result

    def set_language(
        self,
        language
    ):
        self.language = language
        self.rebuild()

    def rebuild(self):
        self.rules = []

        keyword_fmt = self._fmt(
            "#d4a15d",
            bold=True
        )
        string_fmt = self._fmt(
            "#b9c66b"
        )
        comment_fmt = self._fmt(
            "#757575",
            italic=True
        )
        number_fmt = self._fmt(
            "#79a8d7"
        )
        maya_fmt = self._fmt(
            "#69b5b5"
        )

        words = (
            self.MEL_WORDS
            if self.language == "mel"
            else self.PYTHON_WORDS
        )

        for word in words:
            self.rules.append((
                QtCore.QRegExp(
                    "\\b{0}\\b".format(
                        word
                    )
                ),
                keyword_fmt
            ))

        self.rules.append((
            QtCore.QRegExp(
                "\"[^\"\\n]*\""
            ),
            string_fmt
        ))

        self.rules.append((
            QtCore.QRegExp(
                "'[^'\\n]*'"
            ),
            string_fmt
        ))

        if self.language == "mel":
            self.rules.append((
                QtCore.QRegExp(
                    "//[^\\n]*"
                ),
                comment_fmt
            ))
        else:
            self.rules.append((
                QtCore.QRegExp(
                    "#[^\\n]*"
                ),
                comment_fmt
            ))

            for word in (
                "cmds",
                "mel",
                "toolbox"
            ):
                self.rules.append((
                    QtCore.QRegExp(
                        "\\b{0}\\b".format(
                            word
                        )
                    ),
                    maya_fmt
                ))

        self.rules.append((
            QtCore.QRegExp(
                "\\b[0-9]+(?:\\.[0-9]+)?\\b"
            ),
            number_fmt
        ))

        self.rehighlight()

    def highlightBlock(
        self,
        text
    ):
        for expression, fmt in self.rules:
            index = expression.indexIn(
                text
            )

            while index >= 0:
                length = expression.matchedLength()

                self.setFormat(
                    index,
                    length,
                    fmt
                )

                index = expression.indexIn(
                    text,
                    index + max(
                        1,
                        length
                    )
                )


__all__ = [
    "CodeEditor",
    "LineNumberArea",
    "ScriptHighlighter",
]
