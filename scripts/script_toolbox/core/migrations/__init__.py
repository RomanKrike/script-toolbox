# -*- coding: utf-8 -*-
from __future__ import print_function

import copy

from ...constants import CONFIG_VERSION
from .v15_to_v16 import migrate as migrate_v15_to_v16
from .v16_to_v17 import migrate as migrate_v16_to_v17


# Schema 15 is the compatibility baseline used by the first modular release.
# Configs without an explicit version are treated as legacy schema 15 because
# the pre-migration loader already accepted that document shape.
LEGACY_CONFIG_VERSION = 15


class ConfigMigrationError(RuntimeError):
    pass


class UnsupportedConfigVersionError(ConfigMigrationError):
    pass


_MIGRATIONS = {
    15: (16, migrate_v15_to_v16),
    16: (17, migrate_v16_to_v17),
}


def _coerce_version(value):
    if value is None or value == "":
        return LEGACY_CONFIG_VERSION

    try:
        return int(value)
    except Exception:
        raise ConfigMigrationError(
            "Invalid Script Toolbox config version: {0!r}.".format(
                value
            )
        )


def detect_config_version(document):
    if not isinstance(document, dict):
        return None

    return _coerce_version(
        document.get("version")
    )


def migrate_document(
    document,
    target_version=CONFIG_VERSION
):
    """Return a migrated copy of ``document`` for ``target_version``.

    Migration is deliberately separate from model normalization. Migration
    handles version-to-version schema semantics; normalization applies current
    defaults and defensive value cleanup after migration is complete.
    """
    if not isinstance(document, dict):
        return copy.deepcopy(document)

    target_version = _coerce_version(
        target_version
    )
    current_version = detect_config_version(
        document
    )

    if current_version > target_version:
        raise UnsupportedConfigVersionError(
            (
                "Script Toolbox config schema {0} is newer than the "
                "supported schema {1}. Update Script Toolbox before opening "
                "or saving this configuration."
            ).format(
                current_version,
                target_version
            )
        )

    migrated = copy.deepcopy(
        document
    )

    while current_version < target_version:
        step = _MIGRATIONS.get(
            current_version
        )

        if step is None:
            raise ConfigMigrationError(
                "No Script Toolbox config migration path from schema {0} "
                "to schema {1}.".format(
                    current_version,
                    target_version
                )
            )

        next_version, migration = step

        if next_version <= current_version:
            raise ConfigMigrationError(
                "Invalid Script Toolbox migration registration for schema "
                "{0}.".format(
                    current_version
                )
            )

        migrated = migration(
            migrated
        )

        if not isinstance(migrated, dict):
            raise ConfigMigrationError(
                "Migration from schema {0} returned an invalid document.".format(
                    current_version
                )
            )

        result_version = detect_config_version(
            migrated
        )

        if result_version != next_version:
            raise ConfigMigrationError(
                "Migration from schema {0} must produce schema {1}, got "
                "schema {2}.".format(
                    current_version,
                    next_version,
                    result_version
                )
            )

        current_version = next_version

    return migrated


__all__ = [
    "ConfigMigrationError",
    "LEGACY_CONFIG_VERSION",
    "UnsupportedConfigVersionError",
    "detect_config_version",
    "migrate_document",
]
