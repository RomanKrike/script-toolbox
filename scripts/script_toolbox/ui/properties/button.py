# -*- coding: utf-8 -*-
from __future__ import print_function

from ...compat import QtGui
from ...core.executor import execute_script
from ...model.items import safe_color
from ...pycompat import text_type
from ..code_editor import CodeEditor
from ..code_editor import ScriptHighlighter
from .base import PropertyEditorBase


class ButtonPropertyEditor(PropertyEditorBase):

    def __init__(
        self,
        toolbox=None,
        parent=None
    ):
        PropertyEditorBase.__init__(
            self,
            toolbox,
            parent
        )

        self.language = QtGui.QComboBox()
        self.language.addItems([
            "Python",
            "MEL"
        ])

        self.color = [
            0.25,
            0.25,
            0.25
        ]
        self.color_button = QtGui.QPushButton(
            "Choose..."
        )

        self.form.addRow(
            "Language",
            self.language
        )
        self.form.addRow(
            "Button Color",
            self.color_button
        )

        self.tabs = QtGui.QTabWidget()

        self.click_editor = CodeEditor()
        self.shift_editor = CodeEditor()

        self.click_highlighter = ScriptHighlighter(
            self.click_editor.document(),
            "python"
        )
        self.shift_highlighter = ScriptHighlighter(
            self.shift_editor.document(),
            "python"
        )

        self.tabs.addTab(
            self.click_editor,
            "Click"
        )
        self.tabs.addTab(
            self.shift_editor,
            "Shift+Click"
        )

        self.root_layout.addWidget(
            self.tabs,
            1
        )

        actions = QtGui.QHBoxLayout()

        run_click = QtGui.QPushButton(
            "Run Click"
        )
        run_shift = QtGui.QPushButton(
            "Run Shift"
        )

        actions.addWidget(
            run_click
        )
        actions.addWidget(
            run_shift
        )
        actions.addStretch(
            1
        )

        self.root_layout.addLayout(
            actions
        )

        self.language.currentIndexChanged.connect(
            self._language_changed
        )
        self.color_button.clicked.connect(
            self.choose_color
        )
        self.click_editor.textChanged.connect(
            self._control_changed
        )
        self.shift_editor.textChanged.connect(
            self._control_changed
        )

        run_click.clicked.connect(
            self.run_click
        )
        run_shift.clicked.connect(
            self.run_shift
        )

    def current_language(self):
        return (
            "mel"
            if self.language.currentIndex() == 1
            else "python"
        )

    def _language_changed(
        self,
        *args
    ):
        language = self.current_language()

        self.click_highlighter.set_language(
            language
        )
        self.shift_highlighter.set_language(
            language
        )
        self._control_changed()

    def load_specific(
        self,
        item
    ):
        language = item.get(
            "language",
            "python"
        )

        self.language.setCurrentIndex(
            1
            if language == "mel"
            else 0
        )

        self.color = safe_color(
            item.get(
                "color"
            )
        )
        self._refresh_color()

        self.click_editor.setPlainText(
            text_type(
                item.get(
                    "click_script",
                    ""
                )
            )
        )
        self.shift_editor.setPlainText(
            text_type(
                item.get(
                    "shift_script",
                    ""
                )
            )
        )

        self.click_highlighter.set_language(
            language
        )
        self.shift_highlighter.set_language(
            language
        )

    def _refresh_color(self):
        rgb = [
            int(value * 255)
            for value in self.color
        ]

        self.color_button.setStyleSheet(
            "QPushButton { background-color: rgb(%d,%d,%d); }" %
            (
                rgb[0],
                rgb[1],
                rgb[2]
            )
        )

    def choose_color(self):
        initial = QtGui.QColor(
            int(self.color[0] * 255),
            int(self.color[1] * 255),
            int(self.color[2] * 255)
        )

        chosen = QtGui.QColorDialog.getColor(
            initial,
            self,
            "Choose Button Color"
        )

        if not chosen.isValid():
            return

        self.color = [
            chosen.red() / 255.0,
            chosen.green() / 255.0,
            chosen.blue() / 255.0
        ]
        self._refresh_color()
        self._control_changed()

    def write_specific(
        self,
        item
    ):
        item["language"] = self.current_language()
        item["color"] = safe_color(
            self.color
        )
        item["click_script"] = text_type(
            self.click_editor.toPlainText()
        )
        item["shift_script"] = text_type(
            self.shift_editor.toPlainText()
        )

    def run_click(self):
        self.write_to_item()

        if self.item is None:
            return

        execute_script(
            self.item.get(
                "click_script",
                ""
            ),
            self.item.get(
                "language",
                "python"
            ),
            parent=self,
            toolbox=self.toolbox
        )

    def run_shift(self):
        self.write_to_item()

        if self.item is None:
            return

        execute_script(
            self.item.get(
                "shift_script",
                ""
            ),
            self.item.get(
                "language",
                "python"
            ),
            parent=self,
            toolbox=self.toolbox
        )


__all__ = [
    "ButtonPropertyEditor",
]
