# -*- coding: utf-8 -*-
from __future__ import print_function

from .image import image_definition


def builtin_extension_definitions():
    """Return built-ins implemented as independent Item definition modules."""
    return (
        image_definition(),
    )


__all__ = [
    "builtin_extension_definitions",
]
