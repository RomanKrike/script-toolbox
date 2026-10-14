# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore, QtGui
from .palette_drag import (drag_source, drop_location, event_position,
                           insert_palette_drop, PALETTE_MIME)


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
            QtGui.QAbstractItemView.DragDrop
        )

        self.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.setAutoExpandDelay(700)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(PALETTE_MIME):
            if drag_source(self, event) is None:
                event.ignore()
                return
        elif event.source() is not self:
            event.ignore()
            return
        QtGui.QTreeWidget.dragEnterEvent(self, event)

    def dragMoveEvent(self, event):
        QtGui.QTreeWidget.dragMoveEvent(self, event)
        if event.mimeData().hasFormat(PALETTE_MIME):
            source = drag_source(self, event)
            target = self.itemAt(event_position(event))
            location = drop_location(self, target, self.dropIndicatorPosition(), source[1]) if source else None
            if location is None:
                event.ignore()
            else:
                event.setDropAction(QtCore.Qt.CopyAction)
                event.accept()

    def dropEvent(
        self,
        event
    ):
        if event.mimeData().hasFormat(PALETTE_MIME):
            source = drag_source(self, event)
            target = self.itemAt(event_position(event))
            location = drop_location(self, target, self.dropIndicatorPosition(), source[1]) if source else None
            if location is None:
                event.ignore()
                return
            parent, index = location
            result = self.editor._call_tree_action(
                "Create Parameter" if "kind" in source[0] else "Insert Preset",
                insert_palette_drop, source[0], parent, index)
            if result is not None:
                event.setDropAction(QtCore.Qt.CopyAction)
                event.accept()
            else:
                event.ignore()
            return
        if event.source() is not self:
            event.ignore()
            return
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
