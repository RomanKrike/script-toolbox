# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import shutil
import socket
import ssl
import struct
import subprocess
import sys
import tempfile

try:
    import httplib
    from urllib2 import HTTPHandler
    from urllib2 import HTTPSHandler
    from urllib2 import ProxyHandler
    from urllib2 import Request
    from urllib2 import build_opener
    from urllib2 import urlopen
except ImportError:
    import http.client as httplib
    from urllib.request import HTTPHandler
    from urllib.request import HTTPSHandler
    from urllib.request import ProxyHandler
    from urllib.request import Request
    from urllib.request import build_opener
    from urllib.request import urlopen

from ..pycompat import text_type
from . import network_proxy


class TransportError(RuntimeError):
    """Predictable error raised by the shared HTTP transport."""

    def __init__(self, message, kind="network"):
        RuntimeError.__init__(self, message)
        self.kind = kind


_WINDOWS_POWERSHELL_PREFERRED = [False]
_AUTH_ENV = "SCRIPT_TOOLBOX_HTTP_AUTHORIZATION"
_PROXY_USER_ENV = "SCRIPT_TOOLBOX_PROXY_USERNAME"
_PROXY_PASSWORD_ENV = "SCRIPT_TOOLBOX_PROXY_PASSWORD"


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


def _resolve_proxy_config(proxy_config=None):
    if proxy_config is None:
        config = network_proxy.load_proxy_config()
    elif isinstance(proxy_config, network_proxy.ProxyConfig):
        config = proxy_config
    else:
        config = network_proxy.ProxyConfig.from_dict(proxy_config or {})
    config.validate()
    network_proxy.log_proxy_config(config)
    return config


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


def _powershell_web_proxy(script, proxy_uri, username, password, child_env):
    script.append(
        "$proxy = New-Object System.Net.WebProxy('{0}')".format(
            powershell_quote(proxy_uri)
        )
    )
    child_env.pop(_PROXY_USER_ENV, None)
    child_env.pop(_PROXY_PASSWORD_ENV, None)

    if username is not None or password is not None:
        child_env[_PROXY_USER_ENV] = text_type(username or "")
        child_env[_PROXY_PASSWORD_ENV] = text_type(password or "")
        script.extend([
            "$proxyUser = $env:{0}".format(_PROXY_USER_ENV),
            "$proxyPassword = $env:{0}".format(_PROXY_PASSWORD_ENV),
            (
                "$proxy.Credentials = New-Object System.Net.NetworkCredential("
                "$proxyUser, $proxyPassword)"
            ),
        ])
    script.append("$request.Proxy = $proxy")


def _apply_powershell_proxy(script, url, proxy_config, child_env):
    config = _resolve_proxy_config(proxy_config)

    child_env.pop(_PROXY_USER_ENV, None)
    child_env.pop(_PROXY_PASSWORD_ENV, None)

    if config.mode == network_proxy.PROXY_MODE_NONE:
        script.append("$request.Proxy = $null")
        return

    if config.mode == network_proxy.PROXY_MODE_SYSTEM:
        selected = network_proxy.system_proxy_for_url(url)
        if selected == "":
            script.append("$request.Proxy = $null")
            return
        if selected:
            parsed = network_proxy.parse_proxy_uri(selected)
            if (
                parsed is not None and
                parsed.proxy_type == network_proxy.PROXY_TYPE_SOCKS5
            ):
                raise TransportError(
                    "SOCKS5 system proxy requires the Python transport.",
                    kind="proxy_unsupported"
                )
            if parsed is not None:
                _powershell_web_proxy(
                    script,
                    parsed.proxy_uri(include_credentials=False),
                    parsed.username if parsed.requires_auth else None,
                    parsed.password if parsed.requires_auth else None,
                    child_env
                )
        return

    if config.is_socks5:
        raise TransportError(
            "SOCKS5 proxy requires the Python transport.",
            kind="proxy_unsupported"
        )

    _powershell_web_proxy(
        script,
        config.proxy_uri(include_credentials=False),
        config.username if config.requires_auth else None,
        config.password if config.requires_auth else None,
        child_env
    )


def _powershell_transfer(
    url,
    destination,
    data=None,
    headers=None,
    timeout=15,
    method=None,
    proxy_config=None
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

    _apply_powershell_proxy(
        script,
        url,
        proxy_config,
        child_env
    )
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
            config = _resolve_proxy_config(proxy_config)
            detail = network_proxy.redact_text(detail, config)
            kind = _classify_error_kind(detail, config)
            raise TransportError(
                "PowerShell request failed: {0}".format(detail),
                kind=kind
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
    method=None,
    proxy_config=None
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
            method=method,
            proxy_config=proxy_config
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
    timeout=30,
    proxy_config=None
):
    return _powershell_transfer(
        url,
        destination,
        headers=headers,
        timeout=timeout,
        method="GET",
        proxy_config=proxy_config
    )


def _recv_exact(sock, size):
    chunks = []
    remaining = int(size)
    while remaining:
        chunk = sock.recv(remaining)
        if not chunk:
            raise TransportError(
                "SOCKS5 proxy closed the connection unexpectedly.",
                kind="proxy_connection"
            )
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _socks_address(host):
    try:
        packed = socket.inet_pton(socket.AF_INET, host)
        return b"\x01" + packed
    except Exception:
        pass

    if getattr(socket, "AF_INET6", None) is not None:
        try:
            packed = socket.inet_pton(socket.AF_INET6, host)
            return b"\x04" + packed
        except Exception:
            pass

    encoded = _as_bytes(host)
    if len(encoded) > 255:
        raise TransportError(
            "SOCKS5 destination hostname is too long.",
            kind="dns"
        )
    return b"\x03" + struct.pack("!B", len(encoded)) + encoded


def _socks5_connect(config, destination_host, destination_port, timeout):
    config.validate()
    try:
        sock = socket.create_connection(
            (config.host, config.port),
            timeout
        )
    except socket.timeout:
        raise TransportError(
            "Connection to the proxy server timed out.",
            kind="timeout"
        )
    except Exception as exc:
        raise TransportError(
            "Unable to connect to proxy server: {0}".format(
                network_proxy.redact_text(_as_text(exc), config)
            ),
            kind="proxy_connection"
        )

    try:
        if config.requires_auth:
            methods = b"\x00\x02"
        else:
            methods = b"\x00"

        sock.sendall(
            b"\x05" +
            struct.pack("!B", len(methods)) +
            methods
        )
        response = _recv_exact(sock, 2)
        if response[0:1] != b"\x05":
            raise TransportError(
                "Invalid SOCKS5 proxy response.",
                kind="proxy_connection"
            )

        selected = response[1]
        if not isinstance(selected, int):
            selected = ord(selected)

        if selected == 0xFF:
            raise TransportError(
                "SOCKS5 proxy rejected the supported authentication methods.",
                kind="proxy_auth"
            )

        if selected == 0x02:
            username = _as_bytes(config.username)
            password = _as_bytes(config.password)
            if len(username) > 255 or len(password) > 255:
                raise TransportError(
                    "SOCKS5 username/password is too long.",
                    kind="proxy_auth"
                )
            auth_request = (
                b"\x01" +
                struct.pack("!B", len(username)) +
                username +
                struct.pack("!B", len(password)) +
                password
            )
            sock.sendall(auth_request)
            auth_response = _recv_exact(sock, 2)
            auth_status = auth_response[1]
            if not isinstance(auth_status, int):
                auth_status = ord(auth_status)
            if auth_status != 0:
                raise TransportError(
                    "Proxy authentication required or credentials were rejected.",
                    kind="proxy_auth"
                )
        elif selected != 0x00:
            raise TransportError(
                "SOCKS5 proxy selected an unsupported authentication method.",
                kind="proxy_auth"
            )

        request = (
            b"\x05\x01\x00" +
            _socks_address(destination_host) +
            struct.pack("!H", int(destination_port))
        )
        sock.sendall(request)

        header = _recv_exact(sock, 4)
        status = header[1]
        atyp = header[3]
        if not isinstance(status, int):
            status = ord(status)
        if not isinstance(atyp, int):
            atyp = ord(atyp)

        if status != 0:
            status_messages = {
                1: "general SOCKS5 failure",
                2: "connection not allowed",
                3: "network unreachable",
                4: "host unreachable",
                5: "connection refused",
                6: "TTL expired",
                7: "command not supported",
                8: "address type not supported",
            }
            raise TransportError(
                "SOCKS5 proxy connection failed: {0}.".format(
                    status_messages.get(
                        status,
                        "error {0}".format(status)
                    )
                ),
                kind="proxy_connection"
            )

        if atyp == 1:
            _recv_exact(sock, 4)
        elif atyp == 4:
            _recv_exact(sock, 16)
        elif atyp == 3:
            length_value = _recv_exact(sock, 1)[0]
            if not isinstance(length_value, int):
                length_value = ord(length_value)
            _recv_exact(sock, length_value)
        else:
            raise TransportError(
                "Invalid SOCKS5 address type in proxy response.",
                kind="proxy_connection"
            )
        _recv_exact(sock, 2)
        return sock
    except Exception:
        try:
            sock.close()
        except Exception:
            pass
        raise


class _SocksHTTPConnection(httplib.HTTPConnection):
    def __init__(self, host, proxy_config, **kwargs):
        self._script_toolbox_proxy = proxy_config
        httplib.HTTPConnection.__init__(self, host, **kwargs)

    def connect(self):
        self.sock = _socks5_connect(
            self._script_toolbox_proxy,
            self.host,
            self.port,
            self.timeout
        )


class _SocksHTTPSConnection(httplib.HTTPSConnection):
    def __init__(self, host, proxy_config, **kwargs):
        self._script_toolbox_proxy = proxy_config
        httplib.HTTPSConnection.__init__(self, host, **kwargs)

    def connect(self):
        raw_sock = _socks5_connect(
            self._script_toolbox_proxy,
            self.host,
            self.port,
            self.timeout
        )

        context = getattr(self, "_context", None)
        if context is None and hasattr(ssl, "create_default_context"):
            context = ssl.create_default_context()

        if context is not None:
            try:
                self.sock = context.wrap_socket(
                    raw_sock,
                    server_hostname=self.host
                )
            except TypeError:
                self.sock = context.wrap_socket(raw_sock)
        else:
            self.sock = ssl.wrap_socket(raw_sock)


class _SocksHTTPHandler(HTTPHandler):
    def __init__(self, proxy_config):
        HTTPHandler.__init__(self)
        self.proxy_config = proxy_config

    def http_open(self, request):
        proxy_config = self.proxy_config

        def factory(host, **kwargs):
            return _SocksHTTPConnection(
                host,
                proxy_config,
                **kwargs
            )
        return self.do_open(factory, request)


class _SocksHTTPSHandler(HTTPSHandler):
    def __init__(self, proxy_config):
        HTTPSHandler.__init__(self)
        self.proxy_config = proxy_config

    def https_open(self, request):
        proxy_config = self.proxy_config

        def factory(host, **kwargs):
            return _SocksHTTPSConnection(
                host,
                proxy_config,
                **kwargs
            )

        kwargs = {}
        if hasattr(self, "_context"):
            kwargs["context"] = self._context
        if hasattr(self, "_check_hostname"):
            kwargs["check_hostname"] = self._check_hostname
        return self.do_open(factory, request, **kwargs)


def _urllib_opener(config):
    if config.mode == network_proxy.PROXY_MODE_SYSTEM:
        return None

    if config.mode == network_proxy.PROXY_MODE_NONE:
        return build_opener(ProxyHandler({}))

    if config.is_socks5:
        return build_opener(
            ProxyHandler({}),
            _SocksHTTPHandler(config),
            _SocksHTTPSHandler(config)
        )

    uri = config.proxy_uri(include_credentials=True)
    return build_opener(
        ProxyHandler({
            "http": uri,
            "https": uri,
        })
    )


def _urllib_response(
    url,
    data=None,
    headers=None,
    timeout=15,
    method=None,
    proxy_config=None
):
    config = _resolve_proxy_config(proxy_config)
    request = Request(
        url,
        data=_as_bytes(data) if data is not None else None,
        headers=_normalized_headers(headers)
    )
    requested_method = _request_method(data, method)
    derived_method = "POST" if data is not None else "GET"
    if requested_method != derived_method:
        request.get_method = lambda: requested_method

    opener = _urllib_opener(config)
    try:
        if opener is None:
            return urlopen(request, timeout=timeout)
        return opener.open(request, timeout=timeout)
    except TransportError:
        raise
    except socket.timeout as exc:
        raise TransportError(
            "Connection timed out: {0}".format(_as_text(exc)),
            kind="timeout"
        )
    except ssl.SSLError as exc:
        raise TransportError(
            "SSL certificate verification failed: {0}".format(
                network_proxy.redact_text(_as_text(exc), config)
            ),
            kind="ssl"
        )
    except Exception as exc:
        detail = network_proxy.redact_text(_as_text(exc), config)
        raise TransportError(
            detail,
            kind=_classify_error_kind(detail, config)
        )


def _urllib_request_bytes(
    url,
    data=None,
    headers=None,
    timeout=15,
    method=None,
    proxy_config=None
):
    response = _urllib_response(
        url,
        data=data,
        headers=headers,
        timeout=timeout,
        method=method,
        proxy_config=proxy_config
    )
    try:
        return response.read()
    finally:
        try:
            response.close()
        except Exception:
            pass


def _urllib_download(
    url,
    destination,
    headers=None,
    timeout=30,
    proxy_config=None
):
    response = _urllib_response(
        url,
        headers=headers,
        timeout=timeout,
        method="GET",
        proxy_config=proxy_config
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


def _prefer_powershell(prefer_powershell, proxy_config=None):
    config = _resolve_proxy_config(proxy_config)

    if config.is_socks5:
        return False

    if config.mode == network_proxy.PROXY_MODE_SYSTEM:
        selected = network_proxy.system_proxy_for_url(
            "https://api.github.com/"
        )
        if selected:
            parsed = network_proxy.parse_proxy_uri(selected)
            if (
                parsed is not None and
                parsed.proxy_type == network_proxy.PROXY_TYPE_SOCKS5
            ):
                return False

    if prefer_powershell is None:
        return prefer_powershell_first()
    return bool(prefer_powershell) and is_windows()


def _classify_error_kind(detail, config=None):
    lower = _as_text(detail).lower()
    if "407" in lower or "proxy authentication" in lower:
        return "proxy_auth"
    if "timed out" in lower or "timeout" in lower:
        return "timeout"
    if (
        "certificate" in lower or
        "ssl" in lower or
        "tls" in lower
    ):
        return "ssl"
    if (
        "name or service not known" in lower or
        "getaddrinfo" in lower or
        "nodename nor servname" in lower
    ):
        return "dns"
    if config is not None and config.mode == network_proxy.PROXY_MODE_MANUAL:
        if (
            "refused" in lower or
            "proxy" in lower or
            "connect" in lower
        ):
            return "proxy_connection"
    return "network"


def user_error_message(error, proxy_config=None):
    config = _resolve_proxy_config(proxy_config)
    kind = getattr(error, "kind", None)
    detail = network_proxy.redact_text(_as_text(error), config)
    if kind == "proxy_auth":
        return "Proxy authentication required. Check username and password."
    if kind == "proxy_connection":
        return "Unable to connect to the configured proxy server."
    if kind == "proxy_unsupported":
        return "The selected proxy type is unavailable in this runtime."
    if kind == "timeout":
        return "Connection timed out."
    if kind == "ssl":
        return "SSL certificate verification failed."
    if kind == "dns":
        return "Unable to resolve the network host."
    if config.mode == network_proxy.PROXY_MODE_MANUAL:
        return "Could not connect through the configured proxy: {0}".format(
            detail
        )
    return "Network request failed: {0}".format(detail)


def _transport_failure(action, urllib_error, powershell_error, proxy_config=None):
    config = _resolve_proxy_config(proxy_config)
    if urllib_error is None:
        detail = network_proxy.redact_text(
            _as_text(powershell_error),
            config
        )
        return TransportError(
            "{0} failed with PowerShell ({1}).".format(
                action,
                detail
            ),
            kind=getattr(powershell_error, "kind", "network")
        )
    if powershell_error is None:
        detail = network_proxy.redact_text(
            _as_text(urllib_error),
            config
        )
        return TransportError(
            "{0} failed with Python urllib ({1}).".format(
                action,
                detail
            ),
            kind=getattr(urllib_error, "kind", "network")
        )

    urllib_detail = network_proxy.redact_text(
        _as_text(urllib_error),
        config
    )
    powershell_detail = network_proxy.redact_text(
        _as_text(powershell_error),
        config
    )
    kind = getattr(urllib_error, "kind", None)
    if kind in (None, "network"):
        kind = getattr(powershell_error, "kind", "network")
    return TransportError(
        "{0} failed with Python urllib ({1}); PowerShell ({2}).".format(
            action,
            urllib_detail,
            powershell_detail
        ),
        kind=kind
    )


def request_bytes(
    url,
    data=None,
    headers=None,
    timeout=15,
    method=None,
    prefer_powershell=None,
    proxy_config=None
):
    powershell_error = None
    urllib_error = None
    explicit_proxy_config = proxy_config is not None
    config = _resolve_proxy_config(proxy_config)

    use_powershell = _prefer_powershell(
        prefer_powershell,
        proxy_config=config
    )
    if use_powershell:
        try:
            return powershell_request(
                url,
                data=data,
                headers=headers,
                timeout=timeout,
                method=method,
                proxy_config=config
            )
        except Exception as exc:
            powershell_error = exc

    try:
        urllib_kwargs = {
            "data": data,
            "headers": headers,
            "timeout": timeout,
            "method": method,
        }
        if explicit_proxy_config:
            urllib_kwargs["proxy_config"] = config
        return _urllib_request_bytes(
            url,
            **urllib_kwargs
        )
    except Exception as exc:
        urllib_error = exc

    if not is_windows() or config.is_socks5:
        raise _transport_failure(
            "HTTP request",
            urllib_error,
            None,
            proxy_config=config
        )

    if powershell_error is None:
        try:
            result = powershell_request(
                url,
                data=data,
                headers=headers,
                timeout=timeout,
                method=method,
                proxy_config=config
            )
        except Exception as exc:
            powershell_error = exc
        else:
            _WINDOWS_POWERSHELL_PREFERRED[0] = True
            return result

    raise _transport_failure(
        "HTTP request",
        urllib_error,
        powershell_error,
        proxy_config=config
    )


def download_file(
    url,
    destination,
    headers=None,
    timeout=30,
    prefer_powershell=None,
    proxy_config=None
):
    powershell_error = None
    urllib_error = None
    explicit_proxy_config = proxy_config is not None
    config = _resolve_proxy_config(proxy_config)

    use_powershell = _prefer_powershell(
        prefer_powershell,
        proxy_config=config
    )
    if use_powershell:
        try:
            return powershell_download(
                url,
                destination,
                headers=headers,
                timeout=timeout,
                proxy_config=config
            )
        except Exception as exc:
            powershell_error = exc

    try:
        urllib_kwargs = {
            "headers": headers,
            "timeout": timeout,
        }
        if explicit_proxy_config:
            urllib_kwargs["proxy_config"] = config
        return _urllib_download(
            url,
            destination,
            **urllib_kwargs
        )
    except Exception as exc:
        urllib_error = exc

    if not is_windows() or config.is_socks5:
        raise _transport_failure(
            "HTTP download",
            urllib_error,
            None,
            proxy_config=config
        )

    if powershell_error is None:
        try:
            result = powershell_download(
                url,
                destination,
                headers=headers,
                timeout=timeout,
                proxy_config=config
            )
        except Exception as exc:
            powershell_error = exc
        else:
            _WINDOWS_POWERSHELL_PREFERRED[0] = True
            return result

    raise _transport_failure(
        "HTTP download",
        urllib_error,
        powershell_error,
        proxy_config=config
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
    "user_error_message",
]
