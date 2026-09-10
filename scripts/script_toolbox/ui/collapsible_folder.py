# -*- coding: utf-8 -*-
from __future__ import print_function

from ..compat import QtCore
from ..compat import QtGui
from ..pycompat import text_type
from ..style.builtin_icons import builtin_icon
from ..style.metrics import PROPERTY_EDITOR_SPACING
from ..style.metrics import PROPERTY_GROUP_MARGINS


COLLAPSIBLE_FOLDER_ICON_SIZE = 12
COLLAPSIBLE_FOLDER_CONTENT_MARGINS = PROPERTY_GROUP_MARGINS
COLLAPSIBLE_FOLDER_CONTENT_SPACING = PROPERTY_EDITOR_SPACING
_RUNTIME_PATCH_MARKER = "_script_toolbox_shared_collapsible_folder_ui"


def configure_collapsible_folder_frame(frame, nested=False):
    """Apply the shared card styling contract to one collapsible folder."""
    frame.setObjectName("RuntimeFolder")
    frame.setProperty("folderType", "collapsible")
    frame.setProperty("nested", bool(nested))


def configure_collapsible_folder_header(
    header,
    title="",
    tooltip=""
):
    """Configure a full-width folder header shared by runtime and Inspector."""
    header.setObjectName("RuntimeFolderHeader")
    header.setText(text_type(title or ""))
    header.setSizePolicy(
        QtGui.QSizePolicy.Expanding,
        QtGui.QSizePolicy.Preferred
    )
    header.setFocusPolicy(QtCore.Qt.NoFocus)
    header.setStyleSheet(
        "QPushButton#RuntimeFolderHeader {"
        "text-align: left;"
        "}"
    )
    header.setToolTip(text_type(tooltip or ""))
    try:
        header.setIconSize(
            QtCore.QSize(
                COLLAPSIBLE_FOLDER_ICON_SIZE,
                COLLAPSIBLE_FOLDER_ICON_SIZE
            )
        )
    except Exception:
        pass
    return header


def configure_collapsible_folder_content(content, layout):
    """Use the Inspector spacing contract inside collapsible runtime folders."""
    content.setObjectName("RuntimeFolderContent")
    layout.setContentsMargins(
        COLLAPSIBLE_FOLDER_CONTENT_MARGINS[0],
        COLLAPSIBLE_FOLDER_CONTENT_MARGINS[1],
        COLLAPSIBLE_FOLDER_CONTENT_MARGINS[2],
        COLLAPSIBLE_FOLDER_CONTENT_MARGINS[3]
    )
    layout.setSpacing(COLLAPSIBLE_FOLDER_CONTENT_SPACING)
    return layout


def set_collapsible_folder_state(
    frame,
    header,
    content,
    title,
    collapsed
):
    """Update shared collapse visuals without owning persistence."""
    collapsed = bool(collapsed)
    content.setVisible(not collapsed)
    frame.setProperty("collapsed", collapsed)

    if header is not None:
        header.setText(text_type(title or ""))
        header.setIcon(
            builtin_icon(
                "right" if collapsed else "down"
            )
        )
        header.setProperty("collapsed", collapsed)

    # Dynamic QSS properties do not always repaint immediately in Qt4.
    try:
        frame.style().unpolish(frame)
        frame.style().polish(frame)
        if header is not None:
            header.style().unpolish(header)
            header.style().polish(header)
    except Exception:
        pass


def install_runtime_folder_chrome(runtime_module):
    """Patch legacy RuntimeFolder to use the shared Inspector folder chrome.

    RuntimeFolder keeps all existing data/state behavior. Only presentation is
    replaced: header icon, card hooks and collapsible content geometry.
    """
    if getattr(runtime_module, _RUNTIME_PATCH_MARKER, False):
        return runtime_module.RuntimeFolder

    base_class = runtime_module.RuntimeFolder

    class SharedRuntimeFolder(base_class):

        def __init__(
            self,
            toolbox,
            section,
            parent=None,
            embedded=False
        ):
            base_class.__init__(
                self,
                toolbox,
                section,
                parent=parent,
                embedded=embedded
            )

            if self.folder_type != "collapsible":
                return

            configure_collapsible_folder_frame(
                self,
                nested=self.is_nested
            )
            if self.header_button is not None:
                configure_collapsible_folder_header(
                    self.header_button,
                    self.header_label,
                    section.get("tooltip", "")
                )
            configure_collapsible_folder_content(
                self.content,
                self.content_layout
            )
            self.update_state()

        def update_state(self):
            if (
                self.embedded or
                self.folder_type != "collapsible"
            ):
                self.content.setVisible(True)
                return

            set_collapsible_folder_state(
                self,
                self.header_button,
                self.content,
                self.header_label,
                bool(
                    self.section.get(
                        "collapsed",
                        False
                    )
                )
            )

    try:
        SharedRuntimeFolder.__name__ = "RuntimeFolder"
    except Exception:
        pass

    runtime_module.RuntimeFolder = SharedRuntimeFolder
    runtime_module.RuntimeSection = SharedRuntimeFolder
    setattr(runtime_module, _RUNTIME_PATCH_MARKER, True)
    return SharedRuntimeFolder


__all__ = [
    "COLLAPSIBLE_FOLDER_CONTENT_MARGINS",
    "COLLAPSIBLE_FOLDER_CONTENT_SPACING",
    "COLLAPSIBLE_FOLDER_ICON_SIZE",
    "configure_collapsible_folder_content",
    "configure_collapsible_folder_frame",
    "configure_collapsible_folder_header",
    "install_runtime_folder_chrome",
    "set_collapsible_folder_state",
]
