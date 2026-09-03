# -*- coding: utf-8 -*-
from __future__ import print_function

from ...compat import HOST
from ...compat import QtGui
from ...model.items import safe_color
from ...pycompat import text_type
from ..script_editor import ScriptEditorWidget
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
        self.languages = list(
            HOST.available_languages()
        )

        for language in self.languages:
            self.language.addItem(
                language.upper()
                if language == "mel"
                else language.title()
            )

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

        self.click_editor = ScriptEditorWidget(
            language="python",
            toolbox=self.toolbox
        )
        self.shift_editor = ScriptEditorWidget(
            language="python",
            toolbox=self.toolbox
        )

        self.tabs.addTab(
            self.click_editor,
            "Click Script"
        )
        self.tabs.addTab(
            self.shift_editor,
            "Shift + Click"
        )

        self.root_layout.addWidget(
            self.tabs,
            1
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


    def current_language(self):
        index = self.language.currentIndex()

        if (
            index < 0 or
            index >= len(
                self.languages
            )
        ):
            return "python"

        return self.languages[
            index
        ]

    def _language_changed(
        self,
        *args
    ):
        language = self.current_language()

        self.click_editor.set_language(
            language
        )
        self.shift_editor.set_language(
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

        if language not in self.languages:
            self.languages.append(
                language
            )
            self.language.addItem(
                "{0} (Unavailable in {1})".format(
                    language.upper(),
                    HOST.display_name
                )
            )

        self.language.setCurrentIndex(
            self.languages.index(
                language
            )
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

        self.click_editor.set_language(
            language
        )
        self.shift_editor.set_language(
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
        return self.click_editor.run()

    def run_shift(self):
        self.write_to_item()
        return self.shift_editor.run()


__all__ = [
    "ButtonPropertyEditor",
]
