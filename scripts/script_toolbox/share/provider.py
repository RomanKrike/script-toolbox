# -*- coding: utf-8 -*-
from __future__ import print_function

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time

try:
    from urllib import urlencode
    from urllib2 import Request
    from urllib2 import urlopen
except ImportError:
    from urllib.parse import urlencode
    from urllib.request import Request
    from urllib.request import urlopen

from ..constants import PLUGIN_VERSION
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
_WINDOWS_POWERSHELL_PREFERRED = [False]


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


def _is_windows():
    return os.name == "nt"


def _legacy_windows_python():
    return _is_windows() and sys.version_info[0] < 3


def _prefer_powershell_first():
    # Maya versions that embed Python 2.7 commonly fail modern HTTPS/TLS in
    # urllib. Avoid paying the full urllib timeout before using the transport
    # that is known to work there. On newer Windows runtimes, remember a
    # successful fallback for the rest of the process after urllib fails once.
    return _is_windows() and (
        _legacy_windows_python() or
        _WINDOWS_POWERSHELL_PREFERRED[0]
    )


def _powershell_executable():
    if not _is_windows():
        return None

    root = os.environ.get(
        "SystemRoot",
        r"C:\Windows"
    )
    candidate = os.path.join(
        root,
        "System32",
        "WindowsPowerShell",
        "v1.0",
        "powershell.exe"
    )

    if os.path.isfile(candidate):
        return candidate
    return "powershell.exe"


def _ps_quote(value):
    return text_type(value).replace("'", "''")


def _hidden_process_kwargs():
    if not _is_windows():
        return {}

    result = {
        "creationflags": 0x08000000,
    }
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        try:
            startupinfo.wShowWindow = 0
        except Exception:
            pass
        result["startupinfo"] = startupinfo
    except Exception:
        pass
    return result


def _powershell_request(
    url,
    data=None,
    timeout=15,
    content_type=None
):
    executable = _powershell_executable()
    if not executable:
        raise ShareProviderError(
            "PowerShell TLS fallback is unavailable."
        )

    directory = tempfile.mkdtemp(
        prefix="script_toolbox_share_"
    )
    body_path = os.path.join(directory, "request.bin")
    output_path = os.path.join(directory, "response.bin")

    try:
        if data is not None:
            with open(body_path, "wb") as handle:
                handle.write(_as_bytes(data))

        timeout_ms = max(
            1000,
            int(float(timeout) * 1000.0)
        )
        script = [
            "$ErrorActionPreference = 'Stop'",
            "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12",
            "$request = [System.Net.HttpWebRequest]::Create('{0}')".format(
                _ps_quote(url)
            ),
            "$request.UserAgent = '{0}'".format(
                _ps_quote(USER_AGENT)
            ),
            "$request.Accept = 'text/plain'",
            "$request.Timeout = {0}".format(timeout_ms),
            "$request.ReadWriteTimeout = {0}".format(timeout_ms),
        ]

        if data is not None:
            script.extend([
                "$request.Method = 'POST'",
                "$request.ContentType = '{0}'".format(
                    _ps_quote(
                        content_type or
                        "application/octet-stream"
                    )
                ),
                "$body = [System.IO.File]::ReadAllBytes('{0}')".format(
                    _ps_quote(body_path)
                ),
                "$request.ContentLength = [Int64]$body.Length",
                "$requestStream = $request.GetRequestStream()",
                "try { $requestStream.Write($body, 0, $body.Length) } finally { if ($requestStream) { $requestStream.Dispose() } }",
            ])
        else:
            script.append("$request.Method = 'GET'")

        script.extend([
            "$response = $request.GetResponse()",
            "$responseStream = $response.GetResponseStream()",
            "$outputStream = [System.IO.File]::Open('{0}', [System.IO.FileMode]::Create)".format(
                _ps_quote(output_path)
            ),
            "try { $responseStream.CopyTo($outputStream) } finally { if ($outputStream) { $outputStream.Dispose() }; if ($responseStream) { $responseStream.Dispose() }; if ($response) { $response.Close() } }",
        ])

        process = subprocess.Popen(
            [
                executable,
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "; ".join(script),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            **_hidden_process_kwargs()
        )
        stdout_value, stderr_value = process.communicate()

        if process.returncode != 0:
            raise ShareProviderError(
                "PowerShell request failed: {0}".format(
                    _as_text(stderr_value).strip() or
                    _as_text(stdout_value).strip() or
                    "exit code {0}".format(process.returncode)
                )
            )

        if not os.path.isfile(output_path):
            raise ShareProviderError(
                "PowerShell request returned no response body."
            )

        with open(output_path, "rb") as handle:
            return handle.read()

    finally:
        try:
            shutil.rmtree(directory)
        except Exception:
            pass


def _request(
    url,
    data=None,
    timeout=15,
    content_type=None
):
    powershell_error = None

    if _prefer_powershell_first():
        try:
            return _powershell_request(
                url,
                data=data,
                timeout=timeout,
                content_type=content_type
            )
        except Exception as exc:
            # Keep urllib as a safety fallback in case PowerShell is disabled
            # by local policy or unavailable on a particular workstation.
            powershell_error = exc

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/plain",
    }
    if data is not None and content_type:
        headers["Content-Type"] = content_type

    request = Request(
        url,
        data=_as_bytes(data) if data is not None else None,
        headers=headers
    )

    try:
        response = urlopen(
            request,
            timeout=timeout
        )
        try:
            return response.read()
        finally:
            try:
                response.close()
            except Exception:
                pass
    except Exception as urllib_error:
        if not _is_windows():
            raise ShareProviderError(
                "Share service request failed: {0}".format(
                    urllib_error
                )
            )

        _WINDOWS_POWERSHELL_PREFERRED[0] = True

        if powershell_error is None:
            try:
                return _powershell_request(
                    url,
                    data=data,
                    timeout=timeout,
                    content_type=content_type
                )
            except Exception as fallback_error:
                powershell_error = fallback_error

        raise ShareProviderError(
            "Share service request failed with PowerShell ({0}); "
            "Python urllib also failed ({1}).".format(
                powershell_error,
                urllib_error
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
