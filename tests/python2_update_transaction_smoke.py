# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import shutil
import sys
import tempfile


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(
            __file__
        )
    )
)
SCRIPTS = os.path.join(
    ROOT,
    "scripts"
)

if SCRIPTS not in sys.path:
    sys.path.insert(
        0,
        SCRIPTS
    )


from script_toolbox.core.update_transaction import UpdateTransaction


work = tempfile.mkdtemp(
    prefix="script_toolbox_txn_py2_"
)

try:
    repository_root = os.path.join(
        work,
        "repo"
    )
    package = os.path.join(
        repository_root,
        "scripts",
        "script_toolbox"
    )
    source = os.path.join(
        work,
        "source"
    )

    required = {
        "__init__.py": "# package\n",
        "constants.py": 'PLUGIN_VERSION = "2.0.0"\n',
        os.path.join("core", "updater.py"): "VALUE = 1\n",
        os.path.join("model", "items.py"): "VALUE = 1\n",
        os.path.join("hosts", "__init__.py"): "VALUE = 1\n",
        os.path.join("ui", "main_window.py"): "VALUE = 1\n",
    }

    for root_path, version in (
        (package, "1.0.0"),
        (source, "2.0.0"),
    ):
        for relative, content in required.items():
            path = os.path.join(
                root_path,
                relative
            )
            parent = os.path.dirname(
                path
            )
            if not os.path.isdir(
                parent
            ):
                os.makedirs(
                    parent
                )

            value = content
            if relative == "constants.py":
                value = 'PLUGIN_VERSION = "{0}"\n'.format(
                    version
                )

            with open(
                path,
                "wb"
            ) as handle:
                handle.write(
                    value.encode(
                        "utf-8"
                    )
                )

    with open(
        os.path.join(
            package,
            "old_only.py"
        ),
        "wb"
    ) as handle:
        handle.write(
            b"OLD = True\n"
        )

    transaction = UpdateTransaction(
        package,
        repository_root,
        host_key="standalone"
    )

    version = transaction.prepare(
        source,
        expected_version="2.0.0"
    )
    assert version == "2.0.0"

    transaction.activate(
        version
    )

    assert os.path.isdir(
        package
    )
    assert not os.path.exists(
        os.path.join(
            package,
            "old_only.py"
        )
    )
    assert not os.path.exists(
        transaction.backup_path
    )
    assert not os.path.exists(
        transaction.journal_path
    )

finally:
    shutil.rmtree(
        work
    )

print(
    "Python 2 updater transaction v2 smoke passed."
)
