# -*- coding: utf-8 -*-
from __future__ import print_function

import io
import json
import os

from ..compat import cmds
from ..compat import text_type
from ..constants import CONFIG_FILENAME
from ..model import normalize_document


def config_path():
    try:
        folder = cmds.internalVar(
            userPrefDir=True
        )
    except Exception:
        folder = os.path.expanduser("~")

    return os.path.normpath(
        os.path.join(
            folder,
            CONFIG_FILENAME
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
    except Exception:
        return normalize_document({})


def save_config(document, path=None):
    path = path or config_path()
    document = normalize_document(document)

    folder = os.path.dirname(path)

    if folder and not os.path.isdir(folder):
        os.makedirs(folder)

    with io.open(
        path,
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
