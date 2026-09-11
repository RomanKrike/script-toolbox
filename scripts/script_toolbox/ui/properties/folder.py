# -*- coding: utf-8 -*-
from __future__ import print_function

from ...compat import QtGui
from .base import PropertyEditorBase


_GENERIC_FOLDER_LABELS = (
    "Folder",
    "New Folder",
)
_GENERIC_TAB_LABELS = (
    "Tab",
    "New Tab",
)


class FolderPropertyEditor(PropertyEditorBase):

    TYPES = (
        ("Collapsible Section", "collapsible"),
        ("Simple Section", "simple"),
        ("Tabs", "tabs"),
        ("Radio Buttons", "radio"),
    )

    def __init__(self, toolbox=None, parent=None):
        PropertyEditorBase.__init__(self, toolbox, parent)

        self.folder_type = QtGui.QComboBox()
        for label, value in self.TYPES:
            self.folder_type.addItem(label, value)

        self.collapsed = QtGui.QCheckBox()

        self.behavior_section.addRow(
            "Folder Type",
            self.folder_type
        )
        self.behavior_section.addRow(
            "Collapsed by Default",
            self.collapsed
        )

        note = QtGui.QLabel(
            "Collapsible = clickable section header. Simple = always open. "
            "Tabs and Radio Buttons group consecutive sibling Folders of the "
            "same type."
        )
        note.setObjectName("HintText")
        note.setWordWrap(True)
        self.behavior_section.addWidget(note)
        self.add_stretch()

        self.folder_type.currentIndexChanged.connect(
            self._folder_type_changed
        )
        self.collapsed.toggled.connect(self._control_changed)

    def _folder_type_changed(self, *args):
        if not self.loading:
            self._update_generic_label_for_type()
        self._refresh_collapsed_availability()
        self._control_changed()

    def _update_generic_label_for_type(self):
        label = str(self.label_edit.text())
        folder_type = self.current_folder_type()

        if folder_type == "tabs" and label in _GENERIC_FOLDER_LABELS:
            self.label_edit.setText("New Tab")
        elif folder_type != "tabs" and label in _GENERIC_TAB_LABELS:
            self.label_edit.setText("New Folder")

    def _refresh_collapsed_availability(self):
        self.set_property_available(
            self.collapsed,
            self.current_folder_type() == "collapsible",
            "Collapsed by default applies only to Collapsible Section."
        )

    def current_folder_type(self):
        index = self.folder_type.currentIndex()
        if index < 0:
            return "collapsible"

        data = self.folder_type.itemData(index)
        try:
            data = data.toString()
        except Exception:
            pass
        return str(data)

    def load_specific(self, item):
        target = item.get("folder_type", "collapsible")
        index = 0
        for item_index, pair in enumerate(self.TYPES):
            if pair[1] == target:
                index = item_index
                break

        self.folder_type.setCurrentIndex(index)
        self.collapsed.setChecked(
            bool(item.get("collapsed", False))
        )
        self._refresh_collapsed_availability()

    def write_specific(self, item):
        folder_type = self.current_folder_type()
        item["folder_type"] = folder_type
        item["collapsed"] = (
            bool(self.collapsed.isChecked())
            if folder_type == "collapsible"
            else False
        )


__all__ = [
    "FolderPropertyEditor",
]
