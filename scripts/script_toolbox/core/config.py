# -*- coding: utf-8 -*-
from __future__ import print_function

import io
import json
import os
import shutil
import tempfile
import warnings

from ..pycompat import text_type
from ..model import create_item
from ..model import normalize_document
from .config_schema import ConfigSchemaError
from .config_schema import validate_document_schema
from .logging_utils import get_logger
from .user_paths import config_path


CONFIG_BACKUP_COUNT = 3
_LOGGER = get_logger()


class ConfigRecoveryRequired(RuntimeError):

    def __init__(
        self,
        path,
        cause,
        backups=None
    ):
        self.path = os.path.normpath(
            path
        )
        self.cause = text_type(
            cause
        )
        self.backups = list(
            backups or []
        )

        message = (
            "Script Toolbox configuration at {0!r} cannot be read safely: "
            "{1}"
        ).format(
            self.path,
            self.cause
        )

        RuntimeError.__init__(
            self,
            message
        )


def backup_path(
    path,
    index
):
    return "{0}.bak{1}".format(
        os.path.normpath(path),
        int(index)
    )


def _prepare_document(document):
    return normalize_document(
        validate_document_schema(
            document
        )
    )


def serialize_config(document):
    """Return the canonical UTF-8 JSON text representation of a config."""
    document = _prepare_document(
        document
    )
    return text_type(
        json.dumps(
            document,
            ensure_ascii=False,
            indent=2
        )
    )


def deserialize_config(data):
    """Parse and validate config JSON text using the normal load pipeline."""
    raw_document = json.loads(
        text_type(data)
    )

    if (
        not isinstance(raw_document, dict) or
        not raw_document or
        "version" not in raw_document or
        "sections" not in raw_document or
        not isinstance(raw_document.get("sections"), list)
    ):
        raise ConfigSchemaError(
            "Unsupported Script Toolbox config format."
        )

    return _prepare_document(
        raw_document
    )


def deserialize_transfer(data):
    """Parse clipboard transfer JSON as a full config or a single Item."""
    raw = json.loads(
        text_type(data)
    )

    if not isinstance(raw, dict) or not raw:
        raise ConfigSchemaError(
            "Unsupported Script Toolbox transfer format."
        )

    if "version" in raw or "sections" in raw:
        if (
            "version" not in raw or
            "sections" not in raw or
            not isinstance(raw.get("sections"), list)
        ):
            raise ConfigSchemaError(
                "Unsupported Script Toolbox config format."
            )
        return (
            "config",
            _prepare_document(raw)
        )

    kind = text_type(
        raw.get("kind") or ""
    ).lower()
    if kind:
        return (
            "item",
            create_item(
                kind,
                raw
            )
        )

    raise ConfigSchemaError(
        "Unsupported Script Toolbox transfer format."
    )


def _read_document(path):
    with io.open(
        path,
        "r",
        encoding="utf-8"
    ) as handle:
        raw_text = handle.read()

    return deserialize_config(
        raw_text
    )


def valid_backup_paths(
    path,
    count=CONFIG_BACKUP_COUNT
):
    result = []

    for index in range(
        1,
        int(count) + 1
    ):
        candidate = backup_path(
            path,
            index
        )

        if not os.path.isfile(
            candidate
        ):
            continue

        try:
            _read_document(
                candidate
            )
        except Exception:
            _LOGGER.debug(
                "Ignoring invalid config backup %r during recovery scan.",
                candidate,
                exc_info=True
            )
            continue

        result.append(
            candidate
        )

    return result


def load_config(path=None):
    path = path or config_path()

    if not os.path.isfile(path):
        return _prepare_document({})

    try:
        return _read_document(
            path
        )

    except ConfigSchemaError as exc:
        warnings.warn(
            "Script Toolbox: cannot safely load config at {0!r}: {1}".format(
                path,
                exc
            ),
            RuntimeWarning,
            stacklevel=2
        )
        raise

    except Exception as exc:
        backups = valid_backup_paths(
            path
        )

        if backups:
            recovery = restore_config_backup(
                path,
                source_backup=backups[0]
            )
            warnings.warn(
                (
                    "Script Toolbox: config at {0!r} was unreadable ({1}). "
                    "Recovered automatically from {2!r}; the damaged file "
                    "was preserved at {3!r}."
                ).format(
                    path,
                    exc,
                    recovery["backup"],
                    recovery["corrupt_copy"]
                ),
                RuntimeWarning,
                stacklevel=2
            )
            return recovery[
                "document"
            ]

        warnings.warn(
            (
                "Script Toolbox: failed to load config at {0!r}: {1}. "
                "The original file was left untouched, no valid backup was "
                "found, and configuration recovery is required."
            ).format(
                path,
                exc
            ),
            RuntimeWarning,
            stacklevel=2
        )
        raise ConfigRecoveryRequired(
            path,
            exc,
            backups=backups
        )


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


def _rotate_backups(
    path,
    count=CONFIG_BACKUP_COUNT
):
    if not os.path.isfile(
        path
    ):
        return []

    count = max(
        1,
        int(count)
    )

    for index in range(
        count,
        1,
        -1
    ):
        source = backup_path(
            path,
            index - 1
        )
        destination = backup_path(
            path,
            index
        )

        if os.path.isfile(
            source
        ):
            _replace_file(
                source,
                destination
            )

    shutil.copy2(
        path,
        backup_path(
            path,
            1
        )
    )

    return [
        backup_path(path, index)
        for index in range(1, count + 1)
        if os.path.isfile(
            backup_path(path, index)
        )
    ]


def _corrupt_copy_path(path):
    base = os.path.normpath(
        path
    ) + ".corrupt"

    if not os.path.exists(
        base
    ):
        return base

    index = 2

    while True:
        candidate = "{0}.{1}".format(
            base,
            index
        )

        if not os.path.exists(
            candidate
        ):
            return candidate

        index += 1


def restore_config_backup(
    path,
    source_backup=None
):
    path = os.path.normpath(
        path
    )
    backups = valid_backup_paths(
        path
    )

    if source_backup is None:
        if not backups:
            raise RuntimeError(
                "No valid Script Toolbox configuration backup is available."
            )

        source_backup = backups[0]

    source_backup = os.path.normpath(
        source_backup
    )

    if source_backup not in backups:
        expected = set([
            backup_path(path, index)
            for index in range(1, CONFIG_BACKUP_COUNT + 1)
        ])

        if source_backup not in expected:
            raise RuntimeError(
                "The requested configuration backup does not belong to this "
                "Script Toolbox config."
            )

        _read_document(
            source_backup
        )

    folder = os.path.dirname(
        path
    )
    descriptor, temp_path = tempfile.mkstemp(
        prefix=".script_toolbox_restore_",
        suffix=".tmp",
        dir=(folder or ".")
    )
    os.close(
        descriptor
    )

    corrupt_copy = None

    try:
        shutil.copy2(
            source_backup,
            temp_path
        )

        _read_document(
            temp_path
        )

        if os.path.isfile(
            path
        ):
            corrupt_copy = _corrupt_copy_path(
                path
            )
            shutil.copy2(
                path,
                corrupt_copy
            )

        _replace_file(
            temp_path,
            path
        )

    except Exception:
        try:
            if os.path.exists(
                temp_path
            ):
                os.remove(
                    temp_path
                )
        except OSError:
            _LOGGER.debug(
                "Could not remove temporary config recovery file %r.",
                temp_path,
                exc_info=True
            )
        raise

    return {
        "path": path,
        "backup": source_backup,
        "corrupt_copy": corrupt_copy,
        "document": _read_document(path),
    }


def save_config(document, path=None):
    path = path or config_path()
    serialized = serialize_config(
        document
    )

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
                serialized
            )
            handle.flush()
            os.fsync(
                handle.fileno()
            )

        if os.path.isfile(
            path
        ):
            try:
                _read_document(
                    path
                )
            except ConfigSchemaError:
                raise
            except Exception as exc:
                raise ConfigRecoveryRequired(
                    path,
                    exc,
                    backups=valid_backup_paths(path)
                )

            _rotate_backups(
                path
            )

        _replace_file(
            temp_path,
            path
        )

    except Exception:
        try:
            if os.path.exists(
                temp_path
            ):
                os.remove(
                    temp_path
                )
        except OSError:
            _LOGGER.debug(
                "Could not remove temporary config save file %r.",
                temp_path,
                exc_info=True
            )

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


__all__ = [
    "CONFIG_BACKUP_COUNT",
    "ConfigRecoveryRequired",
    "backup_path",
    "config_path",
    "deserialize_config",
    "deserialize_transfer",
    "export_config",
    "import_config",
    "load_config",
    "restore_config_backup",
    "save_config",
    "serialize_config",
    "valid_backup_paths",
]
