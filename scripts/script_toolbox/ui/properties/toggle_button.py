# -*- coding: utf-8 -*-
from __future__ import print_function

from ...compat import QtGui
from ...model.bindings import normalize_bindings
from ...model.items import safe_color
from ...pycompat import text_type
from ..language_script_editor import LanguageScriptEditor
from .base import PropertyEditorBase
from .button import ButtonPropertyEditor
from .inspector_tabs import add_inspector_script_tab


class ToggleButtonPropertyEditor(ButtonPropertyEditor):
    """Property editor for the dedicated stateful Toggle Button item."""

    def __init__(self, toolbox=None, parent=None):
        ButtonPropertyEditor.__init__(
            self,
            toolbox=toolbox,
            parent=parent
        )

        self.appearance_section.set_row_visible(
            self.color_button,
            False
        )

        self.state_source = QtGui.QComboBox()
        self.state_source.addItems([
            "Internal",
            "Script",
        ])
        self.internal_state = QtGui.QCheckBox()
        self.behavior_section.addRow(
            "State Source",
            self.state_source
        )
        self.behavior_section.addRow(
            "Internal State",
            self.internal_state
        )

        self.state_on_label = QtGui.QLineEdit()
        self.state_off_label = QtGui.QLineEdit()
        self.state_on_color = [0.22, 0.42, 0.26]
        self.state_off_color = [0.30, 0.30, 0.30]
        self.state_on_color_button = QtGui.QPushButton("Choose...")
        self.state_off_color_button = QtGui.QPushButton("Choose...")

        section = self.appearance_section
        section.addRow("ON Label", self.state_on_label)
        section.addRow("OFF Label", self.state_off_label)
        section.addRow("ON Color", self.state_on_color_button)
        section.addRow("OFF Color", self.state_off_color_button)

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
        # bindings. Keeping one tab widget removes overlapping panes and makes
        # Click/Ctrl+Click/Get State/Turn ON/Turn OFF share identical geometry.
        self.state_get_page = None
        self.state_on_page = None
        self.state_off_page = None

        self.state_source.currentIndexChanged.connect(
            self._state_source_changed
        )
        self.internal_state.toggled.connect(self._control_changed)
        self.state_on_label.textEdited.connect(self._control_changed)
        self.state_off_label.textEdited.connect(self._control_changed)
        self.state_on_color_button.clicked.connect(
            lambda: self.choose_state_color("on")
        )
        self.state_off_color_button.clicked.connect(
            lambda: self.choose_state_color("off")
        )
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
        ButtonPropertyEditor.bind(self, item)

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

        # Event pages must stay first because BindingPanel maps their list
        # positions directly to tab indices. Re-appending the fixed pages after
        # every binding mutation preserves that invariant.
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

        # Fixed state pages are real tab content, so the panel must not use the
        # compact "no triggers" height even if an old item has no bindings yet.
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

    def _refresh_state_colors(self):
        self.state_on_color_button.setStyleSheet(
            self._button_color_style(self.state_on_color)
        )
        self.state_off_color_button.setStyleSheet(
            self._button_color_style(self.state_off_color)
        )

    def choose_state_color(self, which):
        current = (
            self.state_on_color
            if which == "on"
            else self.state_off_color
        )
        title = (
            "Choose ON Color"
            if which == "on"
            else "Choose OFF Color"
        )
        initial = QtGui.QColor(
            int(current[0] * 255),
            int(current[1] * 255),
            int(current[2] * 255)
        )
        chosen = QtGui.QColorDialog.getColor(initial, self, title)
        if not chosen.isValid():
            return

        value = [
            chosen.red() / 255.0,
            chosen.green() / 255.0,
            chosen.blue() / 255.0
        ]
        if which == "on":
            self.state_on_color = value
        else:
            self.state_off_color = value
        self._refresh_state_colors()
        self._control_changed()

    def load_specific(self, item):
        ButtonPropertyEditor.load_specific(self, item)
        self.state_source.setCurrentIndex(
            1
            if item.get("state_source", "internal") == "script"
            else 0
        )
        self.internal_state.setChecked(bool(item.get("value", False)))
        self.state_on_label.setText(
            text_type(item.get("state_on_label", item.get("label", "Toggle")))
        )
        self.state_off_label.setText(
            text_type(item.get("state_off_label", item.get("label", "Toggle")))
        )
        self.state_on_color = safe_color(item.get("state_on_color"))
        self.state_off_color = safe_color(item.get("state_off_color"))

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

        self._refresh_state_colors()
        self._sync_state_tabs()

    def write_specific(self, item):
        ButtonPropertyEditor.write_specific(self, item)
        item.pop("color", None)

        item["state_source"] = self.current_state_source()
        if item["state_source"] == "internal":
            item["value"] = bool(self.internal_state.isChecked())
        else:
            item.pop("value", None)

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
        item["state_on_label"] = text_type(
            self.state_on_label.text()
        ).strip() or item.get("label", "Toggle")
        item["state_off_label"] = text_type(
            self.state_off_label.text()
        ).strip() or item.get("label", "Toggle")
        item["state_on_color"] = safe_color(self.state_on_color)
        item["state_off_color"] = safe_color(self.state_off_color)

    def write_to_item(self):
        PropertyEditorBase.write_to_item(self)
        if self.item is not None:
            self.item["bindings"] = normalize_bindings(
                "toggle_button",
                self.item
            )


__all__ = [
    "ToggleButtonPropertyEditor",
]
