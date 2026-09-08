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
from script_toolbox.core.config_store import ConfigStore
from script_toolbox.core.state_refresh import StateRefreshQueue


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

        store = ConfigStore(
            document=document,
            path=path
        )
        store.mark_dirty()
        store.flush()

        assert store.dirty is False
        assert store.write_count == 1
        assert os.path.isfile(
            config.backup_path(
                path,
                1
            )
        )

        refresh_queue = StateRefreshQueue()
        assert refresh_queue.request() is True
        assert refresh_queue.request() is False
        assert refresh_queue.consume() is True
        assert refresh_queue.pending is False
    finally:
        shutil.rmtree(folder)


if __name__ == "__main__":
    main()
