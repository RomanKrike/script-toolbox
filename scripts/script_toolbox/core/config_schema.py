# -*- coding: utf-8 -*-
from __future__ import print_function

import copy

from ..constants import CONFIG_VERSION


class ConfigSchemaError(RuntimeError):
    pass


class UnsupportedConfigVersionError(ConfigSchemaError):
    pass


class MissingConfigVersionError(UnsupportedConfigVersionError):
    pass


class InvalidConfigVersionError(ConfigSchemaError):
    pass


class UnsupportedOldConfigVersionError(UnsupportedConfigVersionError):
    pass


class FutureConfigVersionError(UnsupportedConfigVersionError):
    pass


def _coerce_version(value):
    try:
        return int(value)
    except Exception:
        raise InvalidConfigVersionError(
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

    # Empty mapping is used internally only to construct a brand-new config.
    if not document:
        return {
            "version": expected_version,
            "sections": [],
        }

    current_version = detect_config_version(document)
    if current_version is None:
        raise MissingConfigVersionError(
            "Script Toolbox configs must declare schema version {0}.".format(
                expected_version
            )
        )

    if current_version < expected_version:
        raise UnsupportedOldConfigVersionError(
            (
                "Unsupported old Script Toolbox config schema {0}; "
                "this build requires schema {1}."
            ).format(current_version, expected_version)
        )

    if current_version > expected_version:
        raise FutureConfigVersionError(
            (
                "Script Toolbox config schema {0} is newer than this build "
                "supports ({1}); downgrade is not attempted."
            ).format(current_version, expected_version)
        )

    return copy.deepcopy(document)


def migrate_document_schema(document, expected_version=CONFIG_VERSION):
    """Validate the current schema; historical migrations are unsupported."""
    return validate_document_schema(
        document,
        expected_version=expected_version
    )


__all__ = [
    "ConfigSchemaError",
    "FutureConfigVersionError",
    "InvalidConfigVersionError",
    "MissingConfigVersionError",
    "UnsupportedConfigVersionError",
    "UnsupportedOldConfigVersionError",
    "detect_config_version",
    "migrate_document_schema",
    "validate_document_schema",
]
