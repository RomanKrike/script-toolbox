# -*- coding: utf-8 -*-
from __future__ import print_function

import os

from ..compat import QtCore
from ..compat import QtGui
from ..core.executor import evaluate_python_state
from ..core.executor import execute_script_result
from ..pycompat import text_type


_EVENT_MARKER = "_script_toolbox_toggle_icon_event_hooks"
_MAIN_MARKER = "_script_toolbox_toggle_icon_main_window"


def _expanded_path(value):
    return os.path.expanduser(
        os.path.expandvars(
            text_type(value or "")
        )
    )


def _state_value(toolbox, item):
    if item.get("state_source", "internal") == "script":
        return evaluate_python_state(
            item.get("state_get_script", ""),
            toolbox=toolbox,
            parent=toolbox
        )
    return bool(
        item.get("value", False)
    )


def _apply_icon_state(widget, item, state):
    width = int(item.get("width", 24))
    height = int(item.get("height", 24))
    path = _expanded_path(
        item.get(
            "state_on_path" if state else "state_off_path",
            ""
        )
    )

    widget.setFixedSize(width, height)
    widget.setAlignment(
        QtCore.Qt.AlignCenter
    )
    widget.setProperty(
        "stateOn",
        bool(state)
    )

    if path:
        icon = QtGui.QIcon(path)
        pixmap = icon.pixmap(
            width,
            height
        )
    else:
        pixmap = QtGui.QPixmap()

    if not pixmap.isNull():
        widget.setPixmap(pixmap)
        widget.setText("")
    else:
        widget.setPixmap(QtGui.QPixmap())
        widget.setText("?")


def render_toggle_icon(owner, item, compact=False):
    width = int(item.get("width", 24))
    height = int(item.get("height", 24))

    icon_widget = QtGui.QLabel()
    icon_widget.setFixedSize(width, height)
    icon_widget.setAlignment(
        QtCore.Qt.AlignCenter
    )
    icon_widget.setToolTip(
        item.get("tooltip", "")
    )

    state = _state_value(
        owner.toolbox,
        item
    )
    if state is None:
        state = False
    _apply_icon_state(
        icon_widget,
        item,
        state
    )

    register = getattr(
        owner.toolbox,
        "register_toggle_icon",
        None
    )
    if register is not None:
        register(
            item.get("id"),
            icon_widget
        )

    container = QtGui.QWidget()
    container.setToolTip(
        item.get("tooltip", "")
    )
    layout = QtGui.QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    alignment = item.get(
        "content_alignment",
        "left"
    )
    if alignment in ("center", "right"):
        layout.addStretch(1)
    layout.addWidget(
        icon_widget,
        0,
        QtCore.Qt.AlignVCenter
    )
    if alignment == "center":
        layout.addStretch(1)

    return container


def install_toggle_icon_event_hooks(event_binding_module):
    if getattr(
        event_binding_module,
        _EVENT_MARKER,
        False
    ):
        return

    original_mouse_targets = event_binding_module._mouse_targets

    def mouse_targets(widget, kind):
        if kind == "toggle_icon":
            kind = "icon"
        return original_mouse_targets(
            widget,
            kind
        )

    event_binding_module._mouse_targets = mouse_targets

    setattr(
        event_binding_module,
        _EVENT_MARKER,
        True
    )


def install_toggle_icon_main_window(main_window_class):
    if getattr(
        main_window_class,
        _MAIN_MARKER,
        False
    ):
        return

    original_rebuild = main_window_class.rebuild
    original_refresh_state_buttons = main_window_class.refresh_state_buttons
    original_run_state_binding = main_window_class.run_state_binding
    original_run_item = main_window_class.run_item

    def register_toggle_icon(self, item_id, widget):
        registry = getattr(
            self,
            "toggle_icon_widgets",
            None
        )
        if registry is None:
            registry = {}
            self.toggle_icon_widgets = registry
        registry[
            text_type(item_id)
        ] = widget

    def refresh_toggle_icon(self, key):
        item = self.find_item(key)
        if (
            item is None or
            item.get("kind") != "toggle_icon"
        ):
            return False

        registry = getattr(
            self,
            "toggle_icon_widgets",
            {}
        )
        widget = registry.get(
            item.get("id")
        )
        if widget is None:
            return False

        state = _state_value(
            self,
            item
        )
        if state is None:
            return None

        _apply_icon_state(
            widget,
            item,
            state
        )
        return bool(state)

    def refresh_state_buttons(self):
        result = original_refresh_state_buttons(
            self
        )
        for item_id in list(
            getattr(
                self,
                "toggle_icon_widgets",
                {}
            ).keys()
        ):
            try:
                self.refresh_toggle_icon(
                    item_id
                )
            except Exception:
                pass
        return result

    def rebuild(self):
        self.toggle_icon_widgets = {}
        return original_rebuild(
            self
        )

    def run_state_binding(
        self,
        item_or_id,
        binding=None,
        event=None
    ):
        item = (
            item_or_id
            if isinstance(item_or_id, dict)
            else self.find_item(item_or_id)
        )
        if (
            item is None or
            item.get("kind") != "toggle_icon"
        ):
            return original_run_state_binding(
                self,
                item_or_id,
                binding=binding,
                event=event
            )

        state = self.refresh_toggle_icon(
            item.get("id")
        )
        if state is None:
            return None

        if state:
            code = item.get("state_off_script", "")
            language = item.get("state_off_language", "python")
        else:
            code = item.get("state_on_script", "")
            language = item.get("state_on_language", "python")

        result = execute_script_result(
            code,
            language=language,
            toolbox=self,
            parent=self,
            extra_namespace={
                "toolbox": self,
                "item": item,
                "event": event or {},
            },
            context="toggle_icon:{0}".format(
                item.get("name", item.get("id", "toggle_icon"))
            ),
            notify=True
        )

        if item.get("state_source", "internal") == "internal":
            if result.success:
                self.store_value(
                    item.get("id"),
                    not bool(state)
                )
            else:
                self.refresh_toggle_icon(
                    item.get("id")
                )
        else:
            self.refresh_toggle_icon(
                item.get("id")
            )

        return result

    def run_item(self, item_id):
        item = self.find_item(item_id)
        if (
            item is None or
            item.get("kind") != "toggle_icon"
        ):
            return original_run_item(
                self,
                item_id
            )

        return self.dispatch_binding_event(
            item,
            "click",
            mouse_button="left",
            modifiers=[]
        )

    main_window_class.register_toggle_icon = register_toggle_icon
    main_window_class.refresh_toggle_icon = refresh_toggle_icon
    main_window_class.refresh_state_buttons = refresh_state_buttons
    main_window_class.rebuild = rebuild
    main_window_class.run_state_binding = run_state_binding
    main_window_class.run_item = run_item

    setattr(
        main_window_class,
        _MAIN_MARKER,
        True
    )


__all__ = [
    "install_toggle_icon_event_hooks",
    "install_toggle_icon_main_window",
    "render_toggle_icon",
]
