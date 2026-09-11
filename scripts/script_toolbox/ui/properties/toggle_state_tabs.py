# -*- coding: utf-8 -*-
from __future__ import print_function

from ...compat import QtCore
from ...compat import QtGui
from ...model.bindings import binding_display_name
from ...pycompat import text_type
from . import bindings as bindings_module
from . import script_editor_sizing as sizing_module
from . import toggle_button as toggle_button_module
from . import toggle_icon as toggle_icon_module
from . import trigger_tabs as trigger_tabs_module


_INSTALLED = False
_AUXILIARY_TABS_ATTR = "_script_toolbox_auxiliary_tabs"


def _auxiliary_tabs(panel):
    tabs = getattr(panel, _AUXILIARY_TABS_ATTR, None)
    if tabs is None:
        tabs = []
        setattr(panel, _AUXILIARY_TABS_ATTR, tabs)
    return tabs


def _auxiliary_record(panel, key):
    key = text_type(key)
    for record in _auxiliary_tabs(panel):
        if record.get("key") == key:
            return record
    return None


def _script_auxiliary_editors(panel):
    return [
        record.get("widget")
        for record in _auxiliary_tabs(panel)
        if record.get("script_editor") and record.get("widget") is not None
    ]


def _configure_script_editor(editor):
    if editor is None:
        return

    try:
        editor.setMinimumHeight(
            sizing_module._preferred_script_editor_height
        )
    except Exception:
        pass

    try:
        editor.setSizePolicy(
            QtGui.QSizePolicy.Expanding,
            QtGui.QSizePolicy.Expanding
        )
    except Exception:
        pass


def _update_state_toggle_hint(page, binding):
    if binding.get("handler", "script") != "state_toggle":
        return

    message = (
        "This trigger toggles the state. Use Get State / Turn ON / Turn OFF "
        "tabs here to configure state behavior."
    )
    try:
        labels = page.findChildren(QtGui.QLabel)
    except Exception:
        labels = []

    for label in labels:
        try:
            if text_type(label.objectName()) != "HintText":
                continue
            label.setText(message)
            break
        except Exception:
            continue


def _integrate_editor_state_tabs(editor):
    state_tabs = getattr(editor, "state_tabs", None)
    panel = getattr(editor, "binding_panel", None)
    if state_tabs is None or panel is None:
        return

    tabs = (
        (
            "state_get",
            editor.state_get_editor,
            "Get State",
            "Python query that returns the current toggle state."
        ),
        (
            "state_on",
            editor.state_on_editor,
            "Turn ON",
            "Script executed when the toggle switches ON."
        ),
        (
            "state_off",
            editor.state_off_editor,
            "Turn OFF",
            "Script executed when the toggle switches OFF."
        ),
    )

    for key, widget, label, tooltip in tabs:
        try:
            index = state_tabs.indexOf(widget)
            if index >= 0:
                state_tabs.removeTab(index)
        except Exception:
            pass

        panel.add_auxiliary_tab(
            key,
            widget,
            label,
            tooltip=tooltip,
            script_editor=True
        )

    try:
        editor.trigger_section.content_layout.removeWidget(state_tabs)
    except Exception:
        pass

    try:
        editor._trigger_extra_widgets.remove(state_tabs)
    except Exception:
        pass

    try:
        state_tabs.hide()
        state_tabs.setParent(None)
        state_tabs.deleteLater()
    except Exception:
        pass

    editor._refresh_state_source()
    editor._refresh_trigger_section_visibility()


def _state_source_refresh(self):
    scripted = self.current_state_source() == "script"
    self.set_property_available(
        self.internal_state,
        not scripted,
        "Internal State is controlled by Get State when State Source is Script."
    )

    panel = getattr(self, "binding_panel", None)
    if panel is not None:
        try:
            updated = panel.set_auxiliary_tab_enabled(
                "state_get",
                scripted,
                disabled_tooltip=(
                    "Get State is used only when State Source is Script."
                )
            )
            if updated:
                return
        except Exception:
            pass

    state_tabs = getattr(self, "state_tabs", None)
    if state_tabs is not None:
        try:
            state_tabs.setTabEnabled(0, scripted)
            state_tabs.setTabToolTip(
                0,
                "" if scripted else (
                    "Get State is used only when State Source is Script."
                )
            )
            return
        except Exception:
            pass

    try:
        self.state_get_editor.setEnabled(scripted)
    except Exception:
        pass


def _install_editor_class(editor_class):
    original_init = editor_class.__init__

    def editor_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        _integrate_editor_state_tabs(self)

    editor_class._refresh_state_source = _state_source_refresh
    editor_class.__init__ = editor_init


def install_integrated_toggle_state_tabs():
    """Put toggle state scripts on the same tab strip as event bindings."""
    global _INSTALLED
    if _INSTALLED:
        return
    _INSTALLED = True

    panel_class = bindings_module.BindingPanel
    original_refresh_empty = panel_class._refresh_empty
    original_set_panel_height = (
        sizing_module._set_panel_script_editor_height
    )

    def add_auxiliary_tab(
        self,
        key,
        widget,
        label,
        tooltip="",
        script_editor=False
    ):
        key = text_type(key)
        record = _auxiliary_record(self, key)
        if record is not None:
            index = self.tabs.indexOf(record.get("widget"))
            if index >= 0:
                self.tabs.setTabText(index, text_type(label))
                self.tabs.setTabToolTip(index, text_type(tooltip or ""))
            return record.get("widget")

        self._remove_add_tab()
        records = _auxiliary_tabs(self)
        record = {
            "key": key,
            "widget": widget,
            "label": text_type(label),
            "tooltip": text_type(tooltip or ""),
            "script_editor": bool(script_editor),
        }
        records.append(record)

        try:
            insert_index = len(self.pages) + len(records) - 1
            index = self.tabs.insertTab(
                insert_index,
                widget,
                record["label"]
            )
            self.tabs.setTabToolTip(
                index,
                record["tooltip"]
            )
            if script_editor:
                _configure_script_editor(widget)
        finally:
            self._ensure_add_tab()

        self._refresh_empty()
        return widget

    def set_auxiliary_tab_enabled(
        self,
        key,
        enabled,
        disabled_tooltip=""
    ):
        record = _auxiliary_record(self, key)
        if record is None:
            return False

        index = self.tabs.indexOf(record.get("widget"))
        if index < 0:
            return False

        enabled = bool(enabled)
        self.tabs.setTabEnabled(index, enabled)
        self.tabs.setTabToolTip(
            index,
            record.get("tooltip", "") if enabled else text_type(
                disabled_tooltip or ""
            )
        )
        return True

    def script_editor_widgets(self):
        editors = []
        for page in getattr(self, "pages", []):
            editor = getattr(page, "script_editor", None)
            if editor is not None:
                editors.append(editor)
        editors.extend(_script_auxiliary_editors(self))
        return editors

    def clear(self):
        try:
            if self._add_tab_button is not None:
                self._add_tab_button.hide()
        except Exception:
            pass

        self._remove_add_tab()
        for page in list(getattr(self, "pages", [])):
            index = self.tabs.indexOf(page)
            if index >= 0:
                self.tabs.removeTab(index)
            try:
                page.deleteLater()
            except Exception:
                pass
        self.pages = []
        self._ensure_add_tab()
        self._refresh_empty()

    def add_page(self, binding):
        self._remove_add_tab()
        try:
            page = bindings_module.BindingPage(
                binding,
                toolbox=self.toolbox,
                parent=self.tabs
            )
            page.changed.connect(self._page_changed)
            insert_index = len(self.pages)
            self.pages.append(page)
            index = self.tabs.insertTab(
                insert_index,
                page,
                binding_display_name(binding)
            )
            self._update_tab_tooltip(index, binding)
            _update_state_toggle_hint(page, binding)
            self._install_trigger_close_button(page)
            return page
        finally:
            self._ensure_add_tab()

    def refresh_empty(self):
        original_refresh_empty(self)
        has_auxiliary = bool(_auxiliary_tabs(self))
        if has_auxiliary:
            self.tabs.setVisible(True)
            self.empty_label.setVisible(False)
            self.tabs.setMinimumHeight(0)
            self.tabs.setMaximumHeight(16777215)

        try:
            self.script_resize_handle.setVisible(
                bool(self.script_editor_widgets())
            )
        except Exception:
            pass

    def event_filter(self, watched, event):
        if watched is self.tabs.tabBar():
            event_type = event.type()

            if event_type in (
                QtCore.QEvent.Resize,
                QtCore.QEvent.Show,
                QtCore.QEvent.LayoutRequest,
            ):
                QtCore.QTimer.singleShot(
                    0,
                    self._position_add_button
                )

            if event_type == QtCore.QEvent.MouseButtonPress:
                index = watched.tabAt(event.pos())
                add_index = self.tabs.indexOf(
                    self._add_tab_page
                )

                if add_index >= 0 and index == add_index:
                    try:
                        if event.button() != QtCore.Qt.LeftButton:
                            return True
                    except Exception:
                        pass

                    QtCore.QTimer.singleShot(
                        0,
                        self.add_binding
                    )
                    return True

        return trigger_tabs_module._BaseBindingPanel.eventFilter(
            self,
            watched,
            event
        )

    def set_panel_script_editor_height(panel, value):
        value = original_set_panel_height(panel, value)
        for editor in _script_auxiliary_editors(panel):
            try:
                editor.setMinimumHeight(value)
                editor.updateGeometry()
            except Exception:
                pass
        return value

    panel_class.add_auxiliary_tab = add_auxiliary_tab
    panel_class.set_auxiliary_tab_enabled = set_auxiliary_tab_enabled
    panel_class.script_editor_widgets = script_editor_widgets
    panel_class.clear = clear
    panel_class._add_page = add_page
    panel_class._refresh_empty = refresh_empty
    panel_class.eventFilter = event_filter
    panel_class._script_toolbox_integrated_state_tabs = True

    sizing_module._set_panel_script_editor_height = (
        set_panel_script_editor_height
    )

    _install_editor_class(
        toggle_button_module.ToggleButtonPropertyEditor
    )
    _install_editor_class(
        toggle_icon_module.ToggleIconPropertyEditor
    )


__all__ = [
    "install_integrated_toggle_state_tabs",
]
