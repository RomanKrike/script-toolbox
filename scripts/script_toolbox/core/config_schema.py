# -*- coding: utf-8 -*-
from __future__ import print_function

import copy

from ..constants import CONFIG_VERSION


class ConfigSchemaError(RuntimeError):
    pass


class UnsupportedConfigVersionError(ConfigSchemaError):
    """Backward-compatible base for unsupported version failures."""
    pass


class MissingConfigVersionError(UnsupportedConfigVersionError):
    pass


class InvalidConfigVersionError(ConfigSchemaError):
    pass


class UnsupportedOldConfigVersionError(UnsupportedConfigVersionError):
    pass


class MissingMigrationStepError(UnsupportedConfigVersionError):
    pass


class FutureConfigVersionError(UnsupportedConfigVersionError):
    pass


class InvalidMigrationResultError(ConfigSchemaError):
    pass


class MigrationValidationError(ConfigSchemaError):
    pass


# Production migrations are registered by source schema version. The current
# schema remains 20 until an actual storage change requires 20 -> 21.
MIGRATIONS = {}


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

    # Empty mapping is used internally to construct a brand-new config.
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
                "this build requires schema {1} or a registered migration."
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


def migrate_document_schema(
    document,
    expected_version=CONFIG_VERSION,
    migrations=None,
    validator=None
):
    """Apply deterministic N -> N+1 migrations, then current validation."""
    expected_version = _coerce_version(expected_version)
    registry = MIGRATIONS if migrations is None else migrations
    validate = validator or validate_document_schema

    if not isinstance(document, dict) or not document:
        return validate(
            copy.deepcopy(document),
            expected_version=expected_version
        )

    source_version = detect_config_version(document)
    if source_version is None:
        raise MissingConfigVersionError(
            "Script Toolbox config is missing its schema version."
        )

    if source_version > expected_version:
        raise FutureConfigVersionError(
            (
                "Script Toolbox config schema {0} is newer than this build "
                "supports ({1}); downgrade is not attempted."
            ).format(source_version, expected_version)
        )

    if source_version == expected_version:
        return validate(
            copy.deepcopy(document),
            expected_version=expected_version
        )

    candidate = copy.deepcopy(document)
    current_version = source_version
    migrated = False

    while current_version < expected_version:
        migration = registry.get(current_version)
        if migration is None:
            if not migrated:
                raise UnsupportedOldConfigVersionError(
                    (
                        "Unsupported old Script Toolbox config schema {0}; "
                        "no migration path to schema {1} is registered."
                    ).format(source_version, expected_version)
                )
            raise MissingMigrationStepError(
                "Missing Script Toolbox config migration {0} -> {1}.".format(
                    current_version,
                    current_version + 1
                )
            )

        expected_next = current_version + 1
        step_input = copy.deepcopy(candidate)
        step_output = migration(step_input)

        if not isinstance(step_output, dict):
            raise InvalidMigrationResultError(
                (
                    "Config migration {0} -> {1} returned {2}, expected dict."
                ).format(
                    current_version,
                    expected_next,
                    type(step_output).__name__
                )
            )

        returned_version = detect_config_version(step_output)
        if returned_version != expected_next:
            raise InvalidMigrationResultError(
                (
                    "Config migration {0} -> {1} returned schema {2!r}; "
                    "each migration must advance exactly one version."
                ).format(
                    current_version,
                    expected_next,
                    returned_version
                )
            )

        candidate = copy.deepcopy(step_output)
        current_version = returned_version
        migrated = True

    try:
        return validate(
            candidate,
            expected_version=expected_version
        )
    except ConfigSchemaError as exc:
        raise MigrationValidationError(
            "Migrated Script Toolbox config failed current schema validation: {0}".format(
                exc
            )
        )


__all__ = [
    "ConfigSchemaError",
    "FutureConfigVersionError",
    "InvalidConfigVersionError",
    "InvalidMigrationResultError",
    "MIGRATIONS",
    "MigrationValidationError",
    "MissingConfigVersionError",
    "MissingMigrationStepError",
    "UnsupportedConfigVersionError",
    "UnsupportedOldConfigVersionError",
    "detect_config_version",
    "migrate_document_schema",
    "validate_document_schema",
]
