# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)
sys.path.insert(
    0,
    os.path.join(
        ROOT,
        "scripts"
    )
)

from script_toolbox.core import config


def main():
    folder = tempfile.mkdtemp(
        prefix="script_toolbox_config_py2_"
    )
    path = os.path.join(
        folder,
        "toolbox.json"
    )

    try:
        config.save_config(
            {},
            path=path
        )
        document = config.load_config(
            path=path
        )
        assert document["sections"]
        assert os.path.isfile(path)
    finally:
        shutil.rmtree(folder)


if __name__ == "__main__":
    main()
