# -*- coding: utf-8 -*-
from __future__ import print_function

from ...compat import QtGui
from ...pycompat import text_type
from ...style import metrics
from .base import PropertyEditorBase


class TextPropertyEditor(PropertyEditorBase):

    def __init__(self, toolbox=None, parent=None):
        PropertyEditorBase.__init__(
            self,
            toolbox,
            parent
        )

        self.text_edit = QtGui.QPlainTextEdit()
        self.text_edit.setMinimumHeight(
            metrics.PROPERTY_MULTILINE_TEXT_MIN_HEIGHT
        )
        self.content_section.addRow(
            "Text",
            self.text_edit
        )

        self.set_property_available(
            self.label_edit,
            False,
            "Text content is edited in the multiline Text field."
        )
        self.set_property_available(
            self.show_label_check,
            False,
            "Text items render their content directly without a separate label."
        )

        self.add_stretch()

        self.text_edit.textChanged.connect(
            self._control_changed
        )

    def load_specific(self, item):
        self.text_edit.setPlainText(
            text_type(item.get("text", ""))
        )

    def write_specific(self, item):
        item["text"] = text_type(
            self.text_edit.toPlainText()
        )
        item["show_label"] = False
        item["bindings"] = []


__all__ = [
    "TextPropertyEditor",
]
