# -*- coding: utf-8 -*-
"""Administrator utility: publish preset JSON files into a readable library.

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
from script_toolbox.core.preset_sync import HOST_FOLDERS


def publish(input_folder, output_folder, source_id, name):
    presets = []
    for folder, dirs, files in os.walk(input_folder):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        for filename in sorted(files):
            if filename.lower().endswith(".json") and not (folder == input_folder and filename == "library.json"):
                with io.open(os.path.join(folder, filename), encoding="utf-8") as handle:
                    preset = json.load(handle)
                relative = os.path.relpath(folder, input_folder).replace(os.sep, "/").split("/")
                if relative[0] in HOST_FOLDERS:
                    preset["dcc"] = HOST_FOLDERS[relative[0]]
                    preset["category"] = "/".join(relative[1:]) or "General"
                presets.append(preset)
    return publish_presets(presets, output_folder, source_id, name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Folder containing canonical preset JSON files")
    parser.add_argument("--output", required=True, help="Shared Preset Library folder")
    parser.add_argument("--id", required=True, help="Stable lowercase source ID")
    parser.add_argument("--name", required=True, help="Source display name")
    arguments = parser.parse_args()
    manifest = publish(arguments.input, arguments.output, arguments.id, arguments.name)
    print("Published {0}, snapshot {1}, {2} preset(s).".format(
        manifest["id"], manifest["revision"][:12], len(manifest["presets"])))


if __name__ == "__main__":
    main()
