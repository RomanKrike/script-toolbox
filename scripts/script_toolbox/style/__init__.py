# -*- coding: utf-8 -*-

from .app_icon import application_icon
from .app_icon import application_icon_path
from .app_icon import apply_window_icon
from .builtin_icons import builtin_icon
from .components import COMPONENT_STYLES
from .icons import toolbar_icon as _legacy_toolbar_icon
from .runtime_overrides import RUNTIME_OVERRIDES
from .stylesheet import STYLE as BASE_STYLE

STYLE = BASE_STYLE + COMPONENT_STYLES + RUNTIME_OVERRIDES


def toolbar_icon(kind):
    icon = builtin_icon(kind)

    if not icon.isNull():
        return icon

    return _legacy_toolbar_icon(kind)


__all__ = [
    "STYLE",
    "application_icon",
    "application_icon_path",
    "apply_window_icon",
    "toolbar_icon",
]
