# -*- coding: utf-8 -*-

from .registry import PROPERTY_EDITORS
from .registry import create_editor
from .registry import editor_class
from .trigger_tabs import install_integrated_trigger_tabs


install_integrated_trigger_tabs()


__all__ = [
    "PROPERTY_EDITORS",
    "create_editor",
    "editor_class",
]
