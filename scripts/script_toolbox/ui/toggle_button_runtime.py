# -*- coding: utf-8 -*-
from __future__ import print_function

import os

from ..compat import QtCore
from ..compat import QtGui
from ..core.executor import evaluate_python_state
from ..core.executor import execute_script_result
from ..model.items import safe_color
from ..pycompat import text_type


_EVENT_MARKER = "_script_toolbox_toggle_button_event_hooks"
_MAIN_MARKER = "_script_toolbox_toggle_button_main_window"


def render_toggle_button(owner, item, compact=False):
    # Reuse the mature QPushButton construction path while keeping the model
    # kind independent from Button. The shadow exists only for widget creation.
    shadow = dict(item)
    shadow["kind"] = "button"
    shadow["mode"] = "state"

    button = owner._button_widget(
        shadow
    )

    icon_path = os.path.expanduser(
        os.path.expandvars(
            text_type(
                item.get("icon_path") or ""
            )
        )
    )
    icon_size = int(
        item.get("icon_size", 18)
    )

    if icon_path:
        button.setIcon(
            QtGui.QIcon(icon_path)
        )
        button.setIconSize(
            QtCore.QSize(
                icon_size,
                icon_size
            )
        )

    if item.get("icon_only", False):
        button.setText("")

    return button


def install_toggle_button_event_hooks(event_binding_module):
    if getattr(
        event_binding_module,
        _EVENT_MARKER,
        False
    ):
        return

    original_mouse_targets = event_binding_module._mouse_targets

    def mouse_targets(widget, kind):
        if kind == "toggle_button":
            kind = "button"
        return original_mouse_targets(
            widget,
            kind
        )

    event_binding_module._mouse_targets = mouse_targets

    filter_class = event_binding_module.MouseBindingFilter
    original_suppress = filter_class._suppress_button_clicked

    def suppress_button_clicked(self, button):
        if self.item.get("kind") != "toggle_button":
            return original_suppress(
                self,
                button
            )

        # The legacy suppression helper only recognizes kind=button. Present a
        # temporary compatibility view so the final QPushButton.clicked signal
        # does not dispatch the same binding a second time.
        original_kind = self.item.get("kind")
        self.item["kind"] = "button"
        try:
            return original_suppress(
                self,
                button
            )
        finally:
            self.item["kind"] = original_kind

    filter_class._suppress_button_clicked = suppress_button_clicked

    setattr(
        event_binding_module,
        _EVENT_MARKER,
        True
    )


def install_toggle_button_main_window(main_window_class):
    if getattr(
        main_window_class,
        _MAIN_MARKER,
        False
    ):
        return

    original_refresh_state_button = main_window_class.refresh_state_button
    original_run_state_binding = main_window_class.run_state_binding
    original_run_item = main_window_class.run_item

    def refresh_state_button(self, key):
        item = self.find_item(key)

        if (
            item is None or
            item.get("kind") != "toggle_button"
        ):
            return original_refresh_state_button(
                self,
                key
            )

        widget = self.state_button_widgets.get(
            item["id"]
        )
        if widget is None:
            return False

        if item.get("state_source", "internal") == "script":
            state = evaluate_python_state(
                item.get("state_get_script", ""),
                toolbox=self,
                parent=self
            )
            if state is None:
                return None
        else:
            state = bool(
                item.get("value", False)
            )

        label = item.get(
            "state_on_label" if state else "state_off_label",
            item.get("label", item.get("name", "Toggle"))
        )
        color = safe_color(
            item.get(
                "state_on_color" if state else "state_off_color"
            )
        )
        rgb = [
            int(value * 255)
            for value in color
        ]

        if item.get("icon_only", False):
            widget.setText("")
        else:
            widget.setText(
                text_type(label)
            )
        widget.setProperty(
            "stateOn",
            bool(state)
        )
        widget.setStyleSheet(
            "QPushButton#ScriptButton {"
            "background-color: rgb(%d,%d,%d);"
            "}" % (
                rgb[0],
                rgb[1],
                rgb[2]
            )
        )
        return bool(state)

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
            item.get("kind") != "toggle_button"
        ):
            return original_run_state_binding(
                self,
                item_or_id,
                binding=binding,
                event=event
            )

        if item.get("state_source", "internal") == "script":
            return original_run_state_binding(
                self,
                item,
                binding=binding,
                event=event
            )

        state = self.refresh_state_button(
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
            context="toggle:{0}".format(
                item.get("name", item.get("id", "toggle_button"))
            ),
            notify=True
        )

        if result.success:
            self.store_value(
                item.get("id"),
                not bool(state)
            )
        else:
            self.refresh_state_button(
                item.get("id")
            )

        return result

    def run_item(self, item_id):
        item = self.find_item(item_id)
        if (
            item is None or
            item.get("kind") != "toggle_button"
        ):
            return original_run_item(
                self,
                item_id
            )

        suppressed = getattr(
            self,
            "_binding_widget_click_suppression",
            None
        )
        normalized_id = text_type(
            item.get("id", item_id)
        )
        if (
            suppressed is not None and
            normalized_id in suppressed
        ):
            suppressed.discard(
                normalized_id
            )
            return None

        return self.dispatch_binding_event(
            item,
            "click",
            mouse_button="left",
            modifiers=[]
        )

    main_window_class.refresh_state_button = refresh_state_button
    main_window_class.run_state_binding = run_state_binding
    main_window_class.run_item = run_item

    setattr(
        main_window_class,
        _MAIN_MARKER,
        True
    )


__all__ = [
    "install_toggle_button_event_hooks",
    "install_toggle_button_main_window",
    "render_toggle_button",
]
