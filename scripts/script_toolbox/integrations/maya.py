# -*- coding: utf-8 -*-
from __future__ import print_function

import io
import os
import re
import shutil
import tempfile

from ..constants import PLUGIN_VERSION
from ..core.logging_utils import get_logger
from ..pycompat import text_type
from .base import DccAdapter
from .base import DccInstallation
from .base import IntegrationStatus
from .base import STATUS_BROKEN
from .base import STATUS_INSTALLED
from .base import STATUS_NOT_INSTALLED
from .base import STATUS_PARTIAL
from .base import STATUS_UPDATE_REQUIRED
from .config import DEFAULT_PROFILE_ID
from .config import add_profile_root
from .config import find_profile_id_for_paths
from .config import get_integration_settings
from .config import get_profile_roots
from .config import remove_integration_settings
from .config import remove_profile_root
from .config import set_integration_settings
from .discovery import distribution_root
from .discovery import existing_directories
from .discovery import maya_user_config_for_version
from .discovery import maya_user_root
from .discovery import parse_version
from .discovery import version_sort_key


_LOGGER = get_logger()
_MANAGED_MODULE_MARKER = "# ScriptToolbox managed DCC integration"
_USER_SETUP_BEGIN = "# >>> ScriptToolbox DCC Integration >>>"
_USER_SETUP_END = "# <<< ScriptToolbox DCC Integration <<<"
_SHELF_MARKER = "// ScriptToolbox managed shelf"
_MODULE_FILENAME = "ScriptToolboxIntegration.mod"
_SHELF_FILENAME = "shelf_ScriptToolbox.mel"


class MayaIntegrationError(RuntimeError):
    pass


def _read_text(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def _replace_file_windows(source, destination):
    import ctypes

    move_file_ex = ctypes.windll.kernel32.MoveFileExW
    flags = 0x00000001 | 0x00000008
    result = move_file_ex(
        text_type(os.path.abspath(source)),
        text_type(os.path.abspath(destination)),
        flags
    )
    if not result:
        raise ctypes.WinError()


def _replace_file(source, destination):
    replace = getattr(os, "replace", None)
    if replace is not None:
        replace(source, destination)
        return
    if os.name == "nt":
        _replace_file_windows(source, destination)
        return
    os.rename(source, destination)


def _atomic_write(path, content):
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)

    descriptor, temp_path = tempfile.mkstemp(
        prefix=".script_toolbox_dcc_",
        suffix=".tmp",
        dir=(folder or ".")
    )
    os.close(descriptor)
    try:
        with io.open(temp_path, "w", encoding="utf-8") as handle:
            handle.write(text_type(content))
            handle.flush()
            os.fsync(handle.fileno())
        _replace_file(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def _backup_once(path):
    if not os.path.isfile(path):
        return None
    backup = path + ".script_toolbox.bak"
    if not os.path.exists(backup):
        shutil.copy2(path, backup)
    return backup


def _managed_block():
    return "\n".join([
        _USER_SETUP_BEGIN,
        "try:",
        "    from script_toolbox.integrations import maya_runtime as _stb_maya_runtime",
        "    _stb_maya_runtime.install_startup_ui()",
        "except Exception:",
        "    import traceback",
        "    traceback.print_exc()",
        _USER_SETUP_END,
    ])


def _replace_marked_block(content, replacement=None):
    content = text_type(content or "")
    pattern = re.compile(
        re.escape(_USER_SETUP_BEGIN) +
        r".*?" +
        re.escape(_USER_SETUP_END) +
        r"(?:\r?\n)?",
        re.S
    )
    cleaned = pattern.sub("", content)
    cleaned = cleaned.rstrip()

    if replacement:
        if cleaned:
            cleaned += "\n\n"
        cleaned += text_type(replacement).rstrip()

    if cleaned:
        cleaned += "\n"
    return cleaned


def _contains_managed_block(path):
    if not os.path.isfile(path):
        return False
    try:
        content = _read_text(path)
    except Exception:
        return False
    return (
        _USER_SETUP_BEGIN in content and
        _USER_SETUP_END in content
    )


def _shelf_content():
    return u'''// ScriptToolbox managed shelf\n'''+u'''global proc shelf_ScriptToolbox ()\n'''+u'''{\n'''+u'''    global string $gShelfTopLevel;\n'''+u'''    shelfLayout -cellWidth 34 -cellHeight 34 -parent $gShelfTopLevel "ScriptToolbox";\n'''+u'''    shelfButton\n'''+u'''        -label "ScriptToolbox"\n'''+u'''        -annotation "Open Script Toolbox"\n'''+u'''        -image1 "pythonFamily.png"\n'''+u'''        -command "python(\\\"import script_toolbox; script_toolbox.show()\\\")"\n'''+u'''        -sourceType "mel"\n'''+u'''        "ScriptToolboxOpenButton";\n'''+u'''}\n'''


def _normalize_options(options):
    options = dict(options or {})
    return {
        "shelf": bool(options.get("shelf", True)),
        "main_menu": bool(options.get("main_menu", True)),
        "auto_open": bool(options.get("auto_open", False)),
    }


def _default_registry_installations():
    if os.name != "nt":
        return []

    try:
        try:
            import winreg
        except ImportError:
            import _winreg as winreg
    except Exception:
        return []

    result = []
    roots = [winreg.HKEY_LOCAL_MACHINE]
    views = [0]
    for name in ("KEY_WOW64_64KEY", "KEY_WOW64_32KEY"):
        value = getattr(winreg, name, None)
        if value is not None:
            views.append(value)

    base = r"SOFTWARE\Autodesk\Maya"
    for root in roots:
        for view in views:
            access = getattr(winreg, "KEY_READ", 0) | view
            try:
                maya_key = winreg.OpenKey(root, base, 0, access)
            except Exception:
                continue
            try:
                count = winreg.QueryInfoKey(maya_key)[0]
                for index in range(count):
                    try:
                        version_name = winreg.EnumKey(maya_key, index)
                    except Exception:
                        continue
                    version = parse_version(version_name)
                    if not version:
                        continue
                    setup_path = base + "\\" + version_name + "\\Setup\\InstallPath"
                    try:
                        setup_key = winreg.OpenKey(root, setup_path, 0, access)
                    except Exception:
                        continue
                    try:
                        install_path = ""
                        for value_name in ("MAYA_INSTALL_LOCATION", ""):
                            try:
                                install_path = winreg.QueryValueEx(
                                    setup_key,
                                    value_name
                                )[0]
                            except Exception:
                                continue
                            if install_path:
                                break
                        if install_path:
                            result.append((version, install_path))
                    finally:
                        try:
                            winreg.CloseKey(setup_key)
                        except Exception:
                            pass
            finally:
                try:
                    winreg.CloseKey(maya_key)
                except Exception:
                    pass
    return result


class MayaAdapter(DccAdapter):
    key = "maya"
    display_name = "Autodesk Maya"
    integration_available = True
    supported = True

    def __init__(
        self,
        distribution_path=None,
        user_root=None,
        program_files=None,
        registry_reader=None,
        config_path=None
    ):
        self.distribution_path = os.path.normpath(
            distribution_path or distribution_root()
        )
        self.user_root = os.path.normpath(
            user_root or maya_user_root()
        )
        self.program_files = os.path.normpath(
            program_files or
            os.environ.get("ProgramFiles") or
            r"C:\Program Files"
        )
        self.registry_reader = registry_reader or _default_registry_installations
        self.config_path = config_path

    @staticmethod
    def _same_path(first, second):
        if not first or not second:
            return False
        return os.path.normcase(os.path.normpath(first)) == os.path.normcase(
            os.path.normpath(second)
        )

    def profile_roots(self):
        roots = [{
            "id": DEFAULT_PROFILE_ID,
            "label": "Default",
            "path": self.user_root,
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
            raise MayaIntegrationError("Profile path is empty.")
        if self._same_path(normalized, self.user_root):
            raise MayaIntegrationError(
                "This path is already the default Maya profile root."
            )
        return add_profile_root(
            self.key,
            normalized,
            label=label,
            path=self.config_path
        )

    def remove_profile_root(self, profile_id):
        profile_id = text_type(profile_id or "").strip()
        if not profile_id or profile_id == DEFAULT_PROFILE_ID:
            raise MayaIntegrationError(
                "The default Maya profile root cannot be removed."
            )

        for installation in self.get_installations():
            if installation.profile_id != profile_id:
                continue
            if self.status(installation).state != STATUS_NOT_INSTALLED:
                raise MayaIntegrationError(
                    "Uninstall Script Toolbox from {0} {1} ({2}) before "
                    "removing this profile path.".format(
                        self.display_name,
                        installation.version,
                        installation.profile_label
                    )
                )

        return remove_profile_root(
            self.key,
            profile_id,
            path=self.config_path
        )

    @staticmethod
    def _module_path(installation):
        return os.path.join(
            installation.user_config_path,
            "modules",
            _MODULE_FILENAME
        )

    def _module_content(self):
        return u"{0}\n+ ScriptToolboxIntegration {1} {2}\nPYTHONPATH +:= scripts\n".format(
            _MANAGED_MODULE_MARKER,
            PLUGIN_VERSION,
            self.distribution_path.replace("\\", "/")
        )

    @staticmethod
    def _user_setup_path(installation):
        return os.path.join(
            installation.user_config_path,
            "scripts",
            "userSetup.py"
        )

    @staticmethod
    def _shelf_path(installation):
        return os.path.join(
            installation.user_config_path,
            "prefs",
            "shelves",
            _SHELF_FILENAME
        )

    def _module_state(self, installation):
        path = self._module_path(installation)
        if not os.path.isfile(path):
            return "missing"
        try:
            content = _read_text(path)
        except Exception:
            return "broken"
        if _MANAGED_MODULE_MARKER not in content:
            return "foreign"
        if content != self._module_content():
            return "stale"
        return "ok"

    def _detected_install_paths(self):
        result = []
        seen = set()

        try:
            registry_values = self.registry_reader() or []
        except Exception:
            registry_values = []

        for version, path in registry_values:
            normalized = os.path.normpath(text_type(path or ""))
            if not normalized:
                continue
            key = (text_type(version), os.path.normcase(normalized))
            if key not in seen:
                seen.add(key)
                result.append((text_type(version), normalized))

        env_path = os.environ.get("MAYA_LOCATION")
        if env_path:
            version = parse_version(env_path)
            if version:
                key = (version, os.path.normcase(os.path.normpath(env_path)))
                if key not in seen:
                    seen.add(key)
                    result.append((version, os.path.normpath(env_path)))

        if os.name == "nt":
            patterns = [
                os.path.join(
                    self.program_files,
                    "Autodesk",
                    "Maya*"
                )
            ]
        elif os.sys.platform == "darwin":
            patterns = [
                "/Applications/Autodesk/maya*/Maya.app"
            ]
        else:
            patterns = [
                "/usr/autodesk/maya*"
            ]

        for path in existing_directories(patterns):
            version = parse_version(path)
            if not version:
                continue
            key = (version, os.path.normcase(path))
            if key not in seen:
                seen.add(key)
                result.append((version, path))
        return result

    @staticmethod
    def _profile_targets_for_root(root_path):
        root_path = os.path.normpath(
            os.path.expanduser(
                text_type(root_path or "").strip()
            )
        )
        if not root_path or not os.path.isdir(root_path):
            return []

        base_name = os.path.basename(root_path.rstrip("\\/"))
        base_version = parse_version(base_name)
        if base_version and len(base_version) == 4:
            return [(base_version, root_path)]

        try:
            names = os.listdir(root_path)
        except OSError:
            names = []

        result = []
        seen = set()
        for name in names:
            profile_path = os.path.join(root_path, name)
            if not os.path.isdir(profile_path):
                continue
            version = parse_version(name)
            if not version or len(version) != 4:
                continue
            key = (version, os.path.normcase(profile_path))
            if key in seen:
                continue
            seen.add(key)
            result.append((version, profile_path))
        result.sort(key=lambda item: version_sort_key(item[0]))
        return result

    def get_installations(self):
        install_paths = {}
        for version, install_path in self._detected_install_paths():
            install_paths[version] = install_path

        default_versions = set(install_paths.keys())
        for version, unused_path in self._profile_targets_for_root(
            self.user_root
        ):
            default_versions.add(version)

        installations = []
        seen_user_configs = set()
        for version in sorted(default_versions, key=version_sort_key):
            default_config_path = maya_user_config_for_version(
                version,
                user_root=self.user_root
            )
            seen_user_configs.add(
                os.path.normcase(
                    os.path.normpath(default_config_path)
                )
            )
            installation = DccInstallation(
                self.key,
                self.display_name,
                version,
                install_path=install_paths.get(version, ""),
                user_config_path=default_config_path,
                integration_available=True,
                supported=True,
                profile_id=DEFAULT_PROFILE_ID,
                profile_label="Default",
                profile_root=self.user_root,
                profile_source="default"
            )
            installation.integration_status = self.status(
                installation
            ).state
            installations.append(installation)

        for record in get_profile_roots(
            self.key,
            path=self.config_path
        ):
            for version, profile_path in self._profile_targets_for_root(
                record.get("path")
            ):
                profile_path_key = os.path.normcase(
                    os.path.normpath(profile_path)
                )
                if profile_path_key in seen_user_configs:
                    continue
                seen_user_configs.add(profile_path_key)
                installation = DccInstallation(
                    self.key,
                    self.display_name,
                    version,
                    install_path=install_paths.get(version, ""),
                    user_config_path=profile_path,
                    integration_available=True,
                    supported=True,
                    profile_id=record["id"],
                    profile_label=record.get("label") or "Custom",
                    profile_root=record.get("path") or "",
                    profile_source="custom"
                )
                installation.integration_status = self.status(
                    installation
                ).state
                installations.append(installation)

        installations.sort(
            key=lambda item: (
                version_sort_key(item.version),
                0 if item.profile_id == DEFAULT_PROFILE_ID else 1,
                item.profile_label.lower()
            )
        )
        return installations

    def status(self, installation):
        settings = get_integration_settings(
            self.key,
            installation.version,
            path=self.config_path,
            profile_id=installation.profile_id
        )
        user_setup = self._user_setup_path(installation)
        shelf_path = self._shelf_path(installation)
        setup_present = _contains_managed_block(user_setup)
        shelf_present = False
        if os.path.isfile(shelf_path):
            try:
                shelf_present = _SHELF_MARKER in _read_text(shelf_path)
            except Exception:
                shelf_present = False

        if settings is None and not setup_present and not shelf_present:
            return IntegrationStatus(
                STATUS_NOT_INSTALLED,
                loader=(self._module_state(installation) == "ok")
            )

        module_state = self._module_state(installation)
        if module_state in ("foreign", "broken"):
            return IntegrationStatus(
                STATUS_BROKEN,
                loader=False,
                shelf=shelf_present,
                main_menu=setup_present,
                message="Cannot verify the managed Maya module file."
            )
        if module_state == "stale":
            return IntegrationStatus(
                STATUS_UPDATE_REQUIRED,
                loader=True,
                shelf=shelf_present,
                main_menu=setup_present,
                message="The Maya loader points to an older Script Toolbox location or version."
            )
        if module_state == "missing":
            return IntegrationStatus(
                STATUS_BROKEN,
                loader=False,
                shelf=shelf_present,
                main_menu=setup_present,
                message="The Script Toolbox Maya module file is missing."
            )

        desired = _normalize_options(settings or {})
        startup_required = bool(
            desired["shelf"] or
            desired["main_menu"] or
            desired["auto_open"]
        )
        problems = []
        if startup_required != setup_present:
            problems.append("startup loader")
        if desired["shelf"] != shelf_present:
            problems.append("Shelf")

        if problems:
            return IntegrationStatus(
                STATUS_PARTIAL,
                loader=True,
                shelf=shelf_present,
                main_menu=(setup_present and desired["main_menu"]),
                auto_open=(setup_present and desired["auto_open"]),
                message="Mismatch: {0}.".format(
                    ", ".join(problems)
                )
            )

        return IntegrationStatus(
            STATUS_INSTALLED,
            loader=True,
            shelf=desired["shelf"],
            main_menu=desired["main_menu"],
            auto_open=desired["auto_open"]
        )

    def _ensure_module(self, installation):
        path = self._module_path(installation)
        if os.path.isfile(path):
            content = _read_text(path)
            if _MANAGED_MODULE_MARKER not in content:
                raise MayaIntegrationError(
                    "Cannot write Maya module: {0} already exists and is not managed by Script Toolbox.".format(
                        path
                    )
                )
            if content == self._module_content():
                return path
            _backup_once(path)
        _atomic_write(path, self._module_content())
        _LOGGER.info("[DCC] Maya loader installed: %s", path)
        return path

    def _set_startup_block(self, installation, enabled):
        path = self._user_setup_path(installation)
        exists = os.path.isfile(path)
        content = _read_text(path) if exists else u""
        present = (
            _USER_SETUP_BEGIN in content and
            _USER_SETUP_END in content
        )
        if enabled and present:
            normalized = _replace_marked_block(content, _managed_block())
            if normalized == content:
                return path
        elif not enabled and not present:
            return path

        if exists:
            _backup_once(path)
        updated = _replace_marked_block(
            content,
            _managed_block() if enabled else None
        )
        if updated:
            _atomic_write(path, updated)
        elif exists:
            _atomic_write(path, u"")
        return path

    def _set_shelf_file(self, installation, enabled):
        path = self._shelf_path(installation)
        if enabled:
            if os.path.isfile(path):
                content = _read_text(path)
                if _SHELF_MARKER not in content:
                    raise MayaIntegrationError(
                        "Cannot install Shelf: {0} already exists and is not managed by Script Toolbox.".format(
                            path
                        )
                    )
                if content == _shelf_content():
                    return path
                _backup_once(path)
            _atomic_write(path, _shelf_content())
            return path

        if os.path.isfile(path):
            content = _read_text(path)
            if _SHELF_MARKER in content:
                os.remove(path)
        return path

    def _sync_live_maya(self, installation):
        try:
            import maya.cmds as cmds
            current = parse_version(
                cmds.about(version=True)
            )
            if current != text_type(installation.version):
                return False

            candidates = []
            try:
                candidates.append(cmds.internalVar(userAppDir=True))
            except Exception:
                pass
            try:
                user_pref = cmds.internalVar(userPrefDir=True)
                if user_pref:
                    candidates.append(
                        os.path.dirname(
                            os.path.normpath(
                                user_pref.rstrip("\\/")
                            )
                        )
                    )
            except Exception:
                pass

            current_profile_id = find_profile_id_for_paths(
                self.key,
                candidates,
                path=self.config_path
            )
            if current_profile_id != installation.profile_id:
                return False

            from . import maya_runtime
            maya_runtime.apply_current_integration()
            return True
        except Exception:
            _LOGGER.debug(
                "[DCC] Live Maya UI sync skipped.",
                exc_info=True
            )
            return False

    def install(self, installation, options=None, sync_live=True):
        options = _normalize_options(options)
        _LOGGER.info(
            "[DCC] Installing Maya %s integration",
            installation.version
        )

        self._ensure_module(installation)
        self._set_shelf_file(
            installation,
            options["shelf"]
        )
        startup_required = bool(
            options["shelf"] or
            options["main_menu"] or
            options["auto_open"]
        )
        self._set_startup_block(
            installation,
            startup_required
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
            self._sync_live_maya(installation)

        result = self.status(installation)
        if result.state != STATUS_INSTALLED:
            raise MayaIntegrationError(
                result.message or
                "Maya integration verification failed: {0}".format(
                    result.state
                )
            )
        _LOGGER.info("[DCC] Maya %s integration verified", installation.version)
        return result

    def repair(self, installation, sync_live=True):
        settings = get_integration_settings(
            self.key,
            installation.version,
            path=self.config_path,
            profile_id=installation.profile_id
        )
        if settings is None:
            settings = {
                "shelf": True,
                "main_menu": True,
                "auto_open": False,
            }
        _LOGGER.info(
            "[DCC] Repairing Maya %s integration",
            installation.version
        )
        return self.install(
            installation,
            settings,
            sync_live=sync_live
        )

    def uninstall(self, installation, sync_live=True):
        _LOGGER.info(
            "[DCC] Uninstalling Maya %s integration",
            installation.version
        )
        self._set_shelf_file(installation, False)
        self._set_startup_block(installation, False)
        remove_integration_settings(
            self.key,
            installation.version,
            path=self.config_path,
            profile_id=installation.profile_id
        )
        if sync_live:
            self._sync_live_maya(installation)

        module_path = self._module_path(installation)
        if os.path.isfile(module_path):
            try:
                content = _read_text(module_path)
            except Exception:
                content = ""
            if _MANAGED_MODULE_MARKER in content:
                os.remove(module_path)

        return self.status(installation)


__all__ = [
    "MayaAdapter",
    "MayaIntegrationError",
]
