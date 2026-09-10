# -*- coding: utf-8 -*-
from __future__ import print_function

import copy

from ..constants import CONFIG_VERSION


class ConfigSchemaError(RuntimeError):
    pass


class UnsupportedConfigVersionError(ConfigSchemaError):
    pass


def _coerce_version(value):
    try:
        return int(value)
    except Exception:
        raise ConfigSchemaError(
            "Invalid Script Toolbox config version: {0!r}.".format(value)
        )


def detect_config_version(document):
    if not isinstance(document, dict):
        return None
    if "version" not in document:
        return None
    return _coerce_version(document.get("version"))


def validate_document_schema(document, expected_version=CONFIG_VERSION):
    """Validate and copy a document using the single current schema."""
    if not isinstance(document, dict):
        return copy.deepcopy(document)

    expected_version = _coerce_version(expected_version)

    # Empty mapping is used internally to construct a brand-new config.
    if not document:
        return {
            "version": expected_version,
            "sections": [],
        }

    current_version = detect_config_version(document)
    if current_version is None:
        raise UnsupportedConfigVersionError(
            "Script Toolbox configs must declare schema version {0}.".format(
                expected_version
            )
        )

    if current_version != expected_version:
        raise UnsupportedConfigVersionError(
            (
                "Unsupported Script Toolbox config schema {0}; "
                "this build accepts schema {1} only."
            ).format(current_version, expected_version)
        )

    return copy.deepcopy(document)


__all__ = [
    "ConfigSchemaError",
    "UnsupportedConfigVersionError",
    "detect_config_version",
    "validate_document_schema",
]
