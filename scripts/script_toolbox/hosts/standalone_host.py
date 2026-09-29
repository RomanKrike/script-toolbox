# -*- coding: utf-8 -*-
from __future__ import print_function

from .base import BaseHost


class StandaloneHost(BaseHost):
    """Host adapter used when Script Toolbox runs outside a supported DCC."""

    key = "standalone"
    display_name = "Standalone"
    selection_noun = "items"


__all__ = [
    "StandaloneHost",
]
