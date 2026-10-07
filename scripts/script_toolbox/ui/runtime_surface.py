# -*- coding: utf-8 -*-
"""Prepare Qt surfaces with isolated document and registration ownership."""
from __future__ import print_function

from ..compat import QtCore, QtGui
from ..core.values import find_item, get_value
from ..pycompat import text_type
from ..style import metrics
from .layout_helpers import configure_layout
from .runtime_value_sync import RuntimeValueMixin


class RuntimeSurfaceToolbox(RuntimeValueMixin):
    """Limited construction API; active callbacks forward to the live window."""

    def __init__(self, window, document):
        self._window = window
        self.document = document
        self.active = False
        self.disposed = False
        self.value_widgets = {}
        self.field_widgets = {}
        self.state_button_widgets = {}
        self.toggle_icon_widgets = {}

    @property
    def config(self):
        return self._window.config if self.active else self.document

    def find_item(self, key):
        return find_item(self.config, key) if not self.disposed else None

    def get_value(self, key, default=None):
        return get_value(self.config, key, default) if not self.disposed else default

    def register_field_widget(self, item_id, widget):
        self.field_widgets[text_type(item_id)] = widget

    def register_state_button(self, item_id, widget):
        self.state_button_widgets[text_type(item_id)] = widget

    def register_toggle_icon(self, item_id, widget):
        self.toggle_icon_widgets[text_type(item_id)] = widget

    def _presentation(self, name, *args):
        from .main_window import ScriptToolbox
        method = getattr(ScriptToolbox, name)
        function = getattr(method, "__func__", getattr(method, "im_func", method))
        return function(self, *args)

    def field_display_values(self, key):
        return self._presentation("field_display_values", key)

    def field_display_text(self, key):
        return self._presentation("field_display_text", key)

    def refresh_field_widget(self, key):
        return self._presentation("refresh_field_widget", key)

    def _state_value(self, item):
        # Preparing widgets must not execute user state scripts.
        return self._window._state_value(item) if self.active else bool(item.get("props", {}).get("value", False))

    def _toggle_icon_path(self, item, state):
        return self._presentation("_toggle_icon_path", item, state)

    def refresh_state_button(self, key):
        return self._presentation("refresh_state_button", key)

    def refresh_toggle_icon(self, key):
        return self._presentation("refresh_toggle_icon", key)

    def _invoke(self, name, *args, **kwargs):
        if self.disposed:
            return False
        if not self.active:
            raise RuntimeError("Runtime construction cannot call " + name)
        return getattr(self._window, name)(*args, **kwargs)

    def store_value(self, *args, **kwargs):
        return self._invoke("store_value", *args, **kwargs)

    def save(self, *args, **kwargs):
        return self._invoke("save", *args, **kwargs)

    def run_item(self, *args, **kwargs):
        return self._invoke("run_item", *args, **kwargs)

    def dispatch_binding_event(self, *args, **kwargs):
        return self._invoke("dispatch_binding_event", *args, **kwargs)

    def __getattr__(self, name):
        if self.active and not self.disposed:
            return getattr(self._window, name)
        raise AttributeError("Runtime construction does not expose " + name)

    def dispose(self):
        self.active = False
        self.disposed = True
        self.clear_value_widgets()
        self.field_widgets.clear()
        self.state_button_widgets.clear()
        self.toggle_icon_widgets.clear()
        self.document = None
        self._window = None


def capture_view_state(window):
    selected = []
    for tabs in window.content.findChildren(QtGui.QTabWidget):
        page = tabs.currentWidget()
        section = getattr(page, "section", {})
        if section.get("id"):
            selected.append(section["id"])
    for stack in window.content.findChildren(QtGui.QStackedWidget):
        section = getattr(stack.currentWidget(), "section", {})
        if section.get("id"):
            selected.append(section["id"])
    return (selected, window.scroll.horizontalScrollBar().value(),
            window.scroll.verticalScrollBar().value())


def restore_view_state(window, state):
    selected, horizontal, vertical = state
    for tabs in window.content.findChildren(QtGui.QTabWidget):
        for index in range(tabs.count()):
            if getattr(tabs.widget(index), "section", {}).get("id") in selected:
                tabs.setCurrentIndex(index)
                break
    for stack in window.content.findChildren(QtGui.QStackedWidget):
        for index in range(stack.count()):
            if getattr(stack.widget(index), "section", {}).get("id") in selected:
                group = getattr(stack.parentWidget(), "group", None)
                if group is not None and group.button(index) is not None:
                    group.button(index).setChecked(True)
                else:
                    stack.setCurrentIndex(index)
                break
    window.scroll.horizontalScrollBar().setValue(horizontal)
    window.scroll.verticalScrollBar().setValue(vertical)


class RuntimeSurface(object):
    def __init__(self, window, document):
        self.disposed = False
        self.context = RuntimeSurfaceToolbox(window, document)
        self.content = QtGui.QWidget()
        self.content.setObjectName("ToolboxContent")
        self.content.setEnabled(False)
        self.layout = QtGui.QVBoxLayout(self.content)
        configure_layout(self.layout, margins=metrics.TOOLBOX_CONTENT_MARGINS,
                         spacing=metrics.TOOLBOX_CONTENT_SPACING)
        self.layout.addStretch(1)

    def prepare(self, document):
        from .runtime import build_folder_widgets
        try:
            widgets = build_folder_widgets(self.context, document["sections"], self.content)
            for widget in widgets:
                self.layout.insertWidget(self.layout.count() - 1, widget)
            return self
        except Exception:
            self.dispose()
            raise

    def activate(self, window, state):
        names = ("content", "content_layout", "value_widgets", "field_widgets",
                 "state_button_widgets", "toggle_icon_widgets", "runtime_surface")
        previous = dict((name, getattr(window, name, None)) for name in names)
        previous_content = window.scroll.takeWidget()
        try:
            window.scroll.setWidget(self.content)
            window.content, window.content_layout = self.content, self.layout
            for name in names[2:-1]:
                setattr(window, name, getattr(self.context, name))
            window.runtime_surface = self
            self.context.active = True
            self.content.setEnabled(True)
            restore_view_state(window, state)
            timer = QtCore.QTimer(self.content)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: restore_view_state(window, state)
                                  if getattr(window, "runtime_surface", None) is self else None)
            timer.start(0)
        except Exception:
            self.context.active = False
            if window.scroll.widget() is self.content:
                window.scroll.takeWidget()
            for name, value in previous.items():
                setattr(window, name, value)
            window.scroll.setWidget(previous_content)
            raise
        window._runtime_unavailable = False
        selection_timer = getattr(window, "selection_timer", None)
        if selection_timer is not None:
            selection_timer.start()
        old = previous["runtime_surface"]
        if old is not None:
            old.dispose()
        elif previous_content is not None:
            previous_content.deleteLater()

    def dispose(self):
        if self.disposed:
            return
        self.disposed = True
        self.context.dispose()
        self.content.setEnabled(False)
        self.content.deleteLater()
