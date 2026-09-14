# -*- coding: utf-8 -*-
from __future__ import print_function

from ..core.executor import execute_script_result
from ..core.state_toggle import state_toggle_action
from ..model.item_builtins import register_builtin_items
from ..model.item_registry import ITEM_TYPES
from ..model.item_view import ItemDataView


_HOOK_MARKER = "_script_toolbox_state_toggle_behavior"


def install_state_toggle_behavior(toolbox_class):
    """Install shared state-toggle semantics for capable Item types."""
    if getattr(toolbox_class, _HOOK_MARKER, False):
        return False

    def run_state_binding(self, item_or_id, binding=None, event=None):
        item = (
            item_or_id
            if isinstance(item_or_id, (dict, ItemDataView))
            else self.find_item(item_or_id)
        )
        if item is None:
            return None

        register_builtin_items()
        definition = ITEM_TYPES.get(item.get("kind"))
        if (
            definition is None or
            not definition.has_capability("state_toggle")
        ):
            return None

        state = self._state_value(item)
        if state is None:
            return None

        action = state_toggle_action(
            item,
            state
        )
        result = execute_script_result(
            action["script"],
            language=action["language"],
            toolbox=self,
            parent=self,
            extra_namespace={
                "toolbox": self,
                "item": item,
                "event": event or {},
            },
            context="state:{0}".format(
                item.get("name", item.get("id", "toggle"))
            ),
            notify=True
        )

        if action["stores_value"]:
            if result.success:
                self.store_value(
                    item.get("id"),
                    action["next_state"]
                )
        else:
            self.refresh_state_buttons()
        return result

    toolbox_class.run_state_binding = run_state_binding
    setattr(toolbox_class, _HOOK_MARKER, True)
    return True


__all__ = [
    "install_state_toggle_behavior",
]
