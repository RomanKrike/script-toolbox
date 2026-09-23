# -*- coding: utf-8 -*-
from __future__ import print_function

import json
import re
import threading
import time

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

from ..constants import PLUGIN_VERSION
from ..core import http_transport
from ..pycompat import text_type


USER_AGENT = (
    "Script-Toolbox-Share/{0} "
    "(github.com/RomanKrike/script-toolbox)"
).format(PLUGIN_VERSION)


class ShareProviderError(RuntimeError):
    pass


class ShareProvider(object):
    name = ""

    def upload(self, content, expiry_days=7):
        raise NotImplementedError

    def download(self, paste_id):
        raise NotImplementedError


_RATE_LOCK = threading.Lock()
_LAST_REQUEST = [0.0]


def _throttle():
    # dpaste asks automated clients not to exceed one request per second.
    with _RATE_LOCK:
        elapsed = time.time() - _LAST_REQUEST[0]
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)
        _LAST_REQUEST[0] = time.time()


def _as_bytes(value):
    if isinstance(value, bytes):
        return value
    return text_type(value).encode("utf-8")


def _as_text(value):
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return text_type(value)


def _share_headers(content_type=None):
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/plain",
    }
    if content_type:
        headers["Content-Type"] = content_type
    return headers


# ----------------------------------------------------------------------
# Deprecated transport compatibility wrappers
# ----------------------------------------------------------------------
# Older tests and direct imports may still reference these private names. They
# now forward to core.http_transport; production provider flow does not carry a
# second Windows/PowerShell implementation.


def _is_windows():
    return http_transport.is_windows()


def _legacy_windows_python():
    return http_transport.legacy_windows_python()


def _prefer_powershell_first():
    return http_transport.prefer_powershell_first()


def _powershell_executable():
    return http_transport.powershell_executable()


def _ps_quote(value):
    return http_transport.powershell_quote(value)


def _hidden_process_kwargs():
    return http_transport.hidden_process_kwargs()


def _powershell_request(
    url,
    data=None,
    timeout=15,
    content_type=None
):
    try:
        return http_transport.powershell_request(
            url,
            data=data,
            headers=_share_headers(content_type),
            timeout=timeout
        )
    except http_transport.TransportError as exc:
        raise ShareProviderError(text_type(exc))


def _request(
    url,
    data=None,
    timeout=15,
    content_type=None
):
    try:
        return http_transport.request_bytes(
            url,
            data=data,
            headers=_share_headers(content_type),
            timeout=timeout
        )
    except http_transport.TransportError as exc:
        raise ShareProviderError(
            "Share service request failed: {0}".format(
                text_type(exc)
            )
        )


class PastesDevProvider(ShareProvider):
    name = "pastes-dev"
    api_url = "https://api.pastes.dev/post"
    raw_url = "https://api.pastes.dev/{0}"

    def upload(self, content, expiry_days=7):
        # The public pastes.dev API does not expose per-paste expiry.
        # Shared Script Toolbox data is encrypted before it reaches here.
        response_text = _as_text(
            _request(
                self.api_url,
                data=_as_bytes(content),
                content_type="text/plain; charset=utf-8"
            )
        ).strip()

        try:
            payload = json.loads(response_text)
            paste_id = text_type(
                payload.get("key", "")
            ).strip()
        except Exception:
            paste_id = ""

        if not re.match(r"^[A-Za-z0-9_-]+$", paste_id):
            raise ShareProviderError(
                "pastes.dev returned an unexpected response."
            )

        return paste_id

    def download(self, paste_id):
        paste_id = text_type(paste_id or "").strip()
        if not re.match(r"^[A-Za-z0-9_-]+$", paste_id):
            raise ShareProviderError(
                "Invalid pastes.dev item ID."
            )

        return _as_text(
            _request(
                self.raw_url.format(paste_id)
            )
        ).strip()


class DpasteProvider(ShareProvider):
    name = "dpaste"
    api_url = "https://dpaste.com/api/v2/"
    raw_url = "https://dpaste.com/{0}.txt"

    def upload(self, content, expiry_days=7):
        try:
            expiry_days = int(expiry_days)
        except Exception:
            expiry_days = 7
        expiry_days = max(1, min(365, expiry_days))

        form = urlencode({
            "content": text_type(content),
            "title": "Script Toolbox encrypted share",
            "expiry_days": text_type(expiry_days),
        })
        _throttle()
        body = _as_text(
            _request(
                self.api_url,
                data=form,
                content_type="application/x-www-form-urlencoded"
            )
        ).strip()

        match = re.search(
            r"/([A-Za-z0-9_-]+)/?$",
            body
        )
        if match is None:
            raise ShareProviderError(
                "dpaste returned an unexpected response."
            )

        return match.group(1)

    def download(self, paste_id):
        paste_id = text_type(paste_id or "").strip()
        if not re.match(r"^[A-Za-z0-9_-]+$", paste_id):
            raise ShareProviderError(
                "Invalid dpaste item ID."
            )

        _throttle()
        return _as_text(
            _request(
                self.raw_url.format(paste_id)
            )
        ).strip()


__all__ = [
    "DpasteProvider",
    "PastesDevProvider",
    "ShareProvider",
    "ShareProviderError",
]
