# -*- coding: utf-8 -*-

from .registry import PROPERTY_EDITORS
from .registry import create_editor
from .registry import editor_class
from .trigger_tabs import install_integrated_trigger_tabs
from .script_editor_sizing import install_expanding_script_editors


install_integrated_trigger_tabs()
install_expanding_script_editors()


__all__ = [
    "PROPERTY_EDITORS",
    "create_editor",
    "editor_class",
]
