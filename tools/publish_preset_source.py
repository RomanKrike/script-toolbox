# -*- coding: utf-8 -*-
"""Administrator utility: publish canonical preset JSON files as one revision.

The Toolbox client never calls this utility or writes to source folders.
"""
from __future__ import print_function

import argparse
import io
import json
import os
import sys

SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from script_toolbox.core.preset_library import publish_presets


def publish(input_folder, output_folder, source_id, name):
    presets = []
    for filename in sorted(os.listdir(input_folder)):
        if filename.lower().endswith(".json"):
            with io.open(os.path.join(input_folder, filename), encoding="utf-8") as handle:
                presets.append(json.load(handle))
    return publish_presets(presets, output_folder, source_id, name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Folder containing canonical preset JSON files")
    parser.add_argument("--output", required=True, help="Shared Preset Source folder")
    parser.add_argument("--id", required=True, help="Stable lowercase source ID")
    parser.add_argument("--name", required=True, help="Source display name")
    arguments = parser.parse_args()
    manifest = publish(arguments.input, arguments.output, arguments.id, arguments.name)
    print("Published {0}, revision {1}, {2} preset(s).".format(
        manifest["id"], manifest["revision"], len(manifest["presets"])))


if __name__ == "__main__":
    main()
