# -*- coding: utf-8 -*-
from __future__ import print_function

import copy
import os

from ..pycompat import integer_type
from ..pycompat import text_type


class FieldValidationError(ValueError):
    """Raised when a Field cannot coerce or validate an input value."""

    def __init__(self, value, reason):
        self.value = value
        self.reason = text_type(reason or "Invalid value")
        ValueError.__init__(self, self.reason)


class Field(object):
    def __init__(self, default=None, validator=None):
        self.default = default
        self.validator = validator

    def default_value(self):
        return copy.deepcopy(self.default)

    def _validate_custom(self, value):
        if self.validator is None:
            return True
        try:
            return bool(self.validator(value))
        except Exception:
            return False

    def _require_custom(self, value):
        if not self._validate_custom(value):
            raise FieldValidationError(value, "Custom validation failed")
        return value

    def validate(self, value):
        if value is None:
            value = self.default_value()
        return self._validate_custom(value)

    def normalize(self, value):
        if value is None:
            value = self.default_value()
        return self._require_custom(value)


class AnyField(Field):
    pass


class TextField(Field):
    def validate(self, value):
        if value is None:
            value = self.default_value()
        try:
            text_type(value if value is not None else "")
        except Exception:
            return False
        return self._validate_custom(value)

    def normalize(self, value):
        if value is None:
            value = self.default_value()
        try:
            result = text_type(value if value is not None else "")
        except Exception:
            raise FieldValidationError(value, "Expected text-compatible value")
        return self._require_custom(result)


class BoolField(Field):
    _TRUE_TEXT = frozenset(("true", "yes", "1"))
    _FALSE_TEXT = frozenset(("false", "no", "0"))

    def validate(self, value):
        if value is None:
            value = self.default_value()
        return isinstance(value, bool) and self._validate_custom(value)

    def normalize(self, value):
        if value is None:
            value = self.default_value()
        if isinstance(value, bool):
            result = value
        elif type(value) in (int, integer_type) and value in (0, 1):
            result = bool(value)
        elif isinstance(value, text_type):
            candidate = value.strip().lower()
            if candidate in self._TRUE_TEXT:
                result = True
            elif candidate in self._FALSE_TEXT:
                result = False
            else:
                raise FieldValidationError(
                    value,
                    "Expected boolean (true/false, yes/no, 1/0)"
                )
        else:
            raise FieldValidationError(
                value,
                "Expected boolean (true/false, yes/no, 1/0)"
            )
        return self._require_custom(result)


class IntField(Field):
    def __init__(
        self,
        default=0,
        minimum=None,
        maximum=None,
        validator=None
    ):
        Field.__init__(self, default=default, validator=validator)
        self.minimum = minimum
        self.maximum = maximum

    def _coerce(self, value):
        if isinstance(value, bool):
            raise FieldValidationError(value, "Expected integer")
        if isinstance(value, float) and not value.is_integer():
            raise FieldValidationError(value, "Expected integer")
        try:
            return int(value)
        except Exception:
            raise FieldValidationError(value, "Expected integer")

    def validate(self, value):
        if value is None:
            value = self.default_value()
        if isinstance(value, bool) or type(value) not in (int, integer_type):
            return False
        if self.minimum is not None and value < int(self.minimum):
            return False
        if self.maximum is not None and value > int(self.maximum):
            return False
        return self._validate_custom(value)

    def normalize(self, value):
        if value is None:
            value = self.default_value()
        result = self._coerce(value)
        if self.minimum is not None:
            result = max(int(self.minimum), result)
        if self.maximum is not None:
            result = min(int(self.maximum), result)
        return self._require_custom(result)


class FloatField(Field):
    def __init__(
        self,
        default=0.0,
        minimum=None,
        maximum=None,
        validator=None
    ):
        Field.__init__(self, default=default, validator=validator)
        self.minimum = minimum
        self.maximum = maximum

    def _coerce(self, value):
        if isinstance(value, bool):
            raise FieldValidationError(value, "Expected number")
        try:
            return float(value)
        except Exception:
            raise FieldValidationError(value, "Expected number")

    def validate(self, value):
        if value is None:
            value = self.default_value()
        if isinstance(value, bool):
            return False
        try:
            candidate = float(value)
        except Exception:
            return False
        if self.minimum is not None and candidate < float(self.minimum):
            return False
        if self.maximum is not None and candidate > float(self.maximum):
            return False
        return self._validate_custom(value)

    def normalize(self, value):
        if value is None:
            value = self.default_value()
        result = self._coerce(value)
        if self.minimum is not None:
            result = max(float(self.minimum), result)
        if self.maximum is not None:
            result = min(float(self.maximum), result)
        return self._require_custom(result)


class ChoiceField(Field):
    def __init__(
        self,
        choices,
        default=None,
        case_sensitive=False,
        validator=None
    ):
        self.choices = tuple(choices or ())
        self.case_sensitive = bool(case_sensitive)
        if default is None and self.choices:
            default = self.choices[0]
        Field.__init__(self, default=default, validator=validator)

    def _matching_choice(self, value):
        if self.case_sensitive:
            return value if value in self.choices else None
        candidate = text_type(value if value is not None else "").lower()
        for choice in self.choices:
            if text_type(choice).lower() == candidate:
                return choice
        return None

    def validate(self, value):
        if value is None:
            value = self.default_value()
        return (
            self._matching_choice(value) is not None and
            self._validate_custom(value)
        )

    def normalize(self, value):
        if value is None:
            value = self.default_value()
        match = self._matching_choice(value)
        if match is None:
            raise FieldValidationError(
                value,
                "Expected one of: {0}".format(", ".join(
                    text_type(choice) for choice in self.choices
                ))
            )
        return self._require_custom(match)


class ColorField(Field):
    def __init__(self, default=None, validator=None):
        Field.__init__(
            self,
            default=list(default or [0.25, 0.25, 0.25]),
            validator=validator
        )

    def validate(self, value):
        if value is None:
            value = self.default_value()
        if not isinstance(value, (list, tuple)) or len(value) != 3:
            return False
        for entry in value:
            try:
                entry = float(entry)
            except Exception:
                return False
            if entry < 0.0 or entry > 1.0:
                return False
        return self._validate_custom(value)

    def normalize(self, value):
        if value is None:
            value = self.default_value()
        if not isinstance(value, (list, tuple)) or len(value) != 3:
            raise FieldValidationError(value, "Expected RGB list with 3 values")
        result = []
        for entry in value:
            if isinstance(entry, bool):
                raise FieldValidationError(value, "Expected numeric RGB values")
            try:
                entry = float(entry)
            except Exception:
                raise FieldValidationError(value, "Expected numeric RGB values")
            result.append(max(0.0, min(1.0, entry)))
        return self._require_custom(result)


class PathField(TextField):
    def __init__(self, default="", expand=False, validator=None):
        TextField.__init__(self, default=default, validator=validator)
        self.expand = bool(expand)

    def normalize(self, value):
        value = TextField.normalize(self, value)
        if self.expand and value:
            value = os.path.expanduser(os.path.expandvars(value))
        return value


class ListField(Field):
    def __init__(
        self,
        default=None,
        item_field=None,
        minimum=None,
        maximum=None,
        validator=None
    ):
        Field.__init__(
            self,
            default=list(default or []),
            validator=validator
        )
        self.item_field = item_field
        self.minimum = minimum
        self.maximum = maximum

    def validate(self, value):
        if value is None:
            value = self.default_value()
        if not isinstance(value, (list, tuple)):
            return False
        if self.minimum is not None and len(value) < int(self.minimum):
            return False
        if self.maximum is not None and len(value) > int(self.maximum):
            return False
        if self.item_field is not None:
            for entry in value:
                if not self.item_field.validate(entry):
                    return False
        return self._validate_custom(value)

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
        return self._require_custom(result)


__all__ = [
    "AnyField",
    "BoolField",
    "ChoiceField",
    "ColorField",
    "Field",
    "FieldValidationError",
    "FloatField",
    "IntField",
    "ListField",
    "PathField",
    "TextField",
]
