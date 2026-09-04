# -*- coding: utf-8 -*-
from __future__ import print_function

import io
import json
import os
import tempfile
import warnings

from ..hosts import HOST
from ..pycompat import text_type
from ..constants import CONFIG_FILENAME
from ..constants import CONFIG_PATH_ENV
from ..model import normalize_document


def config_path():
    override = os.environ.get(
        CONFIG_PATH_ENV,
        ""
    ).strip()

    if override:
        return os.path.normpath(
            override
        )

    try:
        folder = HOST.user_config_dir()
    except Exception:
        folder = os.path.expanduser("~")

    try:
        filename = HOST.config_filename()
    except Exception:
        filename = CONFIG_FILENAME

    return os.path.normpath(
        os.path.join(
            folder,
            filename
        )
    )


def load_config(path=None):
    path = path or config_path()

    if not os.path.isfile(path):
        return normalize_document({})

    try:
        with io.open(
            path,
            "r",
            encoding="utf-8"
        ) as handle:
            return normalize_document(
                json.load(handle)
            )
    except Exception as exc:
        warnings.warn(
            "Script Toolbox: failed to load config at {0!r}: {1}. "
            "Falling back to the default configuration.".format(
                path,
                exc
            ),
            RuntimeWarning,
            stacklevel=2
        )
        return normalize_document({})


def _replace_file_windows(source, destination):
    # Maya 2015 ships Python 2.7, where os.replace() is unavailable.
    # MoveFileExW provides replace-existing semantics without deleting the
    # destination first, so a failed replacement never creates a deliberate
    # no-config window.
    import ctypes

    move_file_ex = ctypes.windll.kernel32.MoveFileExW
    flags = 0x00000001 | 0x00000008  # REPLACE_EXISTING | WRITE_THROUGH

    result = move_file_ex(
        text_type(os.path.abspath(source)),
        text_type(os.path.abspath(destination)),
        flags
    )

    if not result:
        raise ctypes.WinError()


def _replace_file(source, destination):
    replace = getattr(
        os,
        "replace",
        None
    )

    if replace is not None:
        replace(
            source,
            destination
        )
        return

    if os.name == "nt":
        _replace_file_windows(
            source,
            destination
        )
        return

    # POSIX rename replaces an existing destination atomically.
    os.rename(
        source,
        destination
    )


def save_config(document, path=None):
    path = path or config_path()
    document = normalize_document(document)

    folder = os.path.dirname(path)

    if folder and not os.path.isdir(folder):
        os.makedirs(folder)

    descriptor, temp_path = tempfile.mkstemp(
        prefix=".script_toolbox_config_",
        suffix=".tmp",
        dir=(folder or ".")
    )

    try:
        with io.open(
            descriptor,
            "w",
            encoding="utf-8"
        ) as handle:
            handle.write(
                text_type(
                    json.dumps(
                        document,
                        ensure_ascii=False,
                        indent=2
                    )
                )
            )
            handle.flush()
            os.fsync(
                handle.fileno()
            )

        _replace_file(
            temp_path,
            path
        )

    except Exception:
        try:
            os.remove(
                temp_path
            )
        except OSError:
            pass

        raise

    return path


def export_config(document, path):
    return save_config(
        document,
        path=path
    )


def import_config(path):
    return load_config(
        path=path
    )
