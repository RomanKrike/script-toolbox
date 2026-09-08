# -*- coding: utf-8 -*-
from __future__ import print_function

import os


class BaseHost(object):

    key = "standalone"
    display_name = "Standalone"
    selection_noun = "items"

    def app_version(self):
        return ""

    def current_selection(
        self,
        long_names=True
    ):
        return []

    def object_exists(
        self,
        name
    ):
        return False

    def select_objects(
        self,
        names
    ):
        return False

    def supports_callback(
        self,
        event_name
    ):
        """Return whether this host can provide a native callback event."""
        return False

    def add_callback(
        self,
        event_name,
        callback
    ):
        """Subscribe to a host event and return an opaque handle or None."""
        return None

    def remove_callback(
        self,
        handle
    ):
        """Remove a callback handle returned by add_callback()."""
        if handle is None:
            return False

        try:
            return bool(
                handle.close()
            )
        except Exception:
            return False

    def available_languages(self):
        return (
            "python",
        )

    def script_namespace(self):
        return {
            "host": self,
        }

    def execute_native(
        self,
        language,
        code
    ):
        raise RuntimeError(
            "Language '{0}' is not available in {1}.".format(
                language,
                self.display_name
            )
        )

    def user_config_dir(self):
        return os.path.expanduser(
            "~"
        )

    def config_filename(self):
        return "script_toolbox.json"

    def shift_pressed_native(self):
        return None


__all__ = [
    "BaseHost",
]
