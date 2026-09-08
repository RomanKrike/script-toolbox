# -*- coding: utf-8 -*-
from __future__ import print_function

import copy

from ...compat import QtCore
from ...compat import QtGui
from ...model.bindings import EVENT_LABELS
from ...model.bindings import MOUSE_BUTTONS
from ...model.bindings import binding_display_name
from ...model.bindings import binding_events
from ...model.bindings import binding_signature
from ...model.bindings import bindings_for_editor
from ...model.bindings import is_mouse_event
from ...model.bindings import make_binding
from ...model.bindings import normalize_binding
from ...model.bindings import supports_bindings
from ...pycompat import text_type
from ..language_script_editor import LanguageScriptEditor


class AddBindingDialog(QtGui.QDialog):

    def __init__(
        self,
        item,
        binding=None,
        parent=None
    ):
        QtGui.QDialog.__init__(self, parent)

        self.item = item
        self.original = copy.deepcopy(binding) if binding else None
        self.setWindowTitle(
            "Edit Trigger" if binding else "Add Trigger"
        )
        self.setMinimumWidth(350)

        root = QtGui.QVBoxLayout(self)
        form = QtGui.QFormLayout()
        root.addLayout(form)

        self.event_combo = QtGui.QComboBox()
        self.events = list(
            binding_events(item.get("kind"))
        )
        for event in self.events:
            self.event_combo.addItem(
                EVENT_LABELS.get(
                    event,
                    event.replace("_", " ").title()
                )
            )
        form.addRow("Event", self.event_combo)

        self.mouse_button = QtGui.QComboBox()
        self.mouse_button.addItems([
            "Left",
            "Middle",
            "Right",
        ])
        self.mouse_button_label = QtGui.QLabel("Mouse Button")
        form.addRow(
            self.mouse_button_label,
            self.mouse_button
        )

        self.modifier_widget = QtGui.QWidget()
        modifier_layout = QtGui.QHBoxLayout(
            self.modifier_widget
        )
        modifier_layout.setContentsMargins(0, 0, 0, 0)
        modifier_layout.setSpacing(8)
        self.ctrl = QtGui.QCheckBox("Ctrl")
        self.alt = QtGui.QCheckBox("Alt")
        self.shift = QtGui.QCheckBox("Shift")
        modifier_layout.addWidget(self.ctrl)
        modifier_layout.addWidget(self.alt)
        modifier_layout.addWidget(self.shift)
        modifier_layout.addStretch(1)
        self.modifier_label = QtGui.QLabel("Modifiers")
        form.addRow(
            self.modifier_label,
            self.modifier_widget
        )

        self.label_edit = QtGui.QLineEdit()
        try:
            self.label_edit.setPlaceholderText(
                "Optional tab name"
            )
        except Exception:
            pass
        form.addRow("Tab Name", self.label_edit)

        hint = QtGui.QLabel(
            "Ctrl / Alt / Shift are available only for mouse events."
        )
        hint.setObjectName("HintText")
        hint.setWordWrap(True)
        root.addWidget(hint)

        buttons = QtGui.QHBoxLayout()
        buttons.addStretch(1)
        cancel_button = QtGui.QPushButton("Cancel")
        add_button = QtGui.QPushButton(
            "Save" if binding else "Add"
        )
        add_button.setDefault(True)
        buttons.addWidget(cancel_button)
        buttons.addWidget(add_button)
        root.addLayout(buttons)

        cancel_button.clicked.connect(self.reject)
        add_button.clicked.connect(self.accept)
        self.event_combo.currentIndexChanged.connect(
            self._refresh_event_controls
        )

        if binding is not None:
            event = text_type(binding.get("event", ""))
            if event in self.events:
                self.event_combo.setCurrentIndex(
                    self.events.index(event)
                )

            button = text_type(
                binding.get("mouse_button", "left")
            )
            if button in MOUSE_BUTTONS:
                self.mouse_button.setCurrentIndex(
                    MOUSE_BUTTONS.index(button)
                )

            modifiers = set(
                binding.get("modifiers", []) or []
            )
            self.ctrl.setChecked("ctrl" in modifiers)
            self.alt.setChecked("alt" in modifiers)
            self.shift.setChecked("shift" in modifiers)
            self.label_edit.setText(
                text_type(binding.get("label", ""))
            )

        self._refresh_event_controls()

    def current_event(self):
        index = self.event_combo.currentIndex()
        if index < 0 or index >= len(self.events):
            return ""
        return self.events[index]

    def _refresh_event_controls(self, *args):
        mouse = is_mouse_event(
            self.current_event()
        )
        self.mouse_button_label.setVisible(mouse)
        self.mouse_button.setVisible(mouse)
        self.modifier_label.setVisible(mouse)
        self.modifier_widget.setVisible(mouse)

    def value(self):
        original = self.original or {}
        modifiers = []
        if self.ctrl.isChecked():
            modifiers.append("ctrl")
        if self.alt.isChecked():
            modifiers.append("alt")
        if self.shift.isChecked():
            modifiers.append("shift")

        kind = text_type(
            self.item.get("kind", "")
        )
        mode = text_type(
            self.item.get("mode", "action")
        )

        handler = original.get("handler", "script")
        button_mode = original.get("button_mode", "all")

        if kind == "button" and not self.original:
            if mode == "state":
                handler = "state_toggle"
                button_mode = "state"
            else:
                handler = "script"
                button_mode = "action"

        return make_binding(
            self.current_event(),
            language=original.get("language", "python"),
            script=original.get("script", ""),
            mouse_button=MOUSE_BUTTONS[
                max(0, self.mouse_button.currentIndex())
            ],
            modifiers=modifiers,
            label=text_type(self.label_edit.text()).strip(),
            binding_id=original.get("id"),
            handler=handler,
            button_mode=button_mode,
            modifier_policy="exact"
        )


class BindingPage(QtGui.QWidget):

    changed = QtCore.Signal()

    def __init__(
        self,
        binding,
        toolbox=None,
        parent=None
    ):
        QtGui.QWidget.__init__(self, parent)
        self.binding = copy.deepcopy(binding)

        root = QtGui.QVBoxLayout(self)
        root.setContentsMargins(2, 3, 2, 2)
        root.setSpacing(4)

        self.script_editor = None
        if self.binding.get("handler", "script") == "state_toggle":
            note = QtGui.QLabel(
                "This trigger toggles the State Button. Configure the state "
                "query and ON/OFF scripts in the State section below."
            )
            note.setObjectName("HintText")
            note.setWordWrap(True)
            root.addWidget(note)
            root.addStretch(1)
        else:
            self.script_editor = LanguageScriptEditor(
                language=self.binding.get("language", "python"),
                toolbox=toolbox,
                parent=self
            )
            self.script_editor.setPlainText(
                self.binding.get("script", "")
            )
            try:
                self.script_editor.run_button.setEnabled(False)
                self.script_editor.run_button.setToolTip(
                    "Run this script through its event trigger to receive "
                    "toolbox/item/value/old_value/event context."
                )
            except Exception:
                pass
            self.script_editor.textChanged.connect(
                self._script_changed
            )
            self.script_editor.languageChanged.connect(
                self._script_changed
            )
            root.addWidget(
                self.script_editor,
                1
            )

    def _script_changed(self):
        self.write()
        self.changed.emit()

    def write(self):
        if self.script_editor is not None:
            self.binding["language"] = self.script_editor.language()
            self.binding["script"] = text_type(
                self.script_editor.toPlainText()
            )
        return self.binding

    def replace_trigger(self, binding):
        current = self.write()
        replacement = copy.deepcopy(binding)
        replacement["language"] = current.get("language", "python")
        replacement["script"] = current.get("script", "")
        replacement["handler"] = current.get("handler", "script")
        replacement["button_mode"] = current.get("button_mode", "all")
        self.binding = replacement
        self.changed.emit()


class BindingPanel(QtGui.QGroupBox):

    changed = QtCore.Signal()

    def __init__(
        self,
        toolbox=None,
        parent=None
    ):
        QtGui.QGroupBox.__init__(
            self,
            "Triggers",
            parent
        )

        self.toolbox = toolbox
        self.item = None
        self.pages = []
        self.hidden_bindings = []
        self.loading = False

        root = QtGui.QVBoxLayout(self)
        root.setContentsMargins(5, 5, 5, 5)
        root.setSpacing(3)

        self.tabs = QtGui.QTabWidget()
        self.tabs.setTabsClosable(True)

        self.add_button = QtGui.QToolButton(self.tabs)
        self.add_button.setText("+")
        self.add_button.setAutoRaise(True)
        self.add_button.setFixedSize(24, 22)
        self.add_button.setToolTip("Add trigger")
        self.tabs.setCornerWidget(
            self.add_button,
            QtCore.Qt.TopRightCorner
        )

        self.empty_label = QtGui.QLabel(
            "No triggers. Use + to add one."
        )
        self.empty_label.setObjectName("HintText")
        self.empty_label.setAlignment(QtCore.Qt.AlignCenter)

        root.addWidget(self.tabs, 1)
        root.addWidget(self.empty_label)

        self.add_button.clicked.connect(
            self.add_binding
        )
        self.tabs.tabCloseRequested.connect(
            self._close_tab_requested
        )
        self.tabs.tabBar().installEventFilter(self)
        self.setVisible(False)

    def eventFilter(self, watched, event):
        if (
            watched is self.tabs.tabBar() and
            event.type() == QtCore.QEvent.MouseButtonDblClick
        ):
            index = watched.tabAt(event.pos())
            if 0 <= index < len(self.pages):
                self.edit_binding(
                    self.pages[index]
                )
                return True

        return QtGui.QGroupBox.eventFilter(
            self,
            watched,
            event
        )

    def clear(self):
        while self.tabs.count():
            widget = self.tabs.widget(0)
            self.tabs.removeTab(0)
            if widget is not None:
                widget.deleteLater()
        self.pages = []

    def load(self, item):
        self.loading = True
        try:
            self.item = item
            self.clear()
            kind = item.get("kind")
            enabled = supports_bindings(kind)
            self.setVisible(enabled)

            if not enabled:
                self.hidden_bindings = copy.deepcopy(
                    item.get("bindings", []) or []
                )
                return

            visible_ids = set(
                binding.get("id")
                for binding in bindings_for_editor(item)
            )
            self.hidden_bindings = [
                copy.deepcopy(binding)
                for binding in item.get("bindings", []) or []
                if binding.get("id") not in visible_ids
            ]

            for binding in bindings_for_editor(item):
                self._add_page(binding)

            self._refresh_tabs()
        finally:
            self.loading = False

    def _add_page(self, binding):
        page = BindingPage(
            binding,
            toolbox=self.toolbox,
            parent=self.tabs
        )
        page.changed.connect(self._page_changed)
        self.pages.append(page)
        index = self.tabs.addTab(
            page,
            binding_display_name(binding)
        )
        self._update_tab_tooltip(
            index,
            binding
        )
        return page

    def _update_tab_tooltip(self, index, binding):
        if index < 0:
            return
        self.tabs.setTabToolTip(
            index,
            "{0}\nDouble-click to edit trigger.".format(
                binding_display_name(binding)
            )
        )

    def _refresh_tabs(self):
        for index, page in enumerate(self.pages):
            binding = page.write()
            self.tabs.setTabText(
                index,
                binding_display_name(binding)
            )
            self._update_tab_tooltip(
                index,
                binding
            )
        self._refresh_empty()

    def _refresh_empty(self):
        empty = not bool(self.pages)
        self.tabs.setVisible(True)
        self.empty_label.setVisible(empty)

        if empty:
            self.tabs.setMinimumHeight(28)
            self.tabs.setMaximumHeight(34)
        else:
            self.tabs.setMinimumHeight(0)
            self.tabs.setMaximumHeight(16777215)

    def _page_changed(self):
        if self.loading:
            return
        self._refresh_tabs()
        self.changed.emit()

    def _duplicate_signature(self, candidate, ignore_page=None):
        signature = binding_signature(candidate)
        handler = candidate.get("handler", "script")

        for page in self.pages:
            if page is ignore_page:
                continue
            current = page.write()
            if (
                binding_signature(current) == signature and
                current.get("handler", "script") == handler
            ):
                return True
        return False

    def add_binding(self):
        if self.item is None:
            return

        dialog = AddBindingDialog(
            self.item,
            parent=self
        )
        if dialog.exec_() != QtGui.QDialog.Accepted:
            return

        binding = dialog.value()
        if not binding.get("event"):
            return

        if self._duplicate_signature(binding):
            QtGui.QMessageBox.warning(
                self,
                "Duplicate Trigger",
                "This event trigger already exists for the item."
            )
            return

        page = self._add_page(binding)
        self.tabs.setCurrentWidget(page)
        self._refresh_tabs()
        self.changed.emit()

    def edit_binding(self, page):
        if self.item is None or page not in self.pages:
            return

        current = page.write()
        dialog = AddBindingDialog(
            self.item,
            binding=current,
            parent=self
        )
        if dialog.exec_() != QtGui.QDialog.Accepted:
            return

        binding = dialog.value()
        if self._duplicate_signature(
            binding,
            ignore_page=page
        ):
            QtGui.QMessageBox.warning(
                self,
                "Duplicate Trigger",
                "This event trigger already exists for the item."
            )
            return

        page.replace_trigger(binding)
        self._refresh_tabs()
        self.changed.emit()

    def _required_page(self, page):
        if self.item is None or self.item.get("kind") != "button":
            return False

        current = page.write()
        mode = self.item.get("mode", "action")

        if mode == "state":
            if current.get("handler") != "state_toggle":
                return False
            count = sum(
                1
                for candidate in self.pages
                if candidate.write().get("handler") == "state_toggle"
            )
            return count <= 1

        if current.get("handler", "script") != "script":
            return False
        count = sum(
            1
            for candidate in self.pages
            if candidate.write().get("handler", "script") == "script"
        )
        return count <= 1

    def _close_tab_requested(self, index):
        if index < 0 or index >= len(self.pages):
            return
        self.remove_binding(
            self.pages[index]
        )

    def remove_binding(self, page):
        if page not in self.pages:
            return

        if self._required_page(page):
            QtGui.QMessageBox.information(
                self,
                "Trigger Required",
                "A Button must keep at least one trigger for its current mode."
            )
            return

        name = binding_display_name(
            page.write()
        )
        answer = QtGui.QMessageBox.question(
            self,
            "Remove Trigger",
            'Remove trigger "{0}"?'.format(name),
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
            QtGui.QMessageBox.No
        )
        if answer != QtGui.QMessageBox.Yes:
            return

        index = self.pages.index(page)
        self.pages.remove(page)
        self.tabs.removeTab(index)
        page.deleteLater()
        self._refresh_tabs()
        self.changed.emit()

    def write_to_item(self, item):
        if item is None:
            return

        visible = [
            copy.deepcopy(page.write())
            for page in self.pages
        ]
        combined = list(self.hidden_bindings) + visible
        normalized = []

        for binding in combined:
            value = normalize_binding(
                item.get("kind"),
                binding
            )
            if value is not None:
                normalized.append(value)

        item["bindings"] = normalized
        item.pop("callbacks", None)
        item.pop("on_change_script", None)


__all__ = [
    "AddBindingDialog",
    "BindingPage",
    "BindingPanel",
]
