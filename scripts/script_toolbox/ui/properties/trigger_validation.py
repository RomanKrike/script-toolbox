# -*- coding: utf-8 -*-
from __future__ import print_function

from ...model.bindings import binding_signature
from . import bindings as bindings_module


_INSTALLED = False


def _duplicate_signature(self, candidate, ignore_page=None):
    signature = binding_signature(candidate)

    for page in self.pages:
        if page is ignore_page:
            continue
        if binding_signature(page.write()) == signature:
            return True

    return False


def install_trigger_signature_validation():
    global _INSTALLED
    if _INSTALLED:
        return
    _INSTALLED = True

    bindings_module.BindingPanel._duplicate_signature = _duplicate_signature


__all__ = [
    "install_trigger_signature_validation",
]
