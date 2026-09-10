# -*- coding: utf-8 -*-
from __future__ import print_function

from ...compat import QtCore
from ...compat import QtGui
from ...pycompat import text_type
from ...style.metrics import PROPERTY_EDITOR_SPACING
from ...style.metrics import PROPERTY_GROUP_MARGINS
from ..collapsible_folder import configure_collapsible_folder_content
from ..collapsible_folder import configure_collapsible_folder_frame
from ..collapsible_folder import configure_collapsible_folder_header
from ..collapsible_folder import set_collapsible_folder_state
from ..layout_helpers import configure_layout
from ..layout_helpers import configure_property_form


SECTION_GENERAL = "general"
SECTION_LAYOUT = "layout"
SECTION_CONTAINER_LAYOUT = "container_layout"
SECTION_CONTENT = "content"
SECTION_APPEARANCE = "appearance"
SECTION_INTERFACE_OPTIONS = "interface_options"
SECTION_BEHAVIOR = "behavior"
SECTION_TRIGGERS = "triggers"

INSPECTOR_SECTION_ORDER = (
    SECTION_GENERAL,
    SECTION_LAYOUT,
    SECTION_CONTAINER_LAYOUT,
    SECTION_CONTENT,
    SECTION_APPEARANCE,
    SECTION_INTERFACE_OPTIONS,
    SECTION_BEHAVIOR,
    SECTION_TRIGGERS,
)

INSPECTOR_SECTION_TITLES = {
    SECTION_GENERAL: "GENERAL",
    SECTION_LAYOUT: "LAYOUT",
    SECTION_CONTAINER_LAYOUT: "CONTAINER LAYOUT",
    SECTION_CONTENT: "CONTENT",
    SECTION_APPEARANCE: "APPEARANCE",
    SECTION_INTERFACE_OPTIONS: "INTERFACE OPTIONS",
    SECTION_BEHAVIOR: "BEHAVIOR",
    SECTION_TRIGGERS: "TRIGGERS",
}

_DEFAULT_UNAVAILABLE_REASON = "This property is not available in the current context."
_BASE_TOOLTIP_ATTRIBUTE = "_script_toolbox_inspector_base_tooltip"
_AVAILABLE_ATTRIBUTE = "_script_toolbox_inspector_property_available"


def set_property_available(widget, available, reason=None):
    """Enable or disable one Inspector property without changing its value."""
    if widget is None:
        return

    available = bool(available)
    reason = text_type(reason or _DEFAULT_UNAVAILABLE_REASON)

    if not hasattr(widget, _BASE_TOOLTIP_ATTRIBUTE):
        try:
            setattr(
                widget,
                _BASE_TOOLTIP_ATTRIBUTE,
                text_type(widget.toolTip() or "")
            )
        except Exception:
            setattr(widget, _BASE_TOOLTIP_ATTRIBUTE, "")

    setattr(widget, _AVAILABLE_ATTRIBUTE, available)
    widget.setEnabled(available)

    try:
        if available:
            widget.setToolTip(
                getattr(widget, _BASE_TOOLTIP_ATTRIBUTE, "")
            )
        else:
            widget.setToolTip(reason)
    except Exception:
        pass


def is_property_available(widget):
    if widget is None:
        return False
    # Availability is an Inspector capability, not the widget's effective
    # Qt enabled state. A disabled parent must not make write_to_item() drop a
    # property that is otherwise valid for the selected item.
    return bool(
        getattr(widget, _AVAILABLE_ATTRIBUTE, True)
    )


class InspectorSection(QtGui.QFrame):
    """Reusable collapsible section using the shared Folder chrome."""

    collapsedChanged = QtCore.Signal(bool)

    def __init__(
        self,
        key,
        title,
        collapsed=False,
        visible=False,
        parent=None
    ):
        QtGui.QFrame.__init__(self, parent)

        self.key = text_type(key)
        self.title = text_type(title)
        self._collapsed = False
        self._has_static_content = False
        self._row_labels = {}

        configure_collapsible_folder_frame(
            self,
            nested=False
        )

        root = QtGui.QVBoxLayout(self)
        configure_layout(
            root,
            margins=(0, 0, 0, 0),
            spacing=0
        )

        self.header = QtGui.QPushButton(self)
        configure_collapsible_folder_header(
            self.header,
            self.title
        )
        root.addWidget(self.header)

        self.content = QtGui.QWidget(self)
        self.content_layout = QtGui.QVBoxLayout(self.content)
        configure_collapsible_folder_content(
            self.content,
            self.content_layout,
            margins=PROPERTY_GROUP_MARGINS,
            spacing=PROPERTY_EDITOR_SPACING
        )

        self.form = QtGui.QFormLayout()
        configure_property_form(self.form)
        self.content_layout.addLayout(self.form)
        root.addWidget(self.content)

        self.header.clicked.connect(self._header_clicked)
        self.set_collapsed(collapsed, notify=False)
        self.setVisible(bool(visible))

    @property
    def collapsed(self):
        return self._collapsed

    @property
    def has_static_content(self):
        return self._has_static_content

    def _header_clicked(self, checked=False):
        self.set_collapsed(
            not self._collapsed,
            notify=True
        )

    def set_collapsed(
        self,
        collapsed,
        notify=False,
        sync_header=True
    ):
        collapsed = bool(collapsed)
        changed = collapsed != self._collapsed
        self._collapsed = collapsed

        set_collapsible_folder_state(
            self,
            self.header,
            self.content,
            self.title,
            collapsed
        )

        try:
            policy = self.sizePolicy()
            policy.setVerticalPolicy(
                QtGui.QSizePolicy.Maximum
                if collapsed
                else QtGui.QSizePolicy.Preferred
            )
            self.setSizePolicy(policy)
        except Exception:
            pass

        if changed and notify:
            self.collapsedChanged.emit(collapsed)

    def addRow(self, label, widget):
        self.form.addRow(label, widget)
        self._has_static_content = True
        self.setVisible(True)

        try:
            label_widget = self.form.labelForField(widget)
        except Exception:
            label_widget = None

        if label_widget is not None:
            self._row_labels[id(widget)] = label_widget
        return widget

    def addWidget(self, widget, stretch=0, mark_used=True):
        self.content_layout.addWidget(widget, stretch)
        if mark_used:
            self._has_static_content = True
            self.setVisible(True)
        return widget

    def labelForField(self, widget):
        label = self._row_labels.get(id(widget))
        if label is not None:
            return label
        try:
            return self.form.labelForField(widget)
        except Exception:
            return None

    def set_row_visible(self, widget, visible):
        if widget is None:
            return
        visible = bool(visible)
        widget.setVisible(visible)
        label = self.labelForField(widget)
        if label is not None:
            label.setVisible(visible)

    def set_property_available(self, widget, available, reason=None):
        set_property_available(widget, available, reason)
        label = self.labelForField(widget)
        if label is not None:
            set_property_available(label, available, reason)


__all__ = [
    "INSPECTOR_SECTION_ORDER",
    "INSPECTOR_SECTION_TITLES",
    "InspectorSection",
    "SECTION_APPEARANCE",
    "SECTION_BEHAVIOR",
    "SECTION_CONTAINER_LAYOUT",
    "SECTION_CONTENT",
    "SECTION_GENERAL",
    "SECTION_INTERFACE_OPTIONS",
    "SECTION_LAYOUT",
    "SECTION_TRIGGERS",
    "is_property_available",
    "set_property_available",
]
