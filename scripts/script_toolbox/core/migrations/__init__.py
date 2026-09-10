# -*- coding: utf-8 -*-
from __future__ import print_function

import copy

from ...constants import CONFIG_VERSION


class ConfigMigrationError(RuntimeError):
    pass


class UnsupportedConfigVersionError(ConfigMigrationError):
    pass


def _coerce_version(value):
    try:
        return int(value)
    except Exception:
        raise ConfigMigrationError(
            "Invalid Script Toolbox config version: {0!r}.".format(value)
        )


def detect_config_version(document):
    if not isinstance(document, dict):
        return None
    if "version" not in document:
        return None
    return _coerce_version(document.get("version"))


def migrate_document(document, target_version=CONFIG_VERSION):
    """Validate and copy a document using the single current schema.

    Script Toolbox is still in active development, so historical config
    schemas are intentionally unsupported. The function name remains the
    config-layer entry point, but no migration path exists.
    """
    if not isinstance(document, dict):
        return copy.deepcopy(document)

    target_version = _coerce_version(target_version)

    # An empty mapping is the internal representation of a brand-new config.
    if not document:
        return {
            "version": target_version,
            "sections": [],
        }

    current_version = detect_config_version(document)
    if current_version is None:
        raise UnsupportedConfigVersionError(
            "Script Toolbox configs must declare schema version {0}.".format(
                target_version
            )
        )

    if current_version != target_version:
        raise UnsupportedConfigVersionError(
            (
                "Unsupported Script Toolbox config schema {0}; "
                "this build accepts schema {1} only."
            ).format(current_version, target_version)
        )

    return copy.deepcopy(document)


__all__ = [
    "ConfigMigrationError",
    "UnsupportedConfigVersionError",
    "detect_config_version",
    "migrate_document",
]
