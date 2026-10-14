# -*- coding: utf-8 -*-
from __future__ import print_function

import os

from ..compat import QtCore
from ..compat import QtGui
from ..model.items import clamp
from ..pycompat import text_type
from ..style import metrics, palette
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


class FilenameLabel(QtGui.QLabel):
    """Keep long filenames inside the fixed image width."""
    def set_filename(self, filename):
        self.filename = filename
        self.setToolTip(filename)
        self._update_text()

    def _update_text(self):
        self.setText(self.fontMetrics().elidedText(
            getattr(self, "filename", ""), QtCore.Qt.ElideMiddle, self.width()))

    def resizeEvent(self, event):
        QtGui.QLabel.resizeEvent(self, event)
        self._update_text()


def render_image(owner, item, compact=False):
    frame = QtGui.QFrame()
    frame.setObjectName("RuntimeImage")
    frame.setStyleSheet(
        "QFrame#RuntimeImage {background: %s; border: 1px solid %s; "
        "border-radius: %dpx;}" % (
            palette.PANEL_BG, palette.TOOLTIP_BORDER, metrics.BORDER_RADIUS_CARD))
    layout = QtGui.QVBoxLayout(frame)
    padding = metrics.IMAGE_FRAME_PADDING
    layout.setContentsMargins(padding, padding, padding, padding)
    layout.setSpacing(metrics.FORM_INLINE_SPACING)
    frame.image_label = QtGui.QLabel()
    frame.filename_label = FilenameLabel()
    for label in (frame.image_label, frame.filename_label):
        label.setStyleSheet("border: none; background: transparent;")
        label.setTextFormat(QtCore.Qt.PlainText)
        layout.addWidget(label)
    frame.filename_label.setAlignment(QtCore.Qt.AlignLeft)
    update_image(frame, item)
    return frame


def update_image(frame, item):
    label = frame.image_label
    props = item.get("props", {}) or {}
    ui = item.get("ui", {}) or {}
    width = int(props.get("width", 200))
    height = int(props.get("height", 120))
    fit = text_type(props.get("fit", "contain")).lower()
    if fit not in ("contain", "cover", "stretch"):
        fit = "contain"

    label.setFixedSize(width, height)
    label.setAlignment(QtCore.Qt.AlignCenter)
    frame.setToolTip(ui.get("tooltip", ""))

    source = _expanded_path(props.get("source"))
    filename = source.replace("\\", "/").rsplit("/", 1)[-1]
    caption = frame.filename_label
    caption.setFixedWidth(width)
    caption.set_filename(filename)
    show_filename = bool(props.get("show_filename", True) and filename)
    caption.setVisible(show_filename)
    extra = (caption.sizeHint().height() + metrics.FORM_INLINE_SPACING
             if show_filename else 0)
    padding = metrics.IMAGE_FRAME_PADDING * 2
    frame.setFixedSize(width + padding, height + padding + extra)
    pixmap = QtGui.QPixmap(source) if source else QtGui.QPixmap()
    pixmap = _scaled_pixmap(pixmap, width, height, fit)

    if pixmap.isNull():
        label.clear()
        label.setText("Image")
    else:
        label.setPixmap(pixmap)


class ImagePropertyEditor(PropertyEditorBase):
    def __init__(self, toolbox=None, parent=None):
        PropertyEditorBase.__init__(self, toolbox, parent)

        self.source = QtGui.QLineEdit()
        self.browse = QtGui.QPushButton("Browse...")
        self.fit = QtGui.QComboBox()
        self.fit.addItems(["Contain", "Cover", "Stretch"])
        self.show_filename = QtGui.QCheckBox("Show filename")
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
        self.appearance_section.addRow("", self.show_filename)
        self.appearance_section.addRow("Image Width", self.width)
        self.appearance_section.addRow("Image Height", self.height)
        self.add_stretch()

        self.source.textEdited.connect(self._control_changed)
        self.fit.currentIndexChanged.connect(self._control_changed)
        self.show_filename.toggled.connect(self._control_changed)
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

    def load_specific(self, props):
        self.source.setText(text_type(props.get("source", "")))
        self.show_filename.setChecked(bool(props.get("show_filename", True)))
        self.fit.setCurrentIndex({
            "contain": 0,
            "cover": 1,
            "stretch": 2,
        }.get(text_type(props.get("fit", "contain")).lower(), 0))
        self.width.setValue(int(props.get("width", 200)))
        self.height.setValue(int(props.get("height", 120)))

    def write_specific(self, props):
        props["source"] = text_type(self.source.text())
        props["show_filename"] = self.show_filename.isChecked()
        props["fit"] = (
            "stretch"
            if self.fit.currentIndex() == 2
            else "cover"
            if self.fit.currentIndex() == 1
            else "contain"
        )
        props["width"] = clamp(int(self.width.value()), 8, 4096)
        props["height"] = clamp(int(self.height.value()), 8, 4096)


__all__ = [
    "ImagePropertyEditor",
    "render_image",
]
