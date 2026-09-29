# -*- coding: utf-8 -*-
from __future__ import print_function

import json
import os
import shutil
import sys

from ..constants import PLUGIN_VERSION
from ..core.logging_utils import get_logger
from .base import IntegrationStatus
from .base import STATUS_BROKEN
from .base import STATUS_INSTALLED
from .base import STATUS_NOT_INSTALLED
from .base import STATUS_PARTIAL
from .base import STATUS_UPDATE_REQUIRED
from .config import get_integration_settings
from .config import remove_integration_settings
from .config import set_integration_settings
from .discovery import distribution_root
from .discovery import parse_version
from .discovery import windows_documents_dir
from .generic import DetectionOnlyAdapter
from .managed_files import atomic_write
from .managed_files import read_text


_LOGGER = get_logger()
_PACKAGE_FILENAME = "script_toolbox.json"
_PLUGIN_DIRNAME = "script_toolbox_integration"
_MANIFEST_FILENAME = "manifest.json"
_SHELF_FILENAME = "ScriptToolbox.shelf"
_PYTHON_LIB_DIRS = (
    "python2.7libs",
    "python3.7libs",
    "python3.8libs",
    "python3.9libs",
    "python3.10libs",
    "python3.11libs",
    "python3.12libs",
    "python3.13libs",
)


class HoudiniIntegrationError(RuntimeError):
    pass


def _pref_version(version):
    parts = str(version or "").split(".")
    if len(parts) >= 2:
        return "{0}.{1}".format(parts[0], parts[1])
    return str(version or "")


class HoudiniAdapter(DetectionOnlyAdapter):
    key = "houdini"
    display_name = "SideFX Houdini"
    environment_variable = "HFS"
    integration_available = True
    supported = True

    def __init__(
        self,
        distribution_path=None,
        program_files=None,
        user_root=None,
        config_path=None
    ):
        self.distribution_path = os.path.normpath(
            distribution_path or distribution_root()
        )
        self.program_files = os.path.normpath(
            program_files or
            os.environ.get("ProgramFiles") or
            r"C:\Program Files"
        )
        self.user_root = (
            os.path.normpath(user_root)
            if user_root else None
        )
        self.config_path = config_path

    def install_patterns(self):
        if os.name == "nt":
            return [
                os.path.join(
                    self.program_files,
                    "Side Effects Software",
                    "Houdini *"
                )
            ]
        if sys.platform == "darwin":
            return ["/Applications/Houdini/Houdini*.app"]
        return ["/opt/hfs*"]

    def user_config_path(self, version):
        pref_version = _pref_version(version)
        if self.user_root:
            return os.path.join(
                self.user_root,
                "houdini{0}".format(pref_version)
            )
        if os.name == "nt":
            return os.path.join(
                windows_documents_dir(),
                "houdini{0}".format(pref_version)
            )
        return os.path.expanduser(
            "~/houdini{0}".format(pref_version)
        )

    def option_definitions(self):
        return (
            ("shelf", "Add Houdini Shelf", True),
            ("auto_open", "Open on startup", False),
        )

    def component_status_text(self, status, options=None):
        options = self.normalize_options(options)
        return "    ".join([
            "Package: {0}".format(
                "OK" if status.loader else "Missing"
            ),
            "Shelf: {0}".format(
                (
                    "OK" if status.shelf else "Missing"
                ) if options["shelf"] else "Disabled"
            ),
            "Startup: {0}".format(
                "Enabled" if status.auto_open else "Ready"
            ),
        ])

    @staticmethod
    def _package_path(installation):
        return os.path.join(
            installation.user_config_path,
            "packages",
            _PACKAGE_FILENAME
        )

    @staticmethod
    def _plugin_root(installation):
        return os.path.join(
            installation.user_config_path,
            _PLUGIN_DIRNAME
        )

    def _manifest_path(self, installation):
        return os.path.join(
            self._plugin_root(installation),
            _MANIFEST_FILENAME
        )

    def _shelf_path(self, installation):
        return os.path.join(
            self._plugin_root(installation),
            "toolbar",
            _SHELF_FILENAME
        )

    def _startup_paths(self, installation):
        root = self._plugin_root(installation)
        return [
            os.path.join(root, folder, "uiready.py")
            for folder in _PYTHON_LIB_DIRS
        ]

    def _package_payload(self, installation):
        root = self.distribution_path.replace("\\", "/")
        scripts = os.path.join(
            self.distribution_path,
            "scripts"
        ).replace("\\", "/")
        plugin_root = self._plugin_root(
            installation
        ).replace("\\", "/")
        return {
            "enable": True,
            "env": [
                {
                    "SCRIPT_TOOLBOX_ROOT": root,
                },
                {
                    "var": "PYTHONPATH",
                    "value": scripts,
                    "method": "prepend",
                },
            ],
            "path": plugin_root,
        }

    def _package_content(self, installation):
        return json.dumps(
            self._package_payload(installation),
            indent=4,
            sort_keys=True
        ) + "\n"

    def _manifest_content(self, installation):
        return json.dumps(
            {
                "plugin_version": PLUGIN_VERSION,
                "distribution_path": self.distribution_path.replace(
                    "\\",
                    "/"
                ),
                "integration": "houdini",
            },
            indent=2,
            sort_keys=True
        ) + "\n"

    @staticmethod
    def _uiready_content():
        return (
            "# ScriptToolbox managed Houdini integration\n"
            "try:\n"
            "    import script_toolbox.houdini_integration as _stb_houdini_integration\n"
            "    _stb_houdini_integration.apply_current_integration()\n"
            "except Exception:\n"
            "    import traceback\n"
            "    traceback.print_exc()\n"
        )

    @staticmethod
    def _shelf_content():
        return """<?xml version="1.0" encoding="UTF-8"?>
<shelfDocument>
  <toolshelf name="script_toolbox" label="Script Toolbox">
    <memberTool name="script_toolbox_open"/>
  </toolshelf>
  <tool name="script_toolbox_open" label="Script Toolbox" icon="PYTHON">
    <helpText><![CDATA[Open Script Toolbox]]></helpText>
    <script scriptType="python"><![CDATA[import script_toolbox
script_toolbox.show()]]></script>
  </tool>
</shelfDocument>
"""

    @staticmethod
    def _file_state(path, expected):
        if not os.path.isfile(path):
            return "missing"
        try:
            current = read_text(path)
        except Exception:
            return "broken"
        if current != expected:
            return "stale"
        return "ok"

    def _loader_states(self, installation):
        states = {
            "package": self._file_state(
                self._package_path(installation),
                self._package_content(installation)
            ),
            "manifest": self._file_state(
                self._manifest_path(installation),
                self._manifest_content(installation)
            ),
        }
        startup_expected = self._uiready_content()
        startup_states = [
            self._file_state(path, startup_expected)
            for path in self._startup_paths(installation)
        ]
        states["startup"] = (
            "ok"
            if startup_states and all(
                value == "ok" for value in startup_states
            )
            else (
                "stale"
                if any(value == "stale" for value in startup_states)
                else "missing"
            )
        )
        return states

    def status(self, installation):
        settings = get_integration_settings(
            self.key,
            installation.version,
            path=self.config_path,
            profile_id=installation.profile_id
        )
        states = self._loader_states(installation)
        loader_ok = all(
            value == "ok"
            for value in states.values()
        )

        if settings is None:
            return IntegrationStatus(
                STATUS_NOT_INSTALLED,
                loader=loader_ok
            )

        if any(
            value == "broken"
            for value in states.values()
        ):
            return IntegrationStatus(
                STATUS_BROKEN,
                loader=False,
                message="Cannot read the managed Houdini integration files."
            )

        if any(
            value == "stale"
            for value in states.values()
        ):
            return IntegrationStatus(
                STATUS_UPDATE_REQUIRED,
                loader=True,
                message=(
                    "The Houdini package points to an older Script Toolbox "
                    "location or version."
                )
            )

        if not loader_ok:
            return IntegrationStatus(
                STATUS_BROKEN,
                loader=False,
                message="The Script Toolbox Houdini package/startup files are missing."
            )

        desired = self.normalize_options(settings)
        shelf_state = self._file_state(
            self._shelf_path(installation),
            self._shelf_content()
        )
        shelf_present = shelf_state == "ok"

        if desired["shelf"] and shelf_state == "stale":
            return IntegrationStatus(
                STATUS_UPDATE_REQUIRED,
                loader=True,
                shelf=False,
                message="The managed Houdini Shelf definition is out of date."
            )

        if desired["shelf"] != shelf_present:
            return IntegrationStatus(
                STATUS_PARTIAL,
                loader=True,
                shelf=shelf_present,
                auto_open=desired["auto_open"],
                message="Mismatch: Houdini Shelf."
            )

        return IntegrationStatus(
            STATUS_INSTALLED,
            loader=True,
            shelf=desired["shelf"],
            auto_open=desired["auto_open"]
        )

    def _write_loader(self, installation, options):
        atomic_write(
            self._package_path(installation),
            self._package_content(installation)
        )
        atomic_write(
            self._manifest_path(installation),
            self._manifest_content(installation)
        )
        startup = self._uiready_content()
        for path in self._startup_paths(installation):
            atomic_write(path, startup)

        shelf_path = self._shelf_path(installation)
        if options["shelf"]:
            atomic_write(
                shelf_path,
                self._shelf_content()
            )
        elif os.path.isfile(shelf_path):
            try:
                content = read_text(shelf_path)
            except Exception:
                content = ""
            if "script_toolbox_open" in content:
                os.remove(shelf_path)

    def _same_user_config_still_configured(self, installation):
        target_path = os.path.normcase(
            os.path.normpath(
                installation.user_config_path
            )
        )
        for item in self.get_installations():
            if item.key == installation.key:
                continue
            if os.path.normcase(
                os.path.normpath(item.user_config_path)
            ) != target_path:
                continue
            settings = get_integration_settings(
                self.key,
                item.version,
                path=self.config_path,
                profile_id=item.profile_id
            )
            if settings is not None:
                return True
        return False

    def _sync_live_houdini(self, installation):
        try:
            import hou
            current = parse_version(
                hou.applicationVersionString()
            )
            if current != installation.version:
                return False
            from .. import houdini_integration
            houdini_integration.apply_current_integration()
            return True
        except Exception:
            _LOGGER.debug(
                "[DCC] Live Houdini UI sync skipped.",
                exc_info=True
            )
            return False

    def install(self, installation, options=None):
        options = self.normalize_options(options)
        self._write_loader(
            installation,
            options
        )

        stored = dict(options)
        stored.update({
            "install_path": installation.install_path,
            "user_config_path": installation.user_config_path,
            "plugin_version": PLUGIN_VERSION,
        })
        set_integration_settings(
            self.key,
            installation.version,
            stored,
            path=self.config_path,
            profile_id=installation.profile_id
        )
        self._sync_live_houdini(installation)

        result = self.status(installation)
        if result.state != STATUS_INSTALLED:
            raise HoudiniIntegrationError(
                result.message or
                "Houdini integration verification failed: {0}".format(
                    result.state
                )
            )
        return result

    def repair(self, installation):
        settings = get_integration_settings(
            self.key,
            installation.version,
            path=self.config_path,
            profile_id=installation.profile_id
        )
        if settings is None:
            settings = self.normalize_options()
        return self.install(
            installation,
            settings
        )

    def uninstall(self, installation):
        remove_integration_settings(
            self.key,
            installation.version,
            path=self.config_path,
            profile_id=installation.profile_id
        )
        self._sync_live_houdini(installation)

        if not self._same_user_config_still_configured(
            installation
        ):
            package_path = self._package_path(
                installation
            )
            if os.path.isfile(package_path):
                try:
                    content = read_text(package_path)
                except Exception:
                    content = ""
                if "SCRIPT_TOOLBOX_ROOT" in content:
                    os.remove(package_path)

            plugin_root = self._plugin_root(
                installation
            )
            manifest_path = self._manifest_path(
                installation
            )
            if os.path.isfile(manifest_path):
                try:
                    content = read_text(manifest_path)
                except Exception:
                    content = ""
                if '"integration": "houdini"' in content:
                    shutil.rmtree(
                        plugin_root,
                        ignore_errors=True
                    )

        return self.status(installation)


__all__ = [
    "HoudiniAdapter",
    "HoudiniIntegrationError",
]
