# -*- coding: utf-8 -*-
from __future__ import print_function

from .editor_document import EditorDocumentController


class LayoutEditorDocumentController(EditorDocumentController):
    """Backward-compatible name for the canonical editor document controller."""
    pass


__all__ = [
    "LayoutEditorDocumentController",
]
