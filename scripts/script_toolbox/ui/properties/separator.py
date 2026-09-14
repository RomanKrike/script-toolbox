# -*- coding: utf-8 -*-
from __future__ import print_function

from ...pycompat import text_type
from .base import PropertyEditorBase
from .basic import SeparatorPropertyEditor as _SeparatorPropertyEditor


class SeparatorPropertyEditor(_SeparatorPropertyEditor):
    def write_to_item(self):
        if self.item is None:
            return

        PropertyEditorBase.write_to_item(self)
        self.item["name"] = text_type(
            self.name_edit.text()
        ).strip() or "separator"
        self.item["bindings"] = []


__all__ = [
    "SeparatorPropertyEditor",
]
