# -*- coding: utf-8 -*-
from __future__ import print_function

import os

from ..compat import QtCore
from ..compat import QtGui
from ..model.items import clamp
from ..pycompat import text_type
from .properties.base import PropertyEditorBase


_IMAGE_FILTER = "Images (*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff);;All Files (*)"


def _expanded_path(value):
    return os.path.expanduser(
        os.path.expandvars(text_type(value or ""))
    )


def _scaled_pixmap(pixmap, width, height, fit):
    if pixmap.isNull():
        return pixmap

    if fit == "stretch":
        return pixmap.scaled(
            width,
            height,
            QtCore.Qt.IgnoreAspectRatio,
            QtCore.Qt.SmoothTransformation
        )

    aspect_mode = (
        QtCore.Qt.KeepAspectRatioByExpanding
        if fit == "cover"
        else QtCore.Qt.KeepAspectRatio
    )
    result = pixmap.scaled(
        width,
        height,
        aspect_mode,
        QtCore.Qt.SmoothTransformation
    )

    if fit != "cover":
        return result

    x = max(0, int((result.width() - width) / 2))
    y = max(0, int((result.height() - height) / 2))
    return result.copy(x, y, width, height)


def render_image(owner, item, compact=False):
    width = int(item.get("width", 200))
    height = int(item.get("height", 120))
    fit = text_type(item.get("fit", "contain")).lower()
    if fit not in ("contain", "cover", "stretch"):
        fit = "contain"

    label = QtGui.QLabel()
    label.setObjectName("RuntimeImage")
    label.setFixedSize(width, height)
    label.setAlignment(QtCore.Qt.AlignCenter)
    label.setToolTip(owner._tooltip(item))

    source = _expanded_path(item.get("source"))
    pixmap = QtGui.QPixmap(source) if source else QtGui.QPixmap()
    pixmap = _scaled_pixmap(pixmap, width, height, fit)

    if pixmap.isNull():
        label.setText("Image")
    else:
        label.setPixmap(pixmap)

    return label


class ImagePropertyEditor(PropertyEditorBase):
    def __init__(self, toolbox=None, parent=None):
        PropertyEditorBase.__init__(self, toolbox, parent)

        self.source = QtGui.QLineEdit()
        self.browse = QtGui.QPushButton("Browse...")
        self.fit = QtGui.QComboBox()
        self.fit.addItems(["Contain", "Cover", "Stretch"])
        self.width = QtGui.QSpinBox()
        self.width.setRange(8, 4096)
        self.height = QtGui.QSpinBox()
        self.height.setRange(8, 4096)

        source_row = QtGui.QWidget()
        source_layout = QtGui.QHBoxLayout(source_row)
        source_layout.setContentsMargins(0, 0, 0, 0)
        source_layout.setSpacing(4)
        source_layout.addWidget(self.source, 1)
        source_layout.addWidget(self.browse, 0)

        self.content_section.addRow("Source", source_row)
        self.appearance_section.addRow("Fit", self.fit)
        self.appearance_section.addRow("Image Width", self.width)
        self.appearance_section.addRow("Image Height", self.height)
        self.add_stretch()

        self.source.textEdited.connect(self._control_changed)
        self.fit.currentIndexChanged.connect(self._control_changed)
        self.width.valueChanged.connect(self._control_changed)
        self.height.valueChanged.connect(self._control_changed)
        self.browse.clicked.connect(self._browse_source)

    def _browse_source(self):
        selected = QtGui.QFileDialog.getOpenFileName(
            self,
            "Choose Image",
            text_type(self.source.text() or ""),
            _IMAGE_FILTER
        )
        if isinstance(selected, (list, tuple)):
            selected = selected[0] if selected else ""
        selected = text_type(selected or "")
        if not selected:
            return
        self.source.setText(selected)
        self._control_changed()

    def load_specific(self, item):
        self.source.setText(text_type(item.get("source", "")))
        self.fit.setCurrentIndex({
            "contain": 0,
            "cover": 1,
            "stretch": 2,
        }.get(text_type(item.get("fit", "contain")).lower(), 0))
        self.width.setValue(int(item.get("width", 200)))
        self.height.setValue(int(item.get("height", 120)))

    def write_specific(self, item):
        item["source"] = text_type(self.source.text())
        item["fit"] = (
            "stretch"
            if self.fit.currentIndex() == 2
            else "cover"
            if self.fit.currentIndex() == 1
            else "contain"
        )
        item["width"] = clamp(int(self.width.value()), 8, 4096)
        item["height"] = clamp(int(self.height.value()), 8, 4096)


__all__ = [
    "ImagePropertyEditor",
    "render_image",
]
