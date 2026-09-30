# -*- coding: utf-8 -*-
from __future__ import print_function

import json
import os
import shutil
import sys

from ..constants import PLUGIN_VERSION
from ..core.logging_utils import get_logger
from ..pycompat import text_type
from .base import DccInstallation
from .base import IntegrationStatus
from .base import STATUS_BROKEN
from .base import STATUS_INSTALLED
from .base import STATUS_NOT_INSTALLED
from .base import STATUS_PARTIAL
from .base import STATUS_UPDATE_REQUIRED
from .config import DEFAULT_PROFILE_ID
from .config import add_profile_root
from .config import get_integration_settings
from .config import get_profile_roots
from .config import profile_has_integration_settings
from .config import remove_integration_settings
from .config import remove_profile_root
from .config import set_integration_settings
from .config import user_config_has_integration_settings
from .discovery import distribution_root
from .discovery import parse_version
from .discovery import version_sort_key
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
    parts = text_type(version or "").split(".")
    if len(parts) >= 2:
        return "{0}.{1}".format(parts[0], parts[1])
    return text_type(version or "")


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

    def _default_profile_root(self):
        if self.user_root:
            return self.user_root
        if os.name == "nt":
            return windows_documents_dir()
        return os.path.expanduser("~")

    def user_config_path(self, version):
        return os.path.join(
            self._default_profile_root(),
            "houdini{0}".format(
                _pref_version(version)
            )
        )

    @staticmethod
    def _same_path(first, second):
        if not first or not second:
            return False
        return os.path.normcase(
            os.path.normpath(first)
        ) == os.path.normcase(
            os.path.normpath(second)
        )

    def profile_roots(self):
        roots = [{
            "id": DEFAULT_PROFILE_ID,
            "label": "Default",
            "path": self._default_profile_root(),
            "source": "default",
            "removable": False,
        }]
        for record in get_profile_roots(
            self.key,
            path=self.config_path
        ):
            item = dict(record)
            item["source"] = "custom"
            item["removable"] = True
            roots.append(item)
        return roots

    def add_profile_root(self, profile_path, label=""):
        normalized = os.path.normpath(
            os.path.expanduser(
                text_type(profile_path or "").strip()
            )
        )
        if not normalized:
            raise HoudiniIntegrationError(
                "Profile path is empty."
            )
        if self._same_path(
            normalized,
            self._default_profile_root()
        ):
            raise HoudiniIntegrationError(
                "This path is already the default Houdini profile root."
            )
        return add_profile_root(
            self.key,
            normalized,
            label=label,
            path=self.config_path
        )

    def remove_profile_root(self, profile_id):
        profile_id = text_type(
            profile_id or ""
        ).strip()
        if not profile_id or profile_id == DEFAULT_PROFILE_ID:
            raise HoudiniIntegrationError(
                "The default Houdini profile root cannot be removed."
            )

        if profile_has_integration_settings(
            self.key,
            profile_id,
            path=self.config_path
        ):
            raise HoudiniIntegrationError(
                "Uninstall Script Toolbox from all Houdini targets in this "
                "profile path before removing it."
            )

        return remove_profile_root(
            self.key,
            profile_id,
            path=self.config_path
        )

    @staticmethod
    def _profile_targets_for_root(
        root_path,
        detected_versions
    ):
        root_path = os.path.normpath(
            os.path.expanduser(
                text_type(root_path or "").strip()
            )
        )
        if not root_path or not os.path.isdir(root_path):
            return []

        detected_versions = list(
            detected_versions or []
        )
        base_name = os.path.basename(
            root_path.rstrip("\\/")
        )
        base_lower = base_name.lower()
        base_version = parse_version(base_name)

        def _versions_for_pref(pref_version):
            matches = [
                version
                for version in detected_versions
                if _pref_version(version) == pref_version
            ]
            return matches or [pref_version]

        if (
            base_lower.startswith("houdini") and
            base_version
        ):
            return [
                (version, root_path)
                for version in _versions_for_pref(
                    _pref_version(base_version)
                )
            ]

        children = []
        try:
            names = os.listdir(root_path)
        except OSError:
            names = []

        for name in names:
            full_path = os.path.join(
                root_path,
                name
            )
            if not os.path.isdir(full_path):
                continue
            if not text_type(name).lower().startswith(
                "houdini"
            ):
                continue
            version = parse_version(name)
            if not version:
                continue
            pref_version = _pref_version(version)
            for detected in _versions_for_pref(
                pref_version
            ):
                children.append(
                    (detected, full_path)
                )

        if children:
            return children

        return [
            (version, root_path)
            for version in detected_versions
        ]

    def get_installations(self):
        install_paths = dict(
            self.detected_install_paths()
        )
        versions = sorted(
            install_paths.keys(),
            key=version_sort_key
        )
        installations = []
        seen = set()

        for version in versions:
            user_config = os.path.normpath(
                self.user_config_path(version)
            )
            seen.add((
                text_type(version),
                os.path.normcase(user_config)
            ))
            target = DccInstallation(
                self.key,
                self.display_name,
                version,
                install_path=install_paths.get(
                    version,
                    ""
                ),
                user_config_path=user_config,
                integration_available=True,
                supported=True,
                profile_id=DEFAULT_PROFILE_ID,
                profile_label="Default",
                profile_root=self._default_profile_root(),
                profile_source="default"
            )
            target.integration_status = self.status(
                target
            ).state
            installations.append(target)

        for record in get_profile_roots(
            self.key,
            path=self.config_path
        ):
            targets = self._profile_targets_for_root(
                record.get("path"),
                versions
            )
            for version, user_config in targets:
                user_config = os.path.normpath(
                    user_config
                )
                dedupe = (
                    text_type(version),
                    os.path.normcase(user_config)
                )
                if dedupe in seen:
                    continue
                seen.add(dedupe)
                target = DccInstallation(
                    self.key,
                    self.display_name,
                    version,
                    install_path=install_paths.get(
                        version,
                        ""
                    ),
                    user_config_path=user_config,
                    integration_available=True,
                    supported=True,
                    profile_id=record["id"],
                    profile_label=(
                        record.get("label") or
                        "Custom"
                    ),
                    profile_root=(
                        record.get("path") or
                        ""
                    ),
                    profile_source="custom"
                )
                target.integration_status = self.status(
                    target
                ).state
                installations.append(target)

        installations.sort(
            key=lambda item: (
                version_sort_key(item.version),
                (
                    0
                    if item.profile_id == DEFAULT_PROFILE_ID
                    else 1
                ),
                item.profile_label.lower()
            )
        )
        return installations

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
            os.path.join(
                root,
                folder,
                "uiready.py"
            )
            for folder in _PYTHON_LIB_DIRS
        ]

    def _package_payload(self, installation):
        root = self.distribution_path.replace(
            "\\",
            "/"
        )
        scripts = os.path.join(
            self.distribution_path,
            "scripts"
        ).replace(
            "\\",
            "/"
        )
        plugin_root = self._plugin_root(
            installation
        ).replace(
            "\\",
            "/"
        )
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
            self._package_payload(
                installation
            ),
            indent=4,
            sort_keys=True
        ) + "\n"

    def _manifest_content(self, installation):
        return json.dumps(
            {
                "plugin_version": PLUGIN_VERSION,
                "distribution_path": (
                    self.distribution_path.replace(
                        "\\",
                        "/"
                    )
                ),
                "integration": "houdini",
                "profile_id": installation.profile_id,
            },
            indent=2,
            sort_keys=True
        ) + "\n"

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

    def _uiready_content(self, installation):
        return "".join([
            "# ScriptToolbox managed Houdini integration\n",
            "try:\n",
            (
                "    import script_toolbox.houdini_integration "
                "as _stb_houdini_integration\n"
            ),
            (
                "    _stb_houdini_integration.apply_current_integration("
                "profile_id={0!r})\n"
            ).format(
                installation.profile_id
            ),
            "except Exception:\n",
            "    import traceback\n",
            "    traceback.print_exc()\n",
        ])

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
        startup_expected = self._uiready_content(
            installation
        )
        startup_states = [
            self._file_state(
                path,
                startup_expected
            )
            for path in self._startup_paths(
                installation
            )
        ]
        states["startup"] = (
            "ok"
            if startup_states and all(
                value == "ok"
                for value in startup_states
            )
            else (
                "stale"
                if any(
                    value == "stale"
                    for value in startup_states
                )
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
        states = self._loader_states(
            installation
        )
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
                message=(
                    "Cannot read the managed Houdini "
                    "integration files."
                )
            )

        if any(
            value == "stale"
            for value in states.values()
        ):
            return IntegrationStatus(
                STATUS_UPDATE_REQUIRED,
                loader=True,
                message=(
                    "The Houdini package points to an older "
                    "Script Toolbox location, version, or profile."
                )
            )

        if not loader_ok:
            return IntegrationStatus(
                STATUS_BROKEN,
                loader=False,
                message=(
                    "The Script Toolbox Houdini package/startup "
                    "files are missing."
                )
            )

        desired = self.normalize_options(
            settings
        )
        shelf_state = self._file_state(
            self._shelf_path(installation),
            self._shelf_content()
        )
        shelf_present = shelf_state == "ok"

        if (
            desired["shelf"] and
            shelf_state == "stale"
        ):
            return IntegrationStatus(
                STATUS_UPDATE_REQUIRED,
                loader=True,
                shelf=False,
                message=(
                    "The managed Houdini Shelf definition "
                    "is out of date."
                )
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

    def _write_loader(
        self,
        installation,
        options
    ):
        atomic_write(
            self._package_path(
                installation
            ),
            self._package_content(
                installation
            )
        )
        atomic_write(
            self._manifest_path(
                installation
            ),
            self._manifest_content(
                installation
            )
        )
        startup = self._uiready_content(
            installation
        )
        for path in self._startup_paths(
            installation
        ):
            atomic_write(
                path,
                startup
            )

        shelf_path = self._shelf_path(
            installation
        )
        if options["shelf"]:
            atomic_write(
                shelf_path,
                self._shelf_content()
            )
        elif os.path.isfile(shelf_path):
            try:
                content = read_text(
                    shelf_path
                )
            except Exception:
                content = ""
            if "script_toolbox_open" in content:
                os.remove(
                    shelf_path
                )

    def _sync_live_houdini(
        self,
        installation
    ):
        try:
            import hou
            current = parse_version(
                hou.applicationVersionString()
            )
            if current != installation.version:
                return False

            current_prefs = (
                hou.getenv(
                    "HOUDINI_USER_PREF_DIR"
                ) or
                os.environ.get(
                    "HOUDINI_USER_PREF_DIR"
                )
            )
            if (
                current_prefs and
                not self._same_path(
                    current_prefs,
                    installation.user_config_path
                )
            ):
                return False

            from .. import houdini_integration
            houdini_integration.apply_current_integration(
                profile_id=installation.profile_id
            )
            return True
        except Exception:
            _LOGGER.debug(
                "[DCC] Live Houdini UI sync skipped.",
                exc_info=True
            )
            return False

    def install(self, installation, options=None, sync_live=True):
        options = self.normalize_options(
            options
        )
        self._write_loader(
            installation,
            options
        )

        stored = dict(options)
        stored.update({
            "install_path": installation.install_path,
            "user_config_path": installation.user_config_path,
            "profile_id": installation.profile_id,
            "profile_label": installation.profile_label,
            "profile_root": installation.profile_root,
            "plugin_version": PLUGIN_VERSION,
        })
        set_integration_settings(
            self.key,
            installation.version,
            stored,
            path=self.config_path,
            profile_id=installation.profile_id
        )
        if sync_live:
            self._sync_live_houdini(installation)

        result = self.status(
            installation
        )
        if result.state != STATUS_INSTALLED:
            raise HoudiniIntegrationError(
                result.message or
                "Houdini integration verification failed: {0}".format(
                    result.state
                )
            )
        return result

    def repair(self, installation, sync_live=True):
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
            settings,
            sync_live=sync_live
        )

    def uninstall(self, installation, sync_live=True):
        remove_integration_settings(
            self.key,
            installation.version,
            path=self.config_path,
            profile_id=installation.profile_id
        )
        if sync_live:
            self._sync_live_houdini(installation)

        if not user_config_has_integration_settings(
            self.key,
            installation.user_config_path,
            path=self.config_path
        ):
            package_path = self._package_path(
                installation
            )
            if os.path.isfile(package_path):
                try:
                    content = read_text(
                        package_path
                    )
                except Exception:
                    content = ""
                if "SCRIPT_TOOLBOX_ROOT" in content:
                    os.remove(
                        package_path
                    )

            plugin_root = self._plugin_root(
                installation
            )
            manifest_path = self._manifest_path(
                installation
            )
            if os.path.isfile(manifest_path):
                try:
                    content = read_text(
                        manifest_path
                    )
                except Exception:
                    content = ""
                if '"integration": "houdini"' in content:
                    shutil.rmtree(
                        plugin_root,
                        ignore_errors=True
                    )

        return self.status(
            installation
        )


__all__ = [
    "HoudiniAdapter",
    "HoudiniIntegrationError",
]
