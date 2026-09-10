# -*- coding: utf-8 -*-
from __future__ import print_function

from ...compat import QtCore
from ...compat import QtGui
from ...core.preferences import INSPECTOR_SECTIONS_KEY
from ...core.preferences import load_preferences
from ...core.preferences import set_inspector_section_collapsed
from ...model.items import sanitize_name
from ...pycompat import text_type
from ...style.metrics import PROPERTY_EDITOR_SPACING
from ...style.palette import WINDOW_BG
from .bindings import BindingPanel
from .layout_adapter import LayoutPropertyAdapter
from .sections import INSPECTOR_SECTION_ORDER
from .sections import INSPECTOR_SECTION_TITLES
from .sections import InspectorSection
from .sections import SECTION_APPEARANCE
from .sections import SECTION_BEHAVIOR
from .sections import SECTION_CONTAINER_LAYOUT
from .sections import SECTION_CONTENT
from .sections import SECTION_GENERAL
from .sections import SECTION_INTERFACE_OPTIONS
from .sections import SECTION_LAYOUT
from .sections import SECTION_TRIGGERS
from .sections import is_property_available
from .sections import set_property_available as _set_property_available


class PropertyEditorBase(QtGui.QWidget):

    changed = QtCore.Signal()

    def __init__(self, toolbox=None, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.setObjectName("PropertyEditor")
        try:
            editor_palette = self.palette()
            editor_palette.setColor(
                QtGui.QPalette.Window,
                QtGui.QColor(WINDOW_BG)
            )
            editor_palette.setColor(
                QtGui.QPalette.Base,
                QtGui.QColor(WINDOW_BG)
            )
            self.setPalette(editor_palette)
            self.setAutoFillBackground(True)
        except Exception:
            pass

        self.toolbox = toolbox
        self.item = None
        self.loading = False
        self.parent_layout_kind = ""
        self.parent_layout_item = {}
        self.row_context = False
        self.row_equal_widths = False
        self.column_context = False
        self._trigger_extra_widgets = []

        self.root_layout = QtGui.QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(PROPERTY_EDITOR_SPACING)

        self.sections = {}
        self.section_order = INSPECTOR_SECTION_ORDER
        self._build_sections()

        # GENERAL ---------------------------------------------------------
        self.name_edit = QtGui.QLineEdit()
        self.label_edit = QtGui.QLineEdit()
        self.show_label_check = QtGui.QCheckBox()
        self.tooltip_edit = QtGui.QLineEdit()

        self.general_section.addRow("Name", self.name_edit)
        self.general_section.addRow("Label", self.label_edit)
        self.general_section.addRow("Show Label", self.show_label_check)
        self.general_section.addRow("Tooltip", self.tooltip_edit)

        # LAYOUT ----------------------------------------------------------
        # These controls present one stable Inspector contract while the
        # adapter below keeps the existing row_*/column_* persisted keys.
        self.row_width_mode = QtGui.QComboBox()
        self.row_width_mode.addItems([
            "Auto",
            "Stretch",
            "Fixed",
        ])
        self.row_width = QtGui.QSpinBox()
        self.row_width.setRange(20, 2000)
        self.row_stretch = QtGui.QSpinBox()
        self.row_stretch.setRange(1, 100)

        self.column_height_mode = QtGui.QComboBox()
        self.column_height_mode.addItems([
            "Auto",
            "Stretch",
            "Fixed",
        ])
        self.column_height = QtGui.QSpinBox()
        self.column_height.setRange(8, 2000)
        self.column_stretch = QtGui.QSpinBox()
        self.column_stretch.setRange(1, 100)

        self.layout_horizontal_alignment = QtGui.QComboBox()
        self.layout_horizontal_alignment.addItems([
            "Stretch",
            "Start",
            "Center",
            "End",
        ])
        self.layout_vertical_alignment = QtGui.QComboBox()
        self.layout_vertical_alignment.addItems([
            "Stretch",
            "Start",
            "Center",
            "End",
        ])

        self.layout_section.addRow("Width Mode", self.row_width_mode)
        self.layout_section.addRow("Fixed Width", self.row_width)
        self.layout_section.addRow("Width Stretch", self.row_stretch)
        self.layout_section.addRow("Height Mode", self.column_height_mode)
        self.layout_section.addRow("Fixed Height", self.column_height)
        self.layout_section.addRow("Height Stretch", self.column_stretch)
        self.layout_section.addRow(
            "Horizontal Alignment",
            self.layout_horizontal_alignment
        )
        self.layout_section.addRow(
            "Vertical Alignment",
            self.layout_vertical_alignment
        )

        self.layout_adapter = LayoutPropertyAdapter(self)

        # TRIGGERS --------------------------------------------------------
        # BindingPanel remains the existing event-binding implementation; it
        # is embedded instead of replaced so persisted bindings are untouched.
        self.binding_panel = BindingPanel(
            toolbox=self.toolbox,
            parent=self.trigger_section
        )
        try:
            self.binding_panel.setTitle("Events")
        except Exception:
            pass
        self.trigger_section.addWidget(
            self.binding_panel,
            1,
            mark_used=False
        )

        self.name_edit.textEdited.connect(self._control_changed)
        self.label_edit.textEdited.connect(self._control_changed)
        self.show_label_check.toggled.connect(self._control_changed)
        self.tooltip_edit.textEdited.connect(self._control_changed)
        self.row_width_mode.currentIndexChanged.connect(
            self._row_layout_changed
        )
        self.row_width.valueChanged.connect(self._control_changed)
        self.row_stretch.valueChanged.connect(self._control_changed)
        self.column_height_mode.currentIndexChanged.connect(
            self._column_layout_changed
        )
        self.column_height.valueChanged.connect(self._control_changed)
        self.column_stretch.valueChanged.connect(
            self._control_changed
        )
        self.binding_panel.changed.connect(
            self._control_changed
        )

        self.layout_adapter.refresh()
        self._refresh_trigger_section_visibility()

    def _build_sections(self):
        always_visible = set((
            SECTION_GENERAL,
            SECTION_LAYOUT,
        ))

        preferences = load_preferences()
        collapsed_sections = preferences.get(
            INSPECTOR_SECTIONS_KEY,
            {}
        )
        if not isinstance(collapsed_sections, dict):
            collapsed_sections = {}

        for key in INSPECTOR_SECTION_ORDER:
            section = InspectorSection(
                key,
                INSPECTOR_SECTION_TITLES[key],
                collapsed=bool(collapsed_sections.get(key, False)),
                visible=key in always_visible,
                parent=self
            )
            section.collapsedChanged.connect(
                lambda collapsed, section_key=key:
                self._section_collapsed(section_key, collapsed)
            )
            self.sections[key] = section
            self.root_layout.addWidget(section)

        self.general_section = self.sections[SECTION_GENERAL]
        self.layout_section = self.sections[SECTION_LAYOUT]
        self.container_layout_section = self.sections[
            SECTION_CONTAINER_LAYOUT
        ]
        self.content_section = self.sections[SECTION_CONTENT]
        self.appearance_section = self.sections[SECTION_APPEARANCE]
        self.interface_options_section = self.sections[
            SECTION_INTERFACE_OPTIONS
        ]
        self.behavior_section = self.sections[SECTION_BEHAVIOR]
        self.trigger_section = self.sections[SECTION_TRIGGERS]

    def _section_collapsed(self, key, collapsed):
        set_inspector_section_collapsed(
            key,
            collapsed
        )

    def section(self, key):
        return self.sections[key]

    def set_property_available(
        self,
        widget,
        available,
        reason=None
    ):
        for key in self.section_order:
            section = self.sections[key]
            if section.labelForField(widget) is not None:
                section.set_property_available(
                    widget,
                    available,
                    reason
                )
                return

        # Checkbox rows with an empty label can legitimately have no QLabel.
        # In that case the shared helper still provides the required state and
        # explanatory tooltip on the control itself.
        _set_property_available(
            widget,
            available,
            reason
        )

    def set_section_row_visible(
        self,
        section,
        widget,
        visible
    ):
        section.set_row_visible(widget, visible)

    def add_trigger_widget(self, widget, stretch=0):
        self.trigger_section.addWidget(
            widget,
            stretch,
            mark_used=False
        )
        self._trigger_extra_widgets.append(widget)
        self._refresh_trigger_section_visibility()
        return widget

    def _refresh_trigger_section_visibility(self):
        binding_visible = False
        try:
            binding_visible = not self.binding_panel.isHidden()
        except Exception:
            pass

        extra_visible = any(
            not widget.isHidden()
            for widget in self._trigger_extra_widgets
        )
        self.trigger_section.setVisible(
            binding_visible or extra_visible
        )

    def set_row_context(
        self,
        enabled,
        equal_widths=False
    ):
        if enabled:
            parent_item = dict(self.parent_layout_item or {})
            parent_item["equal_widths"] = bool(equal_widths)
            self.set_parent_layout_context(
                "row",
                parent_item
            )
        elif self.parent_layout_kind == "row":
            self.set_parent_layout_context("", None)

    def set_column_context(self, enabled):
        if enabled:
            self.set_parent_layout_context(
                "column",
                self.parent_layout_item
            )
        elif self.parent_layout_kind == "column":
            self.set_parent_layout_context("", None)

    def set_parent_layout_context(
        self,
        parent_kind,
        parent_item=None
    ):
        self.parent_layout_kind = text_type(
            parent_kind or ""
        ).lower()
        self.parent_layout_item = parent_item or {}
        self.layout_adapter.set_parent_context(
            self.parent_layout_kind,
            self.parent_layout_item
        )

    def _refresh_row_layout_controls(self):
        self.layout_adapter.refresh()

    def _refresh_column_layout_controls(self):
        self.layout_adapter.refresh()

    def _row_layout_changed(self, *args):
        self.layout_adapter.refresh()
        self._control_changed()

    def _column_layout_changed(self, *args):
        self.layout_adapter.refresh()
        self._control_changed()

    def add_stretch(self):
        self.root_layout.addStretch(1)

    def bind(self, item):
        self.item = item
        self.loading = True

        try:
            self.name_edit.setText(
                text_type(item.get("name", ""))
            )
            self.label_edit.setText(
                text_type(
                    item.get(
                        "label",
                        item.get("name", "")
                    )
                )
            )
            self.show_label_check.setChecked(
                bool(item.get("show_label", True))
            )
            self.tooltip_edit.setText(
                text_type(item.get("tooltip", ""))
            )

            self.layout_adapter.load(item)
            self.binding_panel.load(item)
            self.load_specific(item)
        finally:
            self.loading = False
            self.layout_adapter.refresh()
            self._refresh_trigger_section_visibility()

    def refresh_binding_panel(self):
        if self.item is None:
            return
        previous = self.loading
        self.loading = True
        try:
            self.binding_panel.load(self.item)
            self._refresh_trigger_section_visibility()
        finally:
            self.loading = previous

    def load_specific(self, item):
        pass

    def write_specific(self, item):
        pass

    def write_to_item(self):
        if self.item is None:
            return

        kind = self.item.get("kind", "item")
        if is_property_available(self.name_edit):
            self.item["name"] = sanitize_name(
                text_type(self.name_edit.text()),
                kind
            )

        if is_property_available(self.label_edit):
            label = text_type(
                self.label_edit.text()
            ).strip()
            self.item["label"] = (
                label or self.item.get("name", kind)
            )

        if is_property_available(self.show_label_check):
            self.item["show_label"] = bool(
                self.show_label_check.isChecked()
            )

        if is_property_available(self.tooltip_edit):
            self.item["tooltip"] = text_type(
                self.tooltip_edit.text()
            )

        self.layout_adapter.write(self.item)
        self.write_specific(self.item)
        self.binding_panel.write_to_item(self.item)

    def _control_changed(self, *args):
        if self.loading:
            return

        self.write_to_item()
        self.changed.emit()


class ValuePropertyEditorBase(PropertyEditorBase):

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


class EmptyPropertyEditor(QtGui.QWidget):

    def __init__(
        self,
        toolbox=None,
        parent=None
    ):
        QtGui.QWidget.__init__(
            self,
            parent
        )
        self.setObjectName("PropertyEditor")
        try:
            editor_palette = self.palette()
            editor_palette.setColor(
                QtGui.QPalette.Window,
                QtGui.QColor(WINDOW_BG)
            )
            editor_palette.setColor(
                QtGui.QPalette.Base,
                QtGui.QColor(WINDOW_BG)
            )
            self.setPalette(editor_palette)
            self.setAutoFillBackground(True)
        except Exception:
            pass

        layout = QtGui.QVBoxLayout(self)
        layout.addStretch(1)

        label = QtGui.QLabel(
            "Select a parameter to edit its properties."
        )
        label.setObjectName("HintText")
        label.setAlignment(QtCore.Qt.AlignCenter)

        layout.addWidget(label)
        layout.addStretch(1)

    def bind(self, item):
        pass


__all__ = [
    "EmptyPropertyEditor",
    "PropertyEditorBase",
    "ValuePropertyEditorBase",
]
