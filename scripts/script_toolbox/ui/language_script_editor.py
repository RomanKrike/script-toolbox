# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import HOST
from ..compat import QtCore
from ..compat import QtGui
from ..pycompat import text_type
from .script_editor import ScriptEditorWidget


class LanguageScriptEditor(QtGui.QWidget):
    """Script editor with language owned by this script, not its parent item."""

    textChanged = QtCore.Signal()
    languageChanged = QtCore.Signal()

    def __init__(
        self,
        language="python",
        toolbox=None,
        parent=None
    ):
        QtGui.QWidget.__init__(
            self,
            parent
        )

        self.toolbox = toolbox
        self.languages = list(
            HOST.available_languages()
        )
        if "python" not in self.languages:
            self.languages.insert(0, "python")

        root = QtGui.QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)

        language_row = QtGui.QHBoxLayout()
        language_row.setSpacing(5)
        language_row.addWidget(
            QtGui.QLabel("Language")
        )

        self.language_combo = QtGui.QComboBox()
        for entry in self.languages:
            self.language_combo.addItem(
                entry.upper()
                if entry == "mel"
                else entry.title()
            )
        language_row.addWidget(
            self.language_combo
        )
        language_row.addStretch(1)
        root.addLayout(language_row)

        self.editor = ScriptEditorWidget(
            language=language,
            toolbox=toolbox,
            parent=self
        )
        root.addWidget(
            self.editor,
            1
        )

        self.editor.textChanged.connect(
            self.textChanged.emit
        )
        self.language_combo.currentIndexChanged.connect(
            self._language_changed
        )

        self.set_language(language)

    @property
    def run_button(self):
        return self.editor.run_button

    def _language_changed(self, *args):
        language = self.language()
        self.editor.set_language(language)
        self.languageChanged.emit()

    def language(self):
        index = self.language_combo.currentIndex()
        if index < 0 or index >= len(self.languages):
            return "python"
        return self.languages[index]

    def set_language(self, language):
        language = text_type(language or "python").lower()

        if language not in self.languages:
            self.languages.append(language)
            self.language_combo.addItem(
                "{0} (Unavailable in {1})".format(
                    language.upper(),
                    HOST.display_name
                )
            )

        self.language_combo.blockSignals(True)
        try:
            self.language_combo.setCurrentIndex(
                self.languages.index(language)
            )
            self.editor.set_language(language)
        finally:
            self.language_combo.blockSignals(False)

    def set_language_enabled(self, enabled, tooltip=""):
        self.language_combo.setEnabled(bool(enabled))
        if tooltip:
            self.language_combo.setToolTip(
                text_type(tooltip)
            )

    def setPlainText(self, value):
        self.editor.setPlainText(value)

    def toPlainText(self):
        return self.editor.toPlainText()

    def setMinimumHeight(self, value):
        QtGui.QWidget.setMinimumHeight(self, value)

    def set_output_visible(self, visible):
        self.editor.set_output_visible(visible)

    def set_toolbox(self, toolbox):
        self.toolbox = toolbox
        self.editor.set_toolbox(toolbox)

    def run(self):
        return self.editor.run()


__all__ = [
    "LanguageScriptEditor",
]
