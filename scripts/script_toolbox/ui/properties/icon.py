# -*- coding: utf-8 -*-
from __future__ import print_function

from ...compat import QtGui
from ...model.items import clamp
from ...pycompat import text_type
from ...style.builtin_icons import builtin_icon
from ...style.builtin_icons import builtin_icon_entries
from ...style.builtin_icons import builtin_icon_id_from_path
from ...style.builtin_icons import builtin_icon_resource
from ..icon_browse import install_icon_browse
from .base import PropertyEditorBase


class IconPropertyEditor(PropertyEditorBase):

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

        self._custom_path = ""
        self.icon_source = QtGui.QComboBox()
        self.icon_source.addItem(
            "Custom Path",
            ""
        )

        for icon_id, label in builtin_icon_entries():
            self.icon_source.addItem(
                builtin_icon(icon_id),
                label,
                icon_id
            )

        self.path = QtGui.QLineEdit()
        self.width = QtGui.QSpinBox()
        self.height = QtGui.QSpinBox()
        self.alignment = QtGui.QComboBox()

        self.width.setRange(8, 512)
        self.height.setRange(8, 512)
        self.alignment.addItems([
            "Left",
            "Center",
            "Right",
        ])

        self.form.addRow(
            "Icon",
            self.icon_source
        )
        self.form.addRow(
            "Path",
            self.path
        )
        self.form.addRow(
            "Width",
            self.width
        )
        self.form.addRow(
            "Height",
            self.height
        )
        self.form.addRow(
            "Content Alignment",
            self.alignment
        )

        # The active editor exposes a single path-based icon source. Keep the
        # legacy combo alive for config compatibility, but remove it from the
        # visible form instead of patching these methods after construction.
        try:
            source_label = self.form.labelForField(
                self.icon_source
            )
            if source_label is not None:
                source_label.hide()
        except Exception:
            pass
        self.icon_source.hide()
        self.path.setEnabled(True)
        self.icon_browse_button = install_icon_browse(
            self,
            self.path
        )
        self.add_stretch()

        self.icon_source.currentIndexChanged.connect(
            self._icon_source_changed
        )
        self.path.textEdited.connect(
            self._control_changed
        )
        self.width.valueChanged.connect(
            self._control_changed
        )
        self.height.valueChanged.connect(
            self._control_changed
        )
        self.alignment.currentIndexChanged.connect(
            self._control_changed
        )

    def _selected_builtin_icon(self):
        # Built-in selection is retained only as a hidden legacy data source.
        # The current UI persists the explicit path shown to the user.
        return ""

    def _refresh_icon_source(self):
        try:
            self.path.setEnabled(True)
        except Exception:
            pass

    def _icon_source_changed(self, *args):
        self._refresh_icon_source()
        self._control_changed()

    def load_specific(self, item):
        path = text_type(
            item.get(
                "path",
                ""
            )
        )
        icon_id = builtin_icon_id_from_path(path)

        if icon_id:
            self._custom_path = ""
        else:
            self._custom_path = path

        self.path.setText(path)

        index = self.icon_source.findData(icon_id)
        if index < 0:
            index = 0
        self.icon_source.setCurrentIndex(index)
        self._refresh_icon_source()

        self.width.setValue(
            int(
                item.get(
                    "width",
                    24
                )
            )
        )
        self.height.setValue(
            int(
                item.get(
                    "height",
                    24
                )
            )
        )
        content_alignment = item.get(
            "content_alignment",
            item.get(
                "alignment",
                "left"
            )
        )
        self.alignment.setCurrentIndex({
            "left": 0,
            "center": 1,
            "right": 2,
        }.get(
            content_alignment,
            0
        ))

    def write_specific(self, item):
        icon_id = self._selected_builtin_icon()
        item["path"] = (
            builtin_icon_resource(icon_id)
            if icon_id
            else text_type(self.path.text())
        )
        item["width"] = clamp(
            int(
                self.width.value()
            ),
            8,
            512
        )
        item["height"] = clamp(
            int(
                self.height.value()
            ),
            8,
            512
        )
        content_alignment = (
            "right"
            if self.alignment.currentIndex() == 2
            else "center"
            if self.alignment.currentIndex() == 1
            else "left"
        )
        item["content_alignment"] = content_alignment

        # Keep the schema-18 runtime alias synchronized. Older configs and
        # renderers still read ``alignment``.
        item["alignment"] = content_alignment
        item.pop("clickable", None)


__all__ = [
    "IconPropertyEditor",
]
