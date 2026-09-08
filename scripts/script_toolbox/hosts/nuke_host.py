# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import os
import sys

from .base import BaseHost
from .callbacks import EVENT_SELECTION_CHANGED
from .callbacks import HostCallbackHandle


def _resolve_nuke_module():
    """
    Resolve Nuke's real built-in Python API without colliding with
    Script Toolbox package module names under Python 2.7.
    """
    module = sys.modules.get(
        "nuke"
    )

    if (
        module is not None and
        hasattr(
            module,
            "selectedNodes"
        )
    ):
        return module

    main_module = sys.modules.get(
        "__main__"
    )

    if main_module is not None:
        candidate = getattr(
            main_module,
            "nuke",
            None
        )

        if (
            candidate is not None and
            hasattr(
                candidate,
                "selectedNodes"
            )
        ):
            return candidate

    try:
        module = __import__(
            "nuke",
            globals(),
            locals(),
            [],
            0
        )
    except Exception:
        module = None

    if (
        module is None or
        not hasattr(
            module,
            "selectedNodes"
        )
    ):
        module_name = getattr(
            module,
            "__name__",
            "<missing>"
        )
        module_file = getattr(
            module,
            "__file__",
            "<built-in/no file>"
        )

        raise ImportError(
            "Could not resolve the real Nuke Python API. "
            "Resolved module: {0} ({1})".format(
                module_name,
                module_file
            )
        )

    return module


nuke = _resolve_nuke_module()

try:
    nukescripts = __import__(
        "nukescripts",
        globals(),
        locals(),
        [],
        0
    )
except ImportError:
    nukescripts = None


class NukeHost(BaseHost):

    key = "nuke"
    display_name = "Nuke"
    selection_noun = "Nuke nodes"

    def app_version(self):
        try:
            return str(
                nuke.NUKE_VERSION_STRING
            )
        except Exception:
            return ""

    def current_selection(
        self,
        long_names=True
    ):
        nodes = nuke.selectedNodes() or []

        if long_names:
            result = []

            for node in nodes:
                try:
                    result.append(
                        node.fullName()
                    )
                except Exception:
                    result.append(
                        node.name()
                    )

            return result

        return [
            node.name()
            for node in nodes
        ]

    def _node(
        self,
        name
    ):
        try:
            return nuke.toNode(
                str(
                    name
                )
            )
        except Exception:
            return None

    def object_exists(
        self,
        name
    ):
        return self._node(
            name
        ) is not None

    def select_objects(
        self,
        names
    ):
        try:
            for node in nuke.selectedNodes() or []:
                try:
                    node.setSelected(
                        False
                    )
                except Exception:
                    pass

            selected = False

            for name in names:
                node = self._node(
                    name
                )

                if node is None:
                    continue

                node.setSelected(
                    True
                )
                selected = True

            return selected

        except Exception:
            return False

    def supports_callback(
        self,
        event_name
    ):
        return (
            event_name == EVENT_SELECTION_CHANGED and
            callable(
                getattr(
                    nuke,
                    "addUpdateUI",
                    None
                )
            ) and
            callable(
                getattr(
                    nuke,
                    "removeUpdateUI",
                    None
                )
            )
        )

    def _remove_update_ui(
        self,
        callback
    ):
        try:
            nuke.removeUpdateUI(
                callback
            )
            return True
        except Exception:
            return False

    def add_callback(
        self,
        event_name,
        callback
    ):
        if not self.supports_callback(
            event_name
        ):
            return None

        try:
            last_signature = [
                tuple(
                    self.current_selection(
                        long_names=True
                    ) or []
                )
            ]
        except Exception:
            last_signature = [tuple()]

        def _update_ui():
            try:
                signature = tuple(
                    self.current_selection(
                        long_names=True
                    ) or []
                )
            except Exception:
                return

            if signature == last_signature[0]:
                return

            last_signature[0] = signature
            callback()

        try:
            nuke.addUpdateUI(
                _update_ui
            )
        except Exception:
            return None

        return HostCallbackHandle(
            event_name,
            _update_ui,
            self._remove_update_ui
        )

    def available_languages(self):
        return (
            "python",
        )

    def script_namespace(self):
        namespace = {
            "host": self,
            "nuke": nuke,
        }

        if nukescripts is not None:
            namespace[
                "nukescripts"
            ] = nukescripts

        return namespace

    def user_config_dir(self):
        return os.path.join(
            os.path.expanduser(
                "~"
            ),
            ".nuke"
        )

    def config_filename(self):
        return "nuke_script_toolbox.json"


__all__ = [
    "NukeHost",
    "nuke",
    "nukescripts",
]
