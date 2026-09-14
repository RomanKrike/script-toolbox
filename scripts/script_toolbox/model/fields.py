# -*- coding: utf-8 -*-
from __future__ import print_function

import copy
import os

from ..pycompat import text_type


class Field(object):
    def __init__(self, default=None):
        self.default = default

    def default_value(self):
        return copy.deepcopy(self.default)

    def normalize(self, value):
        if value is None:
            return self.default_value()
        return value


class AnyField(Field):
    pass


class TextField(Field):
    def normalize(self, value):
        if value is None:
            value = self.default_value()
        return text_type(value or "")


class BoolField(Field):
    def normalize(self, value):
        if value is None:
            value = self.default_value()
        return bool(value)


class IntField(Field):
    def __init__(self, default=0, minimum=None, maximum=None):
        Field.__init__(self, default=default)
        self.minimum = minimum
        self.maximum = maximum

    def normalize(self, value):
        if value is None:
            value = self.default_value()
        try:
            value = int(value)
        except Exception:
            value = int(self.default_value() or 0)
        if self.minimum is not None:
            value = max(int(self.minimum), value)
        if self.maximum is not None:
            value = min(int(self.maximum), value)
        return value


class FloatField(Field):
    def __init__(self, default=0.0, minimum=None, maximum=None):
        Field.__init__(self, default=default)
        self.minimum = minimum
        self.maximum = maximum

    def normalize(self, value):
        if value is None:
            value = self.default_value()
        try:
            value = float(value)
        except Exception:
            value = float(self.default_value() or 0.0)
        if self.minimum is not None:
            value = max(float(self.minimum), value)
        if self.maximum is not None:
            value = min(float(self.maximum), value)
        return value


class ChoiceField(Field):
    def __init__(self, choices, default=None, case_sensitive=False):
        self.choices = tuple(choices or ())
        self.case_sensitive = bool(case_sensitive)
        if default is None and self.choices:
            default = self.choices[0]
        Field.__init__(self, default=default)

    def normalize(self, value):
        if value is None:
            value = self.default_value()
        if self.case_sensitive:
            return value if value in self.choices else self.default_value()
        candidate = text_type(value or "").lower()
        for choice in self.choices:
            if text_type(choice).lower() == candidate:
                return choice
        return self.default_value()


class ColorField(Field):
    def __init__(self, default=None):
        Field.__init__(
            self,
            default=list(default or [0.25, 0.25, 0.25])
        )

    def normalize(self, value):
        if not isinstance(value, (list, tuple)) or len(value) != 3:
            value = self.default_value()
        result = []
        for entry in value:
            try:
                entry = float(entry)
            except Exception:
                entry = 0.25
            result.append(max(0.0, min(1.0, entry)))
        return result


class PathField(TextField):
    def __init__(self, default="", expand=False):
        TextField.__init__(self, default=default)
        self.expand = bool(expand)

    def normalize(self, value):
        value = TextField.normalize(self, value)
        if self.expand and value:
            value = os.path.expanduser(os.path.expandvars(value))
        return value


class ListField(Field):
    def __init__(self, default=None, item_field=None, minimum=None, maximum=None):
        Field.__init__(self, default=list(default or []))
        self.item_field = item_field
        self.minimum = minimum
        self.maximum = maximum

    def normalize(self, value):
        if value is None:
            value = self.default_value()
        if not isinstance(value, (list, tuple)):
            value = [value]
        result = list(value)
        if self.item_field is not None:
            result = [self.item_field.normalize(entry) for entry in result]
        if self.maximum is not None:
            result = result[:int(self.maximum)]
        if self.minimum is not None:
            while len(result) < int(self.minimum):
                if self.item_field is not None:
                    result.append(self.item_field.default_value())
                else:
                    result.append(None)
        return result


__all__ = [
    "AnyField",
    "BoolField",
    "ChoiceField",
    "ColorField",
    "Field",
    "FloatField",
    "IntField",
    "ListField",
    "PathField",
    "TextField",
]
