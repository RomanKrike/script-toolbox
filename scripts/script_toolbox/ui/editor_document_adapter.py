# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtGui
from ..core.editor_document import EditorDocumentController
from .interface_editor import InterfaceEditor as _LegacyInterfaceEditor


class InterfaceEditor(_LegacyInterfaceEditor):
    """Compatibility adapter that moves staged-document ownership to core."""

    def __init__(self, toolbox, parent=None):
        self.document_controller = EditorDocumentController(
            toolbox.config
        )
        _LegacyInterfaceEditor.__init__(
            self,
            toolbox,
            parent=parent
        )

    @property
    def working(self):
        return self.document_controller.document

    @working.setter
    def working(self, document):
        # Legacy InterfaceEditor callers already copy/normalize external
        # documents before assignment. Internal tree synchronization assembles
        # the current item dicts directly, so adopt preserves those references.
        self.document_controller.adopt(document)

    @property
    def item_cache(self):
        return self.document_controller.item_cache

    @item_cache.setter
    def item_cache(self, mapping):
        self.document_controller.replace_index(mapping)

    def rebuild_cache(self):
        self.document_controller.rebuild_index()

    def _used_names(self):
        return self.document_controller.used_names()

    def _unique_name(self, base, used_names):
        return self.document_controller.unique_name(
            base,
            used_names
        )

    def _clone_data(self, data, used_names=None):
        return self.document_controller.clone_subtree(
            data,
            used_names
        )

    def _cache_subtree(self, data):
        self.document_controller.cache_subtree(data)

    def validate_internal_names(self):
        duplicate = self.document_controller.duplicate_name()

        if duplicate is None:
            return True

        QtGui.QMessageBox.warning(
            self,
            "Duplicate Name",
            "Name '{0}' is used more than once.".format(
                duplicate
            )
        )
        return False


__all__ = [
    "InterfaceEditor",
]
