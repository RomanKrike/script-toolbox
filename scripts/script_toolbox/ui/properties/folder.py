# -*- coding: utf-8 -*-
from __future__ import print_function

from ...compat import QtGui
from .base import PropertyEditorBase


class FolderPropertyEditor(PropertyEditorBase):

    TYPES = (
        ("Collapsible Section", "collapsible"),
        ("Simple Section", "simple"),
        ("Tabs", "tabs"),
        ("Radio Buttons", "radio"),
    )

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

        self.folder_type = QtGui.QComboBox()

        for label, value in self.TYPES:
            self.folder_type.addItem(
                label,
                value
            )

        self.collapsed = QtGui.QCheckBox(
            "Collapsed by default"
        )

        self.form.addRow(
            "Folder Type",
            self.folder_type
        )
        self.form.addRow(
            "",
            self.collapsed
        )

        note = QtGui.QLabel(
            "Collapsible = clickable section header. Simple = always open. "
            "Tabs and Radio Buttons group consecutive sibling Folders "
            "of the same type."
        )
        note.setObjectName(
            "HintText"
        )
        note.setWordWrap(
            True
        )
        self.root_layout.addWidget(
            note
        )
        self.add_stretch()

        self.folder_type.currentIndexChanged.connect(
            self._folder_type_changed
        )
        self.collapsed.toggled.connect(
            self._control_changed
        )

    def _folder_type_changed(
        self,
        *args
    ):
        self.collapsed.setEnabled(
            self.current_folder_type() ==
            "collapsible"
        )
        self._control_changed()

    def current_folder_type(self):
        index = self.folder_type.currentIndex()

        if index < 0:
            return "collapsible"

        data = self.folder_type.itemData(
            index
        )

        try:
            data = data.toString()
        except Exception:
            pass

        return str(
            data
        )

    def load_specific(
        self,
        item
    ):
        target = item.get(
            "folder_type",
            "collapsible"
        )

        index = 0

        for item_index, pair in enumerate(
            self.TYPES
        ):
            if pair[1] == target:
                index = item_index
                break

        self.folder_type.setCurrentIndex(
            index
        )
        self.collapsed.setChecked(
            bool(
                item.get(
                    "collapsed",
                    False
                )
            )
        )
        self.collapsed.setEnabled(
            target ==
            "collapsible"
        )

    def write_specific(
        self,
        item
    ):
        folder_type = self.current_folder_type()

        item["folder_type"] = folder_type
        item["collapsed"] = (
            bool(
                self.collapsed.isChecked()
            )
            if folder_type == "collapsible"
            else False
        )


__all__ = [
    "FolderPropertyEditor",
]
