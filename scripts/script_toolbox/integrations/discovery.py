# -*- coding: utf-8 -*-
from __future__ import print_function

import glob
import os
import re
import sys

from ..pycompat import text_type


_YEAR_VERSION_RE = re.compile(r"(?<!\d)(\d{4})(?!\d)")
_DOTTED_VERSION_RE = re.compile(r"(?<!\d)(\d{1,3}(?:\.\d+)+)(?!\d)")
_INTEGER_VERSION_RE = re.compile(r"(?<!\d)(\d{1,3})(?!\d)")


def distribution_root():
    path = os.path.abspath(__file__)
    for unused in range(4):
        path = os.path.dirname(path)
    return os.path.normpath(path)


def parse_version(value):
    value = text_type(value or "")

    match = _YEAR_VERSION_RE.search(value)
    if match is not None:
        return match.group(1)

    match = _DOTTED_VERSION_RE.search(value)
    if match is not None:
        return match.group(1)

    match = _INTEGER_VERSION_RE.search(value)
    if match is not None:
        return match.group(1)

    return ""


def version_sort_key(version):
    parts = []
    for token in re.findall(r"\d+", text_type(version or "")):
        try:
            parts.append(int(token))
        except Exception:
            parts.append(0)
    return tuple(parts)


def existing_directories(patterns):
    result = []
    seen = set()
    for pattern in patterns:
        for path in glob.glob(pattern):
            normalized = os.path.normpath(path)
            key = os.path.normcase(normalized)
            if key in seen or not os.path.isdir(normalized):
                continue
            seen.add(key)
            result.append(normalized)
    return result


def windows_documents_dir():
    if os.name != "nt":
        return ""

    try:
        import ctypes
        buffer = ctypes.create_unicode_buffer(260)
        shell32 = ctypes.windll.shell32
        result = shell32.SHGetFolderPathW(
            None,
            5,  # CSIDL_PERSONAL / Documents
            None,
            0,
            buffer
        )
        if result == 0 and buffer.value:
            return os.path.normpath(buffer.value)
    except Exception:
        pass

    home = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    return os.path.normpath(
        os.path.join(home, "Documents")
    )


def maya_user_root():
    if os.name == "nt":
        return os.path.join(
            windows_documents_dir(),
            "maya"
        )
    if sys.platform == "darwin":
        return os.path.expanduser(
            "~/Library/Preferences/Autodesk/maya"
        )
    return os.path.expanduser("~/maya")


def maya_user_config_for_version(version, user_root=None):
    root = os.path.normpath(
        user_root or maya_user_root()
    )
    version = text_type(version or "").strip()

    if os.path.isdir(root):
        candidates = []
        prefix = version.lower()
        try:
            names = os.listdir(root)
        except OSError:
            names = []
        for name in names:
            full_path = os.path.join(root, name)
            if not os.path.isdir(full_path):
                continue
            if text_type(name).lower().startswith(prefix):
                candidates.append(full_path)
        if candidates:
            candidates.sort(key=lambda p: (len(os.path.basename(p)), p))
            return os.path.normpath(candidates[0])

    return os.path.normpath(
        os.path.join(root, version)
    )


def _generic_user_home_subdir(*parts):
    return os.path.normpath(
        os.path.join(os.path.expanduser("~"), *parts)
    )


__all__ = [
    "distribution_root",
    "existing_directories",
    "maya_user_config_for_version",
    "maya_user_root",
    "parse_version",
    "version_sort_key",
    "windows_documents_dir",
]
