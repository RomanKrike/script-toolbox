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
    """One detected DCC installation and its user configuration location."""

    def __init__(
        self,
        dcc,
        display_name,
        version,
        install_path="",
        user_config_path="",
        detected=True,
        integration_available=False,
        supported=True
    ):
        self.dcc = text_type(dcc or "").strip().lower()
        self.display_name = text_type(display_name or dcc or "").strip()
        self.version = text_type(version or "").strip()
        self.install_path = text_type(install_path or "").strip()
        self.user_config_path = text_type(user_config_path or "").strip()
        self.detected = bool(detected)
        self.integration_available = bool(integration_available)
        self.supported = bool(supported)
        self.integration_status = STATUS_NOT_INSTALLED

    @property
    def key(self):
        return "{0}:{1}".format(
            self.dcc,
            self.version
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
        message=""
    ):
        self.state = text_type(state)
        self.loader = bool(loader)
        self.shelf = bool(shelf)
        self.main_menu = bool(main_menu)
        self.auto_open = bool(auto_open)
        self.message = text_type(message or "")

    def to_dict(self):
        return {
            "state": self.state,
            "loader": self.loader,
            "shelf": self.shelf,
            "main_menu": self.main_menu,
            "auto_open": self.auto_open,
            "message": self.message,
        }


class DccAdapter(object):
    """Base contract for one DCC integration backend."""

    key = ""
    display_name = ""
    integration_available = False
    supported = True

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
