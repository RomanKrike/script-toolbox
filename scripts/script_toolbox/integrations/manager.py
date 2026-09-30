# -*- coding: utf-8 -*-
from __future__ import print_function

from ..core.logging_utils import get_logger
from .config import get_integration_settings
from .blender import BlenderAdapter
from .houdini import HoudiniAdapter
from .max import MaxAdapter
from .maya import MayaAdapter
from .nuke import NukeAdapter


_LOGGER = get_logger()


class DccIntegrationManager(object):
    """Facade used by Settings UI; adapters own all DCC-specific details."""

    def __init__(self, adapters=None):
        if adapters is None:
            adapters = [
                MayaAdapter(),
                HoudiniAdapter(),
                NukeAdapter(),
                BlenderAdapter(),
                MaxAdapter(),
            ]
        self._adapters = {}
        for adapter in adapters:
            self._adapters[adapter.key] = adapter

    def adapters(self):
        order = ("maya", "houdini", "nuke", "blender", "3dsmax")
        result = []
        for key in order:
            adapter = self._adapters.get(key)
            if adapter is not None:
                result.append(adapter)
        for key, adapter in self._adapters.items():
            if key not in order:
                result.append(adapter)
        return result

    def adapter(self, dcc):
        return self._adapters.get(dcc)

    def scan(self):
        result = {}
        for adapter in self.adapters():
            try:
                installations = adapter.get_installations()
            except Exception:
                _LOGGER.exception(
                    "[DCC] Detection failed for %s",
                    adapter.display_name
                )
                installations = []
            result[adapter.key] = installations
            for installation in installations:
                _LOGGER.info(
                    "[DCC] %s %s detected",
                    adapter.display_name,
                    installation.version
                )
        return result

    def scan_details(self):
        """Filesystem-only snapshot; building widgets never reopens paths."""
        installations = self.scan()
        roots = {}
        for adapter in self.adapters():
            callback = getattr(adapter, "profile_roots", None)
            roots[adapter.key] = callback() if callable(callback) else []
            for target in installations.get(adapter.key, []):
                target.scanned_status = self.status(target)
                target.scanned_options = adapter.normalize_options(
                    get_integration_settings(target.dcc, target.version,
                        profile_id=target.profile_id) or {})
        return {"installations": installations, "roots": roots}

    def files_operation(self, operation, installation, options=None):
        adapter = self.adapter(installation.dcc)
        callback = getattr(adapter, operation)
        if operation == "install":
            return callback(installation, options=options, sync_live=False)
        return callback(installation, sync_live=False)

    def sync_live(self, installation):
        adapter = self.adapter(installation.dcc)
        callback = getattr(adapter, "_sync_live_" + installation.dcc, None)
        return callback(installation) if callable(callback) else False

    def profile_roots(self, dcc):
        adapter = self.adapter(dcc)
        if adapter is None:
            raise KeyError(dcc)
        callback = getattr(adapter, "profile_roots", None)
        if not callable(callback):
            return []
        return callback()

    def add_profile_root(self, dcc, profile_path, label=""):
        adapter = self.adapter(dcc)
        if adapter is None:
            raise KeyError(dcc)
        callback = getattr(adapter, "add_profile_root", None)
        if not callable(callback):
            raise RuntimeError(
                "Custom profile roots are not supported for {0}.".format(
                    adapter.display_name
                )
            )
        return callback(profile_path, label=label)

    def remove_profile_root(self, dcc, profile_id):
        adapter = self.adapter(dcc)
        if adapter is None:
            raise KeyError(dcc)
        callback = getattr(adapter, "remove_profile_root", None)
        if not callable(callback):
            raise RuntimeError(
                "Custom profile roots are not supported for {0}.".format(
                    adapter.display_name
                )
            )
        return callback(profile_id)

    def status(self, installation):
        adapter = self.adapter(installation.dcc)
        if adapter is None:
            raise KeyError(installation.dcc)
        result = adapter.status(installation)
        installation.integration_status = result.state
        return result

    def install(self, installation, options=None):
        adapter = self.adapter(installation.dcc)
        if adapter is None:
            raise KeyError(installation.dcc)
        if not adapter.integration_available:
            raise RuntimeError(
                "Integration is not implemented for {0}.".format(
                    adapter.display_name
                )
            )
        return adapter.install(installation, options=options)

    def repair(self, installation):
        adapter = self.adapter(installation.dcc)
        if adapter is None:
            raise KeyError(installation.dcc)
        return adapter.repair(installation)

    def uninstall(self, installation):
        adapter = self.adapter(installation.dcc)
        if adapter is None:
            raise KeyError(installation.dcc)
        return adapter.uninstall(installation)

    def install_all(self, dcc, options=None):
        adapter = self.adapter(dcc)
        if adapter is None:
            raise KeyError(dcc)
        results = []
        for installation in adapter.get_installations():
            try:
                status = adapter.install(
                    installation,
                    options=options
                )
                results.append((installation, status, None))
            except Exception as exc:
                results.append((installation, None, exc))
        return results


__all__ = ["DccIntegrationManager"]
