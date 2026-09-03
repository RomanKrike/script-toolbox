# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtGui


class ExistingInterfaceTree(QtGui.QTreeWidget):

    def __init__(
        self,
        editor,
        parent=None
    ):
        QtGui.QTreeWidget.__init__(
            self,
            parent
        )

        self.editor = editor

        self.setHeaderLabels(
            [
                "Existing Interface",
                "Name",
                "Type"
            ]
        )
        self.setColumnWidth(
            0,
            210
        )
        self.setColumnWidth(
            1,
            150
        )
        self.setSelectionMode(
            QtGui.QAbstractItemView.SingleSelection
        )
        self.setDragEnabled(
            True
        )
        self.setAcceptDrops(
            True
        )
        self.setDropIndicatorShown(
            True
        )
        self.setDragDropMode(
            QtGui.QAbstractItemView.InternalMove
        )

    def dropEvent(
        self,
        event
    ):
        current = self.currentItem()

        # Folders, Rows and normal items can be moved through the tree.
        # fix_tree_structure() normalizes invalid destinations afterwards.
        QtGui.QTreeWidget.dropEvent(
            self,
            event
        )

        self.editor.fix_tree_structure()
        self.editor.tree_changed()


# ----------------------------------------------------------------------
# Interface Editor
# ----------------------------------------------------------------------


__all__ = [
    "ExistingInterfaceTree",
]
