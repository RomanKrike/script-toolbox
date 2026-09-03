# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import os

import nuke

try:
    import nukescripts
except ImportError:
    nukescripts = None

from .base import BaseHost


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
]
