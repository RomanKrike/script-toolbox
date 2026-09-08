# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import os

import hou

from .base import BaseHost
from .callbacks import EVENT_SELECTION_CHANGED
from .callbacks import HostCallbackHandle


class HoudiniHost(BaseHost):

    key = "houdini"
    display_name = "Houdini"
    selection_noun = "Houdini nodes"

    def app_version(self):
        try:
            return str(
                hou.applicationVersionString()
            )
        except Exception:
            return ""

    def current_selection(
        self,
        long_names=True
    ):
        try:
            nodes = hou.selectedNodes() or []
        except Exception:
            return []

        result = []

        for node in nodes:
            try:
                if long_names:
                    result.append(
                        node.path()
                    )
                else:
                    result.append(
                        node.name()
                    )
            except Exception:
                pass

        return result

    def _node(
        self,
        name
    ):
        try:
            return hou.node(
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
            hou.clearAllSelected()
        except Exception:
            return False

        selected = False

        for name in names:
            node = self._node(
                name
            )

            if node is None:
                continue

            try:
                node.setSelected(
                    True,
                    clear_all_selected=False
                )
                selected = True
            except TypeError:
                try:
                    node.setSelected(
                        True
                    )
                    selected = True
                except Exception:
                    pass
            except Exception:
                pass

        return selected

    def supports_callback(
        self,
        event_name
    ):
        ui = getattr(
            hou,
            "ui",
            None
        )

        return (
            event_name == EVENT_SELECTION_CHANGED and
            ui is not None and
            callable(
                getattr(
                    ui,
                    "addSelectionCallback",
                    None
                )
            ) and
            callable(
                getattr(
                    ui,
                    "removeSelectionCallback",
                    None
                )
            )
        )

    def _remove_selection_callback(
        self,
        callback
    ):
        try:
            hou.ui.removeSelectionCallback(
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

        def _selection_changed(selection):
            callback()

        try:
            hou.ui.addSelectionCallback(
                _selection_changed
            )
        except Exception:
            return None

        return HostCallbackHandle(
            event_name,
            _selection_changed,
            self._remove_selection_callback
        )

    def available_languages(self):
        return (
            "python",
            "hscript",
        )

    def script_namespace(self):
        return {
            "host": self,
            "hou": hou,
        }

    def execute_native(
        self,
        language,
        code
    ):
        if language == "hscript":
            return hou.hscript(
                code
            )

        return BaseHost.execute_native(
            self,
            language,
            code
        )

    def user_config_dir(self):
        try:
            path = hou.getenv(
                "HOUDINI_USER_PREF_DIR"
            )
        except Exception:
            path = None

        path = (
            path or
            os.environ.get(
                "HOUDINI_USER_PREF_DIR"
            )
        )

        if path:
            return path

        return BaseHost.user_config_dir(
            self
        )

    def config_filename(self):
        return "houdini_script_toolbox.json"


__all__ = [
    "HoudiniHost",
    "hou",
]
