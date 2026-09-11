# -*- coding: utf-8 -*-
from __future__ import print_function

from ..pycompat import text_type


def state_toggle_action(item, current_state):
    """Describe the script and stored-value transition for one toggle click."""
    state = bool(current_state)
    if state:
        script = text_type(item.get("state_off_script", "") or "")
        language = text_type(
            item.get("state_off_language", "python") or "python"
        )
    else:
        script = text_type(item.get("state_on_script", "") or "")
        language = text_type(
            item.get("state_on_language", "python") or "python"
        )

    internal = item.get("state_source", "internal") == "internal"
    return {
        "current_state": state,
        "next_state": not state,
        "script": script,
        "language": language.lower(),
        "stores_value": internal,
    }


__all__ = [
    "state_toggle_action",
]
