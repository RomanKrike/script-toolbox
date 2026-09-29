# -*- coding: utf-8 -*-
from __future__ import print_function

import io
import os
import shutil
import tempfile

from ..pycompat import text_type


def read_text(path):
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


def replace_file(source, destination):
    replace = getattr(os, "replace", None)
    if replace is not None:
        replace(source, destination)
        return
    if os.name == "nt":
        _replace_file_windows(source, destination)
        return
    os.rename(source, destination)


def atomic_write(path, content):
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
        replace_file(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def backup_once(path):
    if not os.path.isfile(path):
        return None
    backup = path + ".script_toolbox.bak"
    if not os.path.exists(backup):
        shutil.copy2(path, backup)
    return backup


def replace_marked_block(
    content,
    begin_marker,
    end_marker,
    replacement=None
):
    content = text_type(content or "")
    begin_index = content.find(begin_marker)
    end_index = content.find(end_marker)

    if begin_index >= 0 and end_index >= begin_index:
        end_index += len(end_marker)
        while (
            end_index < len(content) and
            content[end_index] in "\r\n"
        ):
            end_index += 1
        content = (
            content[:begin_index] +
            content[end_index:]
        )

    content = content.rstrip()
    if replacement:
        if content:
            content += "\n\n"
        content += text_type(replacement).rstrip()

    if content:
        content += "\n"
    return content


def contains_marked_block(path, begin_marker, end_marker):
    if not os.path.isfile(path):
        return False
    try:
        content = read_text(path)
    except Exception:
        return False
    return begin_marker in content and end_marker in content


def marked_block_state(
    path,
    begin_marker,
    end_marker,
    expected_block
):
    if not os.path.isfile(path):
        return "missing"

    try:
        content = read_text(path)
    except Exception:
        return "broken"

    if begin_marker not in content or end_marker not in content:
        return "missing"

    normalized = replace_marked_block(
        content,
        begin_marker,
        end_marker,
        expected_block
    )
    if normalized != content:
        return "stale"
    return "ok"


def write_marked_block(
    path,
    begin_marker,
    end_marker,
    replacement
):
    exists = os.path.isfile(path)
    content = read_text(path) if exists else u""
    updated = replace_marked_block(
        content,
        begin_marker,
        end_marker,
        replacement
    )
    if updated == content:
        return path
    if exists:
        backup_once(path)
    atomic_write(path, updated)
    return path


def remove_marked_block(path, begin_marker, end_marker):
    if not os.path.isfile(path):
        return path

    content = read_text(path)
    updated = replace_marked_block(
        content,
        begin_marker,
        end_marker,
        None
    )
    if updated == content:
        return path

    backup_once(path)
    atomic_write(path, updated)
    return path


__all__ = [
    "atomic_write",
    "backup_once",
    "contains_marked_block",
    "marked_block_state",
    "read_text",
    "remove_marked_block",
    "replace_marked_block",
    "write_marked_block",
]
