# -*- coding: utf-8 -*-
from __future__ import print_function

from ..pycompat import text_type


STATUS_NOT_INSTALLED = "Not installed"
STATUS_INSTALLED = "Installed"
STATUS_PARTIAL = "Partially installed"
STATUS_BROKEN = "Broken"
STATUS_UPDATE_REQUIRED = "Update required"
STATUS_UNSUPPORTED = "Unsupported"


class DccInstallation(object):
    """One detected DCC installation/profile integration target."""

    def __init__(
        self,
        dcc,
        display_name,
        version,
        install_path="",
        user_config_path="",
        detected=True,
        integration_available=False,
        supported=False,
        profile_id="default",
        profile_label="Default",
        profile_root="",
        profile_source="default"
    ):
        self.dcc = text_type(dcc or "").strip().lower()
        self.display_name = text_type(display_name or dcc or "").strip()
        self.version = text_type(version or "").strip()
        self.install_path = text_type(install_path or "").strip()
        self.user_config_path = text_type(user_config_path or "").strip()
        self.detected = bool(detected)
        self.integration_available = bool(integration_available)
        self.supported = bool(supported)
        self.profile_id = text_type(profile_id or "default").strip()
        self.profile_label = text_type(profile_label or "Default").strip()
        self.profile_root = text_type(profile_root or "").strip()
        self.profile_source = text_type(profile_source or "default").strip()
        self.integration_status = STATUS_NOT_INSTALLED

    @property
    def key(self):
        if self.profile_id == "default":
            return "{0}:{1}".format(
                self.dcc,
                self.version
            )
        return "{0}:{1}:{2}".format(
            self.dcc,
            self.version,
            self.profile_id
        )

    def to_dict(self):
        return {
            "dcc": self.dcc,
            "display_name": self.display_name,
            "version": self.version,
            "install_path": self.install_path,
            "user_config_path": self.user_config_path,
            "detected": self.detected,
            "integration_available": self.integration_available,
            "supported": self.supported,
            "profile_id": self.profile_id,
            "profile_label": self.profile_label,
            "profile_root": self.profile_root,
            "profile_source": self.profile_source,
            "integration_status": self.integration_status,
        }


class IntegrationStatus(object):
    """Filesystem-backed integration status for one DCC installation."""

    def __init__(
        self,
        state,
        loader=False,
        shelf=False,
        main_menu=False,
        auto_open=False,
        message="",
        components=None
    ):
        self.state = text_type(state)
        self.loader = bool(loader)
        self.shelf = bool(shelf)
        self.main_menu = bool(main_menu)
        self.auto_open = bool(auto_open)
        self.message = text_type(message or "")
        self.components = dict(components or {})

    def to_dict(self):
        return {
            "state": self.state,
            "loader": self.loader,
            "shelf": self.shelf,
            "main_menu": self.main_menu,
            "auto_open": self.auto_open,
            "message": self.message,
            "components": dict(self.components),
        }


class DccAdapter(object):
    """Base contract for one DCC integration backend."""

    key = ""
    display_name = ""
    integration_available = False
    supported = False

    def option_definitions(self):
        return (
            ("shelf", "Add to Shelf", True),
            ("main_menu", "Add to Main Menu", True),
            ("auto_open", "Open on startup", False),
        )

    def normalize_options(self, options=None):
        values = dict(options or {})
        result = {}
        for key, unused_label, default in self.option_definitions():
            result[key] = bool(values.get(key, default))
        return result

    def component_status_text(self, status, options=None):
        options = self.normalize_options(options)
        parts = [
            "Loader: {0}".format(
                "OK" if status.loader else "Missing"
            )
        ]
        if "shelf" in options:
            parts.append(
                "Shelf: {0}".format(
                    (
                        "OK" if status.shelf else "Missing"
                    ) if options["shelf"] else "Disabled"
                )
            )
        if "main_menu" in options:
            parts.append(
                "Main Menu: {0}".format(
                    (
                        "Registered" if status.main_menu else "Missing"
                    ) if options["main_menu"] else "Disabled"
                )
            )
        for label, value in sorted(status.components.items()):
            parts.append("{0}: {1}".format(label, value))
        return "    ".join(parts)

    def detect(self):
        return bool(
            self.get_installations()
        )

    def get_installations(self):
        return []

    def status(self, installation):
        if not self.integration_available:
            return IntegrationStatus(
                STATUS_UNSUPPORTED,
                message="Integration is not implemented for {0}.".format(
                    self.display_name
                )
            )
        return IntegrationStatus(
            STATUS_NOT_INSTALLED
        )

    def install(self, installation, options=None):
        raise NotImplementedError

    def repair(self, installation):
        raise NotImplementedError

    def uninstall(self, installation):
        raise NotImplementedError


__all__ = [
    "DccAdapter",
    "DccInstallation",
    "IntegrationStatus",
    "STATUS_BROKEN",
    "STATUS_INSTALLED",
    "STATUS_NOT_INSTALLED",
    "STATUS_PARTIAL",
    "STATUS_UNSUPPORTED",
    "STATUS_UPDATE_REQUIRED",
]
