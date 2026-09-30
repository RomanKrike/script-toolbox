# -*- coding: utf-8 -*-
"""Bounded filesystem discovery in an isolated interpreter, without host APIs."""
from __future__ import print_function

import json
import os
import re
import subprocess
import sys
import tempfile
import time

from ..pycompat import text_type
from .base import DccInstallation, IntegrationStatus
from .discovery import distribution_root

DEFAULT_SCAN_TIMEOUT = 15.0


class DiscoveryError(RuntimeError):
    pass


def interpreter_command():
    explicit = os.environ.get("SCRIPT_TOOLBOX_DISCOVERY_PYTHON")
    if explicit:
        return [explicit]
    root = distribution_root()
    name = os.path.basename(sys.executable).lower()
    candidates = [os.path.join(root, "runtime", "python.exe"),
                  os.path.join(root, "runtime", "python")]
    if re.match(r"^(python(?:w|\d+(?:\.\d+)?)?|mayapy|hython)(?:\.exe)?$", name):
        candidates.insert(0, sys.executable)
    candidates.extend([os.path.join(sys.prefix, "python.exe"),
                       os.path.join(sys.prefix, "bin", "python"),
                       os.path.join(os.path.dirname(sys.executable), "mayapy.exe"),
                       os.path.join(os.path.dirname(sys.executable), "mayapy"),
                       os.path.join(os.path.dirname(sys.executable), "hython.exe"),
                       os.path.join(os.path.dirname(sys.executable), "hython")])
    for candidate in candidates:
        if candidate.startswith(("\\\\", "//")):
            continue
        if os.name == "nt":
            import ctypes
            drive = os.path.splitdrive(os.path.abspath(candidate))[0]
            if drive and ctypes.windll.kernel32.GetDriveTypeW(text_type(drive) + u"\\") == 4:
                continue
        if os.path.isfile(candidate):
            return [candidate]
    raise DiscoveryError("No isolated Python runtime for DCC discovery. Use the shared portable "
                         "distribution or set SCRIPT_TOOLBOX_DISCOVERY_PYTHON to a Python executable.")


def encode_snapshot(snapshot):
    result = {"roots": snapshot["roots"], "installations": {}}
    for dcc, targets in snapshot["installations"].items():
        result["installations"][dcc] = [dict(target.to_dict(),
            scanned_status=target.scanned_status.to_dict(),
            scanned_options=target.scanned_options) for target in targets]
    return result


def decode_snapshot(snapshot):
    installations = {}
    for dcc, records in snapshot["installations"].items():
        targets = []
        for record in records:
            record = dict(record)
            status = record.pop("scanned_status")
            options = record.pop("scanned_options")
            record.pop("integration_status", None)
            target = DccInstallation(**record)
            target.scanned_status = IntegrationStatus(**status)
            target.integration_status = target.scanned_status.state
            target.scanned_options = options
            targets.append(target)
        installations[dcc] = targets
    return {"installations": installations, "roots": snapshot["roots"]}


def scan_in_process(request, cancel_event=None, timeout=DEFAULT_SCAN_TIMEOUT,
                    command=None, worker_path=None):
    if timeout <= 0:
        raise ValueError("Discovery timeout must be positive.")
    worker_path = worker_path or os.path.join(os.path.dirname(__file__), "discovery_worker.py")
    directory = tempfile.mkdtemp(prefix="stb_scan_")
    request_path = os.path.join(directory, "request.json")
    result_path = os.path.join(directory, "result.json")
    log_path = os.path.join(directory, "worker.log")
    process = None
    clock = getattr(time, "monotonic", time.time)
    started = clock()
    try:
        with open(request_path, "w") as handle:
            json.dump(request, handle)
        argv = list(command or interpreter_command()) + [worker_path, request_path, result_path]
        environment = dict(os.environ)
        environment["SCRIPT_TOOLBOX_DISCOVERY_WORKER"] = "1"
        # A DCC may set these for its own embedded Python. Let the selected
        # interpreter resolve its own standard library instead.
        environment.pop("PYTHONHOME", None)
        environment.pop("PYTHONPATH", None)
        kwargs = {}
        if os.name == "nt":
            kwargs["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
        with open(log_path, "wb") as log:
            process = subprocess.Popen(argv, env=environment, stdout=log, stderr=log, **kwargs)
            while process.poll() is None:
                if cancel_event is not None and cancel_event.is_set():
                    raise DiscoveryError("DCC discovery cancelled.")
                if clock() - started >= timeout:
                    raise DiscoveryError("DCC discovery timed out after {0:g} seconds. "
                                         "Check unavailable custom/network profile paths.".format(timeout))
                time.sleep(0.025)
            if process.returncode:
                with open(log_path, "rb") as handle:
                    detail = handle.read(4096).decode("utf-8", "replace")
                raise DiscoveryError("DCC discovery process failed: " + detail)
        if os.path.getsize(result_path) > 4 * 1024 * 1024:
            raise DiscoveryError("DCC discovery returned an oversized result.")
        with open(result_path, "rb") as handle:
            return decode_snapshot(json.loads(handle.read().decode("utf-8")))
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait()
        import shutil
        shutil.rmtree(directory)


__all__ = ["DiscoveryError", "scan_in_process", "DEFAULT_SCAN_TIMEOUT"]
