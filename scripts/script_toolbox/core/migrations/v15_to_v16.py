# -*- coding: utf-8 -*-
from __future__ import print_function

import copy


SOURCE_VERSION = 15
TARGET_VERSION = 16


def migrate(document):
    """Migrate schema 15 to schema 16.

    Schema 16 added State Buttons, On Change scripts, advanced Row layout and
    Field 2.0 settings. Those additions are backward-compatible defaults, so
    the versioned migration preserves the existing document and lets current
    model normalization populate the new optional fields.
    """
    migrated = copy.deepcopy(
        document
    )
    migrated["version"] = TARGET_VERSION
    return migrated


__all__ = [
    "SOURCE_VERSION",
    "TARGET_VERSION",
    "migrate",
]
