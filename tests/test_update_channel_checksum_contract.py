# -*- coding: utf-8 -*-

import pytest

from script_toolbox.core import update_channels
from script_toolbox.core.updater import UpdateError


def test_development_release_requires_checksum_asset(monkeypatch):
    manifest_url = "https://example.invalid/dev-manifest.json"

    def fake_read_json(url, token=None, timeout=8):
        if url.endswith("/releases/tags/dev-latest"):
            return {
                "assets": [
                    {
                        "name": "script-toolbox-dev.zip",
                        "browser_download_url": (
                            "https://example.invalid/script-toolbox-dev.zip"
                        ),
                    },
                    {
                        "name": "dev-manifest.json",
                        "browser_download_url": manifest_url,
                    },
                ],
            }
        raise AssertionError("manifest must not be read without checksum")

    monkeypatch.setattr(
        update_channels.updater,
        "_read_json",
        fake_read_json
    )

    with pytest.raises(UpdateError) as exc_info:
        update_channels.development_release()

    assert "script-toolbox-dev.zip.sha256" in str(exc_info.value)
