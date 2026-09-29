# -*- coding: utf-8 -*-
from __future__ import print_function

import os

from .base import DccAdapter
from .base import DccInstallation
from .discovery import existing_directories
from .discovery import parse_version
from .discovery import version_sort_key


class DetectionOnlyAdapter(DccAdapter):
    """Shared detection scaffolding for DCCs whose installer is not implemented."""

    integration_available = False
    supported = False
    environment_variable = ""

    def install_patterns(self):
        return []

    def user_config_path(self, version):
        return ""

    def get_installations(self):
        by_version = {}

        if self.environment_variable:
            path = os.environ.get(self.environment_variable)
            if path and os.path.isdir(path):
                version = parse_version(path)
                if version:
                    by_version[version] = os.path.normpath(path)

        for path in existing_directories(self.install_patterns()):
            version = parse_version(path)
            if version:
                by_version.setdefault(version, path)

        result = []
        for version in sorted(by_version.keys(), key=version_sort_key):
            installation = DccInstallation(
                self.key,
                self.display_name,
                version,
                install_path=by_version[version],
                user_config_path=self.user_config_path(version),
                integration_available=False,
                supported=True
            )
            installation.integration_status = self.status(installation).state
            result.append(installation)
        return result


__all__ = [
    "DetectionOnlyAdapter",
]
