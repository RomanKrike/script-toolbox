# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import sys

from ..constants import PLUGIN_VERSION
from ..core.logging_utils import get_logger
from .base import IntegrationStatus
from .base import STATUS_BROKEN
from .base import STATUS_INSTALLED
from .base import STATUS_NOT_INSTALLED
from .base import STATUS_UPDATE_REQUIRED
from .config import configured_versions
from .config import get_integration_settings
from .config import remove_integration_settings
from .config import set_integration_settings
from .discovery import distribution_root
from .discovery import parse_version
from .generic import DetectionOnlyAdapter
from .managed_files import marked_block_state
from .managed_files import remove_marked_block
from .managed_files import write_marked_block


_LOGGER = get_logger()
_MENU_BEGIN = "# >>> ScriptToolbox Nuke Integration >>>"
_MENU_END = "# <<< ScriptToolbox Nuke Integration <<<"


class NukeIntegrationError(RuntimeError):
    pass


class NukeAdapter(DetectionOnlyAdapter):
    key = "nuke"
    display_name = "Foundry Nuke"
    environment_variable = ""
    integration_available = True
    supported = True

    def __init__(
        self,
        distribution_path=None,
        program_files=None,
        user_config_path=None,
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
        self._user_config_path = os.path.normpath(
            user_config_path or os.path.expanduser("~/.nuke")
        )
        self.config_path = config_path

    @property
    def scripts_path(self):
        return os.path.join(
            self.distribution_path,
            "scripts"
        )

    def install_patterns(self):
        if os.name == "nt":
            return [os.path.join(self.program_files, "Nuke*")]
        if sys.platform == "darwin":
            return ["/Applications/Nuke*.app"]
        return ["/usr/local/Nuke*"]

    def user_config_path(self, version):
        return self._user_config_path

    def option_definitions(self):
        return (
            ("main_menu", "Add to Main Menu", True),
            ("dock_panel", "Register Dock Panel", True),
            ("auto_open", "Open on startup", False),
        )

    def component_status_text(self, status, options=None):
        options = self.normalize_options(options)
        return "    ".join([
            "Loader: {0}".format(
                "OK" if status.loader else "Missing"
            ),
            "Main Menu: {0}".format(
                (
                    "Registered" if status.main_menu else "Missing"
                ) if options["main_menu"] else "Disabled"
            ),
            "Dock Panel: {0}".format(
                "Enabled" if options["dock_panel"] else "Disabled"
            ),
        ])

    @staticmethod
    def _menu_path(installation):
        return os.path.join(
            installation.user_config_path,
            "menu.py"
        )

    def _startup_block(self):
        scripts_path = self.scripts_path.replace("\\", "/")
        return "\n".join([
            _MENU_BEGIN,
            "import sys as _stb_sys",
            "_stb_scripts = {0!r}".format(scripts_path),
            "if _stb_scripts not in _stb_sys.path:",
            "    _stb_sys.path.insert(0, _stb_scripts)",
            "try:",
            "    import script_toolbox.nuke_integration as _stb_nuke_integration",
            "    _stb_nuke_integration.apply_current_integration()",
            "except Exception:",
            "    import traceback",
            "    traceback.print_exc()",
            _MENU_END,
        ])

    def _startup_state(self, installation):
        return marked_block_state(
            self._menu_path(installation),
            _MENU_BEGIN,
            _MENU_END,
            self._startup_block()
        )

    def status(self, installation):
        settings = get_integration_settings(
            self.key,
            installation.version,
            path=self.config_path,
            profile_id=installation.profile_id
        )
        startup_state = self._startup_state(installation)

        if settings is None:
            return IntegrationStatus(
                STATUS_NOT_INSTALLED,
                loader=(startup_state == "ok")
            )

        if startup_state == "broken":
            return IntegrationStatus(
                STATUS_BROKEN,
                loader=False,
                message="Cannot read the managed Nuke menu.py integration."
            )
        if startup_state == "missing":
            return IntegrationStatus(
                STATUS_BROKEN,
                loader=False,
                message="The Script Toolbox Nuke startup block is missing."
            )
        if startup_state == "stale":
            return IntegrationStatus(
                STATUS_UPDATE_REQUIRED,
                loader=True,
                message=(
                    "The Nuke startup integration points to an older "
                    "Script Toolbox location or version."
                )
            )

        desired = self.normalize_options(settings)
        return IntegrationStatus(
            STATUS_INSTALLED,
            loader=True,
            main_menu=desired["main_menu"],
            auto_open=desired["auto_open"],
            components={
                "Dock Panel": (
                    "Enabled" if desired["dock_panel"] else "Disabled"
                )
            }
        )

    def _sync_live_nuke(self, installation):
        try:
            import nuke
            current = parse_version(
                getattr(nuke, "NUKE_VERSION_STRING", "")
            )
            if current != installation.version:
                return False
            from .. import nuke_integration
            nuke_integration.apply_current_integration()
            return True
        except Exception:
            _LOGGER.debug(
                "[DCC] Live Nuke UI sync skipped.",
                exc_info=True
            )
            return False

    def install(self, installation, options=None):
        options = self.normalize_options(options)
        write_marked_block(
            self._menu_path(installation),
            _MENU_BEGIN,
            _MENU_END,
            self._startup_block()
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
        self._sync_live_nuke(installation)

        result = self.status(installation)
        if result.state != STATUS_INSTALLED:
            raise NukeIntegrationError(
                result.message or
                "Nuke integration verification failed: {0}".format(
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
        return self.install(installation, settings)

    def uninstall(self, installation):
        remove_integration_settings(
            self.key,
            installation.version,
            path=self.config_path,
            profile_id=installation.profile_id
        )

        if not configured_versions(
            self.key,
            path=self.config_path
        ):
            remove_marked_block(
                self._menu_path(installation),
                _MENU_BEGIN,
                _MENU_END
            )

        self._sync_live_nuke(installation)
        return self.status(installation)


__all__ = [
    "NukeAdapter",
    "NukeIntegrationError",
]
