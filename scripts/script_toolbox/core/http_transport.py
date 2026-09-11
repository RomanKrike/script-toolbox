# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import shutil
import subprocess
import sys
import tempfile

try:
    from urllib2 import Request
    from urllib2 import urlopen
except ImportError:
    from urllib.request import Request
    from urllib.request import urlopen

from ..pycompat import text_type


class TransportError(RuntimeError):
    """Predictable error raised by the shared HTTP transport."""


_WINDOWS_POWERSHELL_PREFERRED = [False]
_AUTH_ENV = "SCRIPT_TOOLBOX_HTTP_AUTHORIZATION"


def _as_bytes(value):
    if isinstance(value, bytes):
        return value
    return text_type(value).encode("utf-8")


def _as_text(value):
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return text_type(value)


def is_windows():
    return os.name == "nt"


def legacy_windows_python():
    return is_windows() and sys.version_info[0] < 3


def prefer_powershell_first():
    return is_windows() and (
        legacy_windows_python() or
        _WINDOWS_POWERSHELL_PREFERRED[0]
    )


def powershell_executable():
    if not is_windows():
        return None

    root = os.environ.get("SystemRoot", r"C:\Windows")
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


def powershell_quote(value):
    return text_type(value or "").replace("'", "''")


def hidden_process_kwargs():
    if not is_windows():
        return {}

    result = {
        # CREATE_NO_WINDOW. Numeric form is available on Python 2.7 builds
        # that do not expose subprocess.CREATE_NO_WINDOW.
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


def _normalized_headers(headers):
    result = {}
    for name, value in (headers or {}).items():
        if value is None:
            continue
        result[text_type(name)] = text_type(value)
    return result


def _request_method(data, method):
    if method:
        return text_type(method).upper()
    return "POST" if data is not None else "GET"


def _apply_powershell_headers(script, headers, child_env):
    headers = _normalized_headers(headers)
    authorization = None

    for name in sorted(headers.keys(), key=lambda value: value.lower()):
        value = headers[name]
        lower_name = name.lower()

        if lower_name == "user-agent":
            script.append(
                "$request.UserAgent = '{0}'".format(
                    powershell_quote(value)
                )
            )
        elif lower_name == "accept":
            script.append(
                "$request.Accept = '{0}'".format(
                    powershell_quote(value)
                )
            )
        elif lower_name == "content-type":
            script.append(
                "$request.ContentType = '{0}'".format(
                    powershell_quote(value)
                )
            )
        elif lower_name == "authorization":
            authorization = value
        else:
            script.append(
                "$request.Headers['{0}'] = '{1}'".format(
                    powershell_quote(name),
                    powershell_quote(value)
                )
            )

    child_env.pop(_AUTH_ENV, None)
    if authorization:
        child_env[_AUTH_ENV] = authorization
        script.extend([
            "$authorization = $env:{0}".format(_AUTH_ENV),
            "if ($authorization) { $request.Headers['Authorization'] = $authorization }",
        ])


def _powershell_transfer(
    url,
    destination,
    data=None,
    headers=None,
    timeout=15,
    method=None
):
    executable = powershell_executable()
    if not executable:
        raise TransportError("PowerShell transport is unavailable.")

    directory = None
    body_path = None
    if data is not None:
        directory = tempfile.mkdtemp(prefix="script_toolbox_http_")
        body_path = os.path.join(directory, "request.bin")
        with open(body_path, "wb") as handle:
            handle.write(_as_bytes(data))

    timeout_ms = max(1000, int(float(timeout) * 1000.0))
    child_env = os.environ.copy()
    script = [
        "$ErrorActionPreference = 'Stop'",
        "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12",
        "$request = [System.Net.HttpWebRequest]::Create('{0}')".format(
            powershell_quote(url)
        ),
        "$request.Method = '{0}'".format(
            powershell_quote(_request_method(data, method))
        ),
        "$request.Timeout = {0}".format(timeout_ms),
        "$request.ReadWriteTimeout = {0}".format(timeout_ms),
    ]
    _apply_powershell_headers(script, headers, child_env)

    if data is not None:
        script.extend([
            "$body = [System.IO.File]::ReadAllBytes('{0}')".format(
                powershell_quote(body_path)
            ),
            "$request.ContentLength = [Int64]$body.Length",
            "$requestStream = $request.GetRequestStream()",
            (
                "try { $requestStream.Write($body, 0, $body.Length) } "
                "finally { if ($requestStream -ne $null) { $requestStream.Close() } }"
            ),
        ])

    destination_ps = powershell_quote(destination)
    transfer_block = (
        "try { "
        "$response = $request.GetResponse(); "
        "$responseStream = $response.GetResponseStream(); "
        "$output = [System.IO.File]::Open('" +
        destination_ps +
        "', [System.IO.FileMode]::Create); "
        "$buffer = New-Object byte[] 65536; "
        "while (($readCount = $responseStream.Read($buffer, 0, $buffer.Length)) -gt 0) { "
        "$output.Write($buffer, 0, $readCount) "
        "} "
        "} catch { "
        "$transferError = $_.Exception.Message "
        "} finally { "
        "if ($output -ne $null) { $output.Close() }; "
        "if ($responseStream -ne $null) { $responseStream.Close() }; "
        "if ($response -ne $null) { $response.Close() } "
        "}"
    )

    script.extend([
        "$response = $null",
        "$responseStream = $null",
        "$output = $null",
        "$transferError = $null",
        transfer_block,
        "if ($transferError) { [Console]::Error.WriteLine($transferError); exit 1 }",
    ])

    try:
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
            env=child_env,
            **hidden_process_kwargs()
        )
        stdout_value, stderr_value = process.communicate()

        if process.returncode != 0:
            detail = (
                _as_text(stderr_value).strip() or
                _as_text(stdout_value).strip() or
                "exit code {0}".format(process.returncode)
            )
            raise TransportError(
                "PowerShell request failed: {0}".format(detail)
            )

        if not os.path.isfile(destination):
            raise TransportError(
                "PowerShell request did not create the destination file."
            )

        return destination
    finally:
        if directory:
            try:
                shutil.rmtree(directory)
            except Exception:
                pass


def powershell_request(
    url,
    data=None,
    headers=None,
    timeout=15,
    method=None
):
    directory = tempfile.mkdtemp(prefix="script_toolbox_http_response_")
    output_path = os.path.join(directory, "response.bin")
    try:
        _powershell_transfer(
            url,
            output_path,
            data=data,
            headers=headers,
            timeout=timeout,
            method=method
        )
        with open(output_path, "rb") as handle:
            return handle.read()
    finally:
        try:
            shutil.rmtree(directory)
        except Exception:
            pass


def powershell_download(
    url,
    destination,
    headers=None,
    timeout=30
):
    return _powershell_transfer(
        url,
        destination,
        headers=headers,
        timeout=timeout,
        method="GET"
    )


def _urllib_response(url, data=None, headers=None, timeout=15, method=None):
    request = Request(
        url,
        data=_as_bytes(data) if data is not None else None,
        headers=_normalized_headers(headers)
    )
    # urllib2.Request on Python 2.7 has no method argument. The supported
    # shared callers use GET/POST, which Request derives from data presence.
    requested_method = _request_method(data, method)
    derived_method = "POST" if data is not None else "GET"
    if requested_method != derived_method:
        request.get_method = lambda: requested_method
    return urlopen(request, timeout=timeout)


def _urllib_request_bytes(url, data=None, headers=None, timeout=15, method=None):
    response = _urllib_response(
        url,
        data=data,
        headers=headers,
        timeout=timeout,
        method=method
    )
    try:
        return response.read()
    finally:
        try:
            response.close()
        except Exception:
            pass


def _urllib_download(url, destination, headers=None, timeout=30):
    response = _urllib_response(
        url,
        headers=headers,
        timeout=timeout,
        method="GET"
    )
    try:
        with open(destination, "wb") as handle:
            while True:
                chunk = response.read(1024 * 256)
                if not chunk:
                    break
                handle.write(chunk)
    finally:
        try:
            response.close()
        except Exception:
            pass
    return destination


def _prefer_powershell(prefer_powershell):
    if prefer_powershell is None:
        return prefer_powershell_first()
    return bool(prefer_powershell) and is_windows()


def _transport_failure(action, urllib_error, powershell_error):
    if urllib_error is None:
        return TransportError(
            "{0} failed with PowerShell ({1}).".format(
                action,
                _as_text(powershell_error)
            )
        )
    if powershell_error is None:
        return TransportError(
            "{0} failed with Python urllib ({1}).".format(
                action,
                _as_text(urllib_error)
            )
        )
    return TransportError(
        "{0} failed with Python urllib ({1}); PowerShell ({2}).".format(
            action,
            _as_text(urllib_error),
            _as_text(powershell_error)
        )
    )


def request_bytes(
    url,
    data=None,
    headers=None,
    timeout=15,
    method=None,
    prefer_powershell=None
):
    powershell_error = None
    urllib_error = None

    if _prefer_powershell(prefer_powershell):
        try:
            return powershell_request(
                url,
                data=data,
                headers=headers,
                timeout=timeout,
                method=method
            )
        except Exception as exc:
            powershell_error = exc

    try:
        return _urllib_request_bytes(
            url,
            data=data,
            headers=headers,
            timeout=timeout,
            method=method
        )
    except Exception as exc:
        urllib_error = exc

    if not is_windows():
        raise _transport_failure(
            "HTTP request",
            urllib_error,
            None
        )

    if powershell_error is None:
        try:
            result = powershell_request(
                url,
                data=data,
                headers=headers,
                timeout=timeout,
                method=method
            )
        except Exception as exc:
            powershell_error = exc
        else:
            _WINDOWS_POWERSHELL_PREFERRED[0] = True
            return result

    raise _transport_failure(
        "HTTP request",
        urllib_error,
        powershell_error
    )


def download_file(
    url,
    destination,
    headers=None,
    timeout=30,
    prefer_powershell=None
):
    powershell_error = None
    urllib_error = None

    if _prefer_powershell(prefer_powershell):
        try:
            return powershell_download(
                url,
                destination,
                headers=headers,
                timeout=timeout
            )
        except Exception as exc:
            powershell_error = exc

    try:
        return _urllib_download(
            url,
            destination,
            headers=headers,
            timeout=timeout
        )
    except Exception as exc:
        urllib_error = exc

    if not is_windows():
        raise _transport_failure(
            "HTTP download",
            urllib_error,
            None
        )

    if powershell_error is None:
        try:
            result = powershell_download(
                url,
                destination,
                headers=headers,
                timeout=timeout
            )
        except Exception as exc:
            powershell_error = exc
        else:
            _WINDOWS_POWERSHELL_PREFERRED[0] = True
            return result

    raise _transport_failure(
        "HTTP download",
        urllib_error,
        powershell_error
    )


__all__ = [
    "TransportError",
    "download_file",
    "hidden_process_kwargs",
    "is_windows",
    "legacy_windows_python",
    "powershell_download",
    "powershell_executable",
    "powershell_quote",
    "powershell_request",
    "prefer_powershell_first",
    "request_bytes",
]
