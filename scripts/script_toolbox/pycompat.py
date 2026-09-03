# -*- coding: utf-8 -*-
from __future__ import print_function

try:
    text_type = unicode
except NameError:
    text_type = str

try:
    integer_type = long
except NameError:
    integer_type = int

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

__all__ = [
    "text_type",
    "integer_type",
    "StringIO",
]
