# -*- coding: utf-8 -*-
"""Exercise real package sync and reference persistence on Python 2.7."""
from __future__ import print_function

import io
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, ROOT)

from script_toolbox.constants import CONFIG_VERSION
from script_toolbox.core.config import serialize_config, deserialize_config
from script_toolbox.core.preset_sources import SourceRegistry
from script_toolbox.core.preset_sync import SyncService
from script_toolbox.core.preset_references import PresetResolver
from script_toolbox.model import create_item
from tools.publish_preset_source import publish


def main():
    folder = tempfile.mkdtemp(prefix="stb-managed-smoke-")
    try:
        inputs = os.path.join(folder, "inputs")
        os.makedirs(inputs)
        source = os.path.join(folder, "source")
        preset = {"id": "pipeline", "dcc": "all", "root": create_item("menu", {
            "id": "shots", "name": "shots", "ui": {"label": u"Шоты"},
            "props": {"items": ["sh001", "sh002"]}})}
        with io.open(os.path.join(inputs, "pipeline.json"), "w", encoding="utf-8") as handle:
            handle.write(json.dumps(preset, ensure_ascii=False))
        publish(inputs, source, "studio", u"Студия")
        registry = SourceRegistry(os.path.join(folder, "settings.json"),
                                  os.path.join(folder, "cache"))
        registry.put({"id": "studio", "name": u"Студия", "remote_path": source})
        service = SyncService(registry)
        assert service.check("studio", True)["state"] == "up_to_date"
        resolver = PresetResolver(registry)
        reference = resolver.create_reference("studio", "pipeline", "shots")
        document = {"version": CONFIG_VERSION, "sections": [create_item("folder", {"items": [reference]})]}
        resolver.resolve_document(document)
        document["sections"][0]["items"][0]["props"]["value"] = "sh002"
        saved = deserialize_config(serialize_config(document))
        assert saved["sections"][0]["items"][0]["kind"] == "reference"
        assert saved["sections"][0]["items"][0]["props"]["state"]["value"] == "sh002"
        shutil.rmtree(source)
        assert service.check("studio", True)["state"] == "offline"
        PresetResolver(registry).resolve_document(saved)
        assert saved["sections"][0]["items"][0]["props"]["value"] == "sh002"
        print("Python 2 managed preset sync/reference/offline smoke passed.")
    finally:
        shutil.rmtree(folder)


if __name__ == "__main__":
    main()
