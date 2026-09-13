# -*- coding: utf-8 -*-
from __future__ import print_function

from ...compat import QtGui
from ...model.bindings import normalize_bindings
from ...model.items import clamp
from ...pycompat import text_type
from ..icon_browse import install_icon_browse
from ..language_script_editor import LanguageScriptEditor
from .base import PropertyEditorBase
from .inspector_tabs import add_inspector_script_tab


class ToggleIconPropertyEditor(PropertyEditorBase):
    """Property editor for a stateful icon with independent ON/OFF images."""

    def __init__(
        self,
        toolbox=None,
        parent=None
    ):
        PropertyEditorBase.__init__(self, toolbox, parent)

        self.state_source = QtGui.QComboBox()
        self.state_source.addItems([
            "Internal",
            "Script",
        ])
        self.internal_state = QtGui.QCheckBox()
        self.state_on_path = QtGui.QLineEdit()
        self.state_off_path = QtGui.QLineEdit()
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

        self.behavior_section.addRow("State Source", self.state_source)
        self.behavior_section.addRow("Internal State", self.internal_state)

        section = self.appearance_section
        section.addRow("ON Icon", self.state_on_path)
        section.addRow("OFF Icon", self.state_off_path)
        section.addRow("Icon Width", self.width)
        section.addRow("Icon Height", self.height)
        section.addRow("Content Alignment", self.alignment)

        self.state_on_browse_button = install_icon_browse(
            self,
            self.state_on_path,
            form=section.form
        )
        self.state_off_browse_button = install_icon_browse(
            self,
            self.state_off_path,
            form=section.form
        )

        self.state_get_editor = LanguageScriptEditor(
            language="python",
            toolbox=self.toolbox
        )
        self.state_get_editor.set_language_enabled(
            False,
            "State queries use Python so the state variable can be evaluated."
        )
        self.state_on_editor = LanguageScriptEditor(
            language="python",
            toolbox=self.toolbox
        )
        self.state_off_editor = LanguageScriptEditor(
            language="python",
            toolbox=self.toolbox
        )

        # State scripts are fixed pages of the same QTabWidget that owns event
        # bindings. This prevents a second tab pane from overlapping Get State
        # and guarantees identical page geometry for every trigger tab.
        self.state_get_page = None
        self.state_on_page = None
        self.state_off_page = None

        self.state_source.currentIndexChanged.connect(
            self._state_source_changed
        )
        self.internal_state.toggled.connect(self._control_changed)
        self.state_on_path.textEdited.connect(self._control_changed)
        self.state_off_path.textEdited.connect(self._control_changed)
        self.width.valueChanged.connect(self._control_changed)
        self.height.valueChanged.connect(self._control_changed)
        self.alignment.currentIndexChanged.connect(self._control_changed)
        self.binding_panel.changed.connect(self._sync_state_tabs)

        for editor in (
            self.state_get_editor,
            self.state_on_editor,
            self.state_off_editor,
        ):
            editor.textChanged.connect(self._control_changed)
            editor.languageChanged.connect(self._control_changed)

        self._refresh_state_source()

    def bind(self, item):
        # BindingPanel.load() rebuilds event-binding pages. Detach the fixed
        # state pages first so its clear() only destroys binding-owned pages.
        self._detach_state_tabs()
        PropertyEditorBase.bind(self, item)

    def _state_tab_specs(self):
        return (
            ("state_get_page", self.state_get_editor, "Get State"),
            ("state_on_page", self.state_on_editor, "Turn ON"),
            ("state_off_page", self.state_off_editor, "Turn OFF"),
        )

    def _detach_state_tabs(self):
        tabs = self.binding_panel.tabs
        for attr, editor, label in self._state_tab_specs():
            page = getattr(self, attr)
            if page is None:
                continue
            index = tabs.indexOf(page)
            if index >= 0:
                tabs.removeTab(index)
            try:
                page.setParent(self)
            except Exception:
                pass

    def _hide_state_tab_close_button(self, index):
        if index < 0:
            return
        try:
            tab_bar = self.binding_panel.tabs.tabBar()
            for side_name in ("LeftSide", "RightSide"):
                side = getattr(QtGui.QTabBar, side_name, None)
                if side is not None:
                    tab_bar.setTabButton(index, side, None)
        except Exception:
            pass

    def _sync_state_tabs(self):
        tabs = self.binding_panel.tabs

        # BindingPanel assumes all event-binding pages occupy the leading tab
        # indices. Keep fixed state pages after them after every add/edit/remove.
        self._detach_state_tabs()
        for attr, editor, label in self._state_tab_specs():
            page = getattr(self, attr)
            if page is None:
                page = add_inspector_script_tab(
                    tabs,
                    editor,
                    label
                )
                setattr(self, attr, page)
            else:
                tabs.addTab(page, label)

            page.setEnabled(True)
            index = tabs.indexOf(page)
            if index >= 0:
                tabs.setTabEnabled(index, True)
                try:
                    tabs.tabBar().setTabEnabled(index, True)
                except Exception:
                    pass
                self._hide_state_tab_close_button(index)

        tabs.setMinimumHeight(0)
        tabs.setMaximumHeight(16777215)
        self.binding_panel.empty_label.setVisible(False)
        self._refresh_state_source()

    def current_state_source(self):
        return (
            "script"
            if self.state_source.currentIndex() == 1
            else "internal"
        )

    def _state_source_changed(self, *args):
        self._refresh_state_source()
        self._control_changed()

    def _refresh_state_source(self):
        scripted = self.current_state_source() == "script"
        self.set_property_available(
            self.internal_state,
            not scripted,
            "Internal State is controlled by Get State when State Source is Script."
        )
        self.state_get_editor.setEnabled(True)

        page = self.state_get_page
        if page is None:
            return

        page.setEnabled(True)
        tabs = self.binding_panel.tabs
        index = tabs.indexOf(page)
        if index < 0:
            return

        tabs.setTabEnabled(index, True)
        try:
            tabs.tabBar().setTabEnabled(index, True)
        except Exception:
            pass
        tabs.setTabToolTip(
            index,
            "State query available for editing; runtime uses it when State Source is Script."
            if not scripted else
            "State query used to evaluate the current toggle state."
        )

    def load_specific(self, item):
        self.state_source.setCurrentIndex(
            1
            if item.get("state_source", "internal") == "script"
            else 0
        )
        self.internal_state.setChecked(bool(item.get("value", False)))
        self.state_on_path.setText(
            text_type(item.get("state_on_path", ""))
        )
        self.state_off_path.setText(
            text_type(item.get("state_off_path", ""))
        )
        self.width.setValue(int(item.get("width", 24)))
        self.height.setValue(int(item.get("height", 24)))
        self.alignment.setCurrentIndex({
            "left": 0,
            "center": 1,
            "right": 2,
        }.get(
            item.get("content_alignment", "left"),
            0
        ))

        self.state_get_editor.set_language("python")
        self.state_get_editor.setPlainText(
            text_type(item.get("state_get_script", ""))
        )
        self.state_on_editor.set_language(
            item.get("state_on_language", "python")
        )
        self.state_on_editor.setPlainText(
            text_type(item.get("state_on_script", ""))
        )
        self.state_off_editor.set_language(
            item.get("state_off_language", "python")
        )
        self.state_off_editor.setPlainText(
            text_type(item.get("state_off_script", ""))
        )
        self._sync_state_tabs()

    def write_specific(self, item):
        item["state_source"] = self.current_state_source()
        if item["state_source"] == "internal":
            item["value"] = bool(self.internal_state.isChecked())
        else:
            item.pop("value", None)

        item["state_on_path"] = text_type(self.state_on_path.text())
        item["state_off_path"] = text_type(self.state_off_path.text())
        item["width"] = clamp(int(self.width.value()), 8, 512)
        item["height"] = clamp(int(self.height.value()), 8, 512)
        item["content_alignment"] = (
            "right"
            if self.alignment.currentIndex() == 2
            else "center"
            if self.alignment.currentIndex() == 1
            else "left"
        )

        item["state_get_script"] = text_type(
            self.state_get_editor.toPlainText()
        )
        item["state_get_language"] = "python"
        item["state_on_script"] = text_type(
            self.state_on_editor.toPlainText()
        )
        item["state_on_language"] = self.state_on_editor.language()
        item["state_off_script"] = text_type(
            self.state_off_editor.toPlainText()
        )
        item["state_off_language"] = self.state_off_editor.language()

    def write_to_item(self):
        PropertyEditorBase.write_to_item(self)
        if self.item is not None:
            self.item["bindings"] = normalize_bindings(
                "toggle_icon",
                self.item
            )


__all__ = [
    "ToggleIconPropertyEditor",
]
