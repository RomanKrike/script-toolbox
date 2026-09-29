# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtGui
from ..pycompat import text_type
from ..style import metrics
from ..style import palette


def build_page_header(title_text, description_text, parent=None):
    """Build the shared title/description header used by Settings pages."""
    header = QtGui.QWidget(parent)
    layout = QtGui.QVBoxLayout(header)
    layout.setContentsMargins(*metrics.MARGINS_NONE)
    layout.setSpacing(metrics.SETTINGS_HEADER_SPACING)

    title = QtGui.QLabel(text_type(title_text), header)
    title.setObjectName("SettingsPageTitle")
    title_font = title.font()
    title_font.setBold(True)
    title_font.setPointSize(title_font.pointSize() + 2)
    title.setFont(title_font)
    layout.addWidget(title)

    description = QtGui.QLabel(text_type(description_text), header)
    description.setObjectName("SettingsPageDescription")
    description.setWordWrap(True)
    layout.addWidget(description)
    return header


def build_simple_section(title_text, tooltip="", nested=False, parent=None):
    """Build Settings chrome from the existing Runtime Simple Section contract."""
    section = QtGui.QGroupBox(text_type(title_text), parent)
    section.setObjectName("SimpleSectionGroupBox")
    section.setProperty("nested", bool(nested))
    section.setToolTip(text_type(tooltip or ""))

    section_layout = QtGui.QVBoxLayout(section)
    section_layout.setContentsMargins(*metrics.RUNTIME_FOLDER_ROOT_MARGINS)
    section_layout.setSpacing(metrics.RUNTIME_FOLDER_ROOT_SPACING)

    content = QtGui.QWidget(section)
    content.setObjectName("RuntimeFolderContent")
    content_layout = QtGui.QVBoxLayout(content)
    content_layout.setContentsMargins(*metrics.RUNTIME_FOLDER_CONTENT_MARGINS)
    content_layout.setSpacing(metrics.RUNTIME_FOLDER_CONTENT_SPACING)

    section_layout.addWidget(content)
    return section, content_layout


def build_section_form():
    form = QtGui.QFormLayout()
    form.setContentsMargins(*metrics.MARGINS_NONE)
    form.setSpacing(metrics.RUNTIME_FOLDER_CONTENT_SPACING)
    return form


def _apply_content_palette(widget):
    """Qt4 fallback for widgets whose viewport ignores inherited QSS."""
    if widget is None:
        return

    try:
        widget_palette = widget.palette()
        widget_palette.setColor(
            QtGui.QPalette.Window,
            QtGui.QColor(palette.CONTENT_BG)
        )
        widget_palette.setColor(
            QtGui.QPalette.Base,
            QtGui.QColor(palette.CONTENT_BG)
        )
        widget_palette.setColor(
            QtGui.QPalette.Text,
            QtGui.QColor(palette.TEXT_PRIMARY)
        )
        widget.setPalette(widget_palette)
        widget.setAutoFillBackground(True)
    except Exception:
        pass


def configure_settings_scroll_area(scroll):
    """Apply the shared Settings surface contract to a QScrollArea.

    Maya 2015 / Qt4 can keep the native light Base color on the internal
    viewport even while the parent QScrollArea inherits the application QSS.
    The object names keep normal styling in QSS; the palette assignment is a
    compatibility fallback using the same shared palette values.
    """
    if scroll is None:
        return None

    scroll.setObjectName("SettingsScroll")
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QtGui.QFrame.NoFrame)
    _apply_content_palette(scroll)

    try:
        viewport = scroll.viewport()
    except Exception:
        viewport = None

    if viewport is not None:
        viewport.setObjectName("SettingsScrollViewport")
        _apply_content_palette(viewport)

    return scroll


def mark_secondary_text(label):
    if label is not None:
        label.setObjectName("SettingsSecondaryText")
    return label


def mark_status_text(label):
    if label is not None:
        label.setObjectName("SettingsStatusText")
    return label


__all__ = [
    "build_page_header",
    "build_section_form",
    "build_simple_section",
    "configure_settings_scroll_area",
    "mark_secondary_text",
    "mark_status_text",
]
