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
_RUNTIME_COMPOSITION_MARKER = (
    "_script_toolbox_collapsible_section_composition"
)


class CollapsibleSection(QtGui.QFrame):
    """Reusable collapsible UI primitive with no persistence knowledge.

    The widget owns the complete visual/interaction contract: card, header,
    disclosure SVG, content container, dynamic QSS properties and the Qt4
    repolish workaround. Callers only decide what content is inserted and
    what to do when ``collapsedChanged`` is emitted.
    """

    collapsedChanged = QtCore.Signal(bool)

    def __init__(
        self,
        title="",
        collapsed=False,
        nested=False,
        tooltip="",
        content_margins=None,
        content_spacing=None,
        parent=None
    ):
        QtGui.QFrame.__init__(self, parent)

        self._title = text_type(title or "")
        self._collapsed = False
        self._nested = bool(nested)

        self.setObjectName("RuntimeFolder")
        self.setProperty("folderType", "collapsible")
        self.setProperty("nested", self._nested)

        self.root_layout = QtGui.QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        self.header = QtGui.QPushButton(self)
        self.header.setObjectName("RuntimeFolderHeader")
        self.header.setSizePolicy(
            QtGui.QSizePolicy.Expanding,
            QtGui.QSizePolicy.Preferred
        )
        self.header.setFocusPolicy(QtCore.Qt.NoFocus)
        self.header.setStyleSheet(
            "QPushButton#RuntimeFolderHeader {"
            "text-align: left;"
            "}"
        )
        self.header.setToolTip(text_type(tooltip or ""))
        try:
            self.header.setIconSize(
                QtCore.QSize(
                    COLLAPSIBLE_FOLDER_ICON_SIZE,
                    COLLAPSIBLE_FOLDER_ICON_SIZE
                )
            )
        except Exception:
            pass
        self.root_layout.addWidget(self.header)

        self.content = QtGui.QWidget(self)
        self.content.setObjectName("RuntimeFolderContent")
        self.content_layout = QtGui.QVBoxLayout(self.content)

        margins = (
            COLLAPSIBLE_FOLDER_CONTENT_MARGINS
            if content_margins is None
            else content_margins
        )
        spacing = (
            COLLAPSIBLE_FOLDER_CONTENT_SPACING
            if content_spacing is None
            else content_spacing
        )
        self.content_layout.setContentsMargins(
            margins[0],
            margins[1],
            margins[2],
            margins[3]
        )
        self.content_layout.setSpacing(spacing)
        self.root_layout.addWidget(self.content)

        self.header.clicked.connect(self._header_clicked)
        self.set_collapsed(collapsed, notify=False)

    @property
    def title(self):
        return self._title

    @property
    def collapsed(self):
        return self._collapsed

    @property
    def nested(self):
        return self._nested

    def set_title(self, title):
        self._title = text_type(title or "")
        self._sync_header()

    def set_tooltip(self, tooltip):
        self.header.setToolTip(text_type(tooltip or ""))

    def set_nested(self, nested):
        nested = bool(nested)
        if nested == self._nested:
            return
        self._nested = nested
        self.setProperty("nested", nested)
        self._repolish()

    def _header_clicked(self, checked=False):
        self.toggle()

    def toggle(self):
        self.set_collapsed(
            not self._collapsed,
            notify=True
        )

    def set_collapsed(self, collapsed, notify=False):
        collapsed = bool(collapsed)
        changed = collapsed != self._collapsed
        self._collapsed = collapsed

        self.content.setVisible(not collapsed)
        self.setProperty("collapsed", collapsed)
        self.header.setProperty("collapsed", collapsed)
        self._sync_header()
        self._sync_size_policy()
        self._repolish()

        if changed and notify:
            self.collapsedChanged.emit(collapsed)

    def _sync_header(self):
        self.header.setText(self._title)
        self.header.setIcon(
            builtin_icon(
                "right" if self._collapsed else "down"
            )
        )

    def _sync_size_policy(self):
        try:
            policy = self.sizePolicy()
            policy.setVerticalPolicy(
                QtGui.QSizePolicy.Maximum
                if self._collapsed
                else QtGui.QSizePolicy.Preferred
            )
            self.setSizePolicy(policy)
        except Exception:
            pass

    def _repolish(self):
        """Force dynamic-property QSS refresh in Maya's Qt4/Qt5 hosts."""
        try:
            self.style().unpolish(self)
            self.style().polish(self)
            self.header.style().unpolish(self.header)
            self.header.style().polish(self.header)
        except Exception:
            pass


def install_runtime_folder_composition(runtime_module):
    """Make legacy RuntimeFolder compose CollapsibleSection.

    ``RuntimeFolder`` remains the runtime/domain renderer responsible for
    config data and child construction. Only its ``collapsible`` mode uses the
    shared UI primitive. Simple/tabs/radio behavior stays on the legacy path.

    This installation keeps the existing public RuntimeFolder class identity
    stable for registry/hooks compatibility; it does not create a subclass.
    """
    runtime_class = runtime_module.RuntimeFolder
    if getattr(runtime_class, _RUNTIME_COMPOSITION_MARKER, False):
        return runtime_class

    legacy_init = runtime_class.__init__
    legacy_toggle = runtime_class.toggle
    legacy_update_state = runtime_class.update_state

    def runtime_folder_init(
        self,
        toolbox,
        section,
        parent=None,
        embedded=False
    ):
        folder_type = section.get(
            "folder_type",
            "collapsible"
        )

        # Embedded tab/radio pages and all non-collapsible folder modes keep
        # their specialized legacy presentation.
        if embedded or folder_type != "collapsible":
            legacy_init(
                self,
                toolbox,
                section,
                parent=parent,
                embedded=embedded
            )
            self.collapsible_section = None
            return

        QtGui.QFrame.__init__(self, parent)
        self.setObjectName("RuntimeFolderHost")

        self.toolbox = toolbox
        self.section = section
        self.embedded = False
        self.folder_type = folder_type
        self.is_nested = False

        try:
            self.is_nested = (
                parent is not None and
                parent.objectName() == "RuntimeFolderContent"
            )
        except Exception:
            self.is_nested = False

        # Preserve compatibility properties on the runtime host while the
        # visual QSS properties live on CollapsibleSection itself.
        self.setProperty("folderType", self.folder_type)
        self.setProperty("nested", self.is_nested)

        root = QtGui.QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        label = (
            section.get(
                "label",
                section["name"]
            )
            if section.get("show_label", True)
            else ""
        )
        self.header_label = text_type(label)

        self.collapsible_section = CollapsibleSection(
            title=self.header_label,
            collapsed=bool(
                section.get("collapsed", False)
            ),
            nested=self.is_nested,
            tooltip=section.get("tooltip", ""),
            parent=self
        )
        root.addWidget(self.collapsible_section)

        # Stable compatibility aliases used by older runtime hooks/tests.
        self.header = None
        self.header_button = self.collapsible_section.header
        self.arrow = self.header_button
        self.content = self.collapsible_section.content
        self.content_layout = self.collapsible_section.content_layout

        self.collapsible_section.collapsedChanged.connect(
            self._collapsible_section_changed
        )

        self._populate_runtime_items(
            section["items"]
        )
        self.update_state()

    def collapsible_section_changed(self, collapsed):
        collapsed = bool(collapsed)
        previous = bool(
            self.section.get("collapsed", False)
        )
        if previous == collapsed:
            return

        self.section["collapsed"] = collapsed
        self.toolbox.save()

    def runtime_folder_toggle(self):
        current = getattr(
            self,
            "collapsible_section",
            None
        )
        if current is not None:
            current.toggle()
            return
        return legacy_toggle(self)

    def runtime_folder_update_state(self):
        current = getattr(
            self,
            "collapsible_section",
            None
        )
        if current is not None:
            current.set_collapsed(
                bool(
                    self.section.get(
                        "collapsed",
                        False
                    )
                ),
                notify=False
            )
            return
        return legacy_update_state(self)

    runtime_class.__init__ = runtime_folder_init
    runtime_class._collapsible_section_changed = collapsible_section_changed
    runtime_class.toggle = runtime_folder_toggle
    runtime_class.update_state = runtime_folder_update_state
    setattr(
        runtime_class,
        _RUNTIME_COMPOSITION_MARKER,
        True
    )
    return runtime_class


# Compatibility alias for integrations that imported the transitional name.
def install_runtime_folder_chrome(runtime_module):
    return install_runtime_folder_composition(runtime_module)


__all__ = [
    "COLLAPSIBLE_FOLDER_CONTENT_MARGINS",
    "COLLAPSIBLE_FOLDER_CONTENT_SPACING",
    "COLLAPSIBLE_FOLDER_ICON_SIZE",
    "CollapsibleSection",
    "install_runtime_folder_chrome",
    "install_runtime_folder_composition",
]
