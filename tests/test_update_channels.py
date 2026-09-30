# -*- coding: utf-8 -*-

from script_toolbox.core import update_channels


def _fake_dev_release(build_number=42):
    return {
        "tag": "dev-latest",
        "version": "0.8.5-dev.{0}".format(build_number),
        "name": "Script Toolbox Development",
        "release_url": "https://example.invalid/dev",
        "download_url": "https://example.invalid/script-toolbox-dev.zip",
        "checksum_url": "https://example.invalid/script-toolbox-dev.zip.sha256",
        "asset_name": "script-toolbox-dev.zip",
        "published_at": "2026-09-08T00:00:00Z",
        "body": "",
        "channel": "development",
        "build_number": build_number,
        "commit": "abcdef0",
        "package_kind": "plugin",
    }


def test_development_release_reads_manifest(monkeypatch):
    monkeypatch.setattr(
        update_channels,
        "_is_standalone",
        lambda: False
    )
    manifest_url = "https://example.invalid/dev-manifest.json"

    def fake_read_json(url, token=None, timeout=8):
        if url.endswith(
            "/releases/tags/dev-latest"
        ):
            return {
                "name": "Script Toolbox Development",
                "html_url": "https://example.invalid/dev",
                "published_at": "2026-09-08T00:00:00Z",
                "body": "",
                "assets": [
                    {
                        "name": "script-toolbox-dev.zip",
                        "browser_download_url": (
                            "https://example.invalid/script-toolbox-dev.zip"
                        ),
                    },
                    {
                        "name": "script-toolbox-dev.zip.sha256",
                        "browser_download_url": (
                            "https://example.invalid/script-toolbox-dev.zip.sha256"
                        ),
                    },
                    {
                        "name": "dev-manifest.json",
                        "browser_download_url": manifest_url,
                    },
                ],
            }

        assert url == manifest_url
        return {
            "channel": "development",
            "version": "0.8.5-dev.42",
            "build_number": 42,
            "commit": "abcdef0",
        }

    monkeypatch.setattr(
        update_channels.updater,
        "_read_json",
        fake_read_json
    )

    release = update_channels.development_release()

    assert release["version"] == "0.8.5-dev.42"
    assert release["build_number"] == 42
    assert release["commit"] == "abcdef0"
    assert release["asset_name"] == "script-toolbox-dev.zip"


def test_stable_channel_delegates_to_existing_updater(monkeypatch):
    monkeypatch.setattr(
        update_channels,
        "_is_standalone",
        lambda: False
    )
    captured = {}

    def fake_check_for_update(**kwargs):
        captured.update(kwargs)
        return {
            "available": False,
            "current_version": kwargs["current_version"],
            "latest_version": "0.8.5",
            "release": None,
            "error": None,
        }

    monkeypatch.setattr(
        update_channels.updater,
        "check_for_update",
        fake_check_for_update
    )

    result = update_channels.check_for_update(
        channel="stable",
        current_version="0.8.5"
    )

    assert result["channel"] == "stable"
    assert captured["current_version"] == "0.8.5"


def test_stable_install_can_switch_to_development(monkeypatch):
    monkeypatch.setattr(
        update_channels,
        "_is_standalone",
        lambda: False
    )
    monkeypatch.setattr(
        update_channels,
        "development_release",
        lambda **kwargs: _fake_dev_release(42)
    )

    result = update_channels.check_for_update(
        channel="development",
        current_version="0.8.5",
        current_build_channel="stable",
        current_build_number=0
    )

    assert result["available"] is True
    assert result["latest_version"] == "0.8.5-dev.42"


def test_development_channel_ignores_same_build(monkeypatch):
    monkeypatch.setattr(
        update_channels,
        "_is_standalone",
        lambda: False
    )
    monkeypatch.setattr(
        update_channels,
        "development_release",
        lambda **kwargs: _fake_dev_release(42)
    )

    result = update_channels.check_for_update(
        channel="development",
        current_version="0.8.5-dev.42",
        current_build_channel="development",
        current_build_number=42
    )

    assert result["available"] is False


def test_development_channel_detects_newer_build(monkeypatch):
    monkeypatch.setattr(
        update_channels,
        "_is_standalone",
        lambda: False
    )
    monkeypatch.setattr(
        update_channels,
        "development_release",
        lambda **kwargs: _fake_dev_release(43)
    )

    result = update_channels.check_for_update(
        channel="development",
        current_version="0.8.5-dev.42",
        current_build_channel="development",
        current_build_number=42
    )

    assert result["available"] is True
    assert result["latest_version"] == "0.8.5-dev.43"



def test_standalone_development_release_selects_portable_asset(monkeypatch):
    manifest_url = "https://example.invalid/dev-manifest.json"

    monkeypatch.setattr(
        update_channels,
        "_is_standalone",
        lambda: True
    )

    def fake_read_json(url, token=None, timeout=8):
        if url.endswith(
            "/releases/tags/dev-latest"
        ):
            return {
                "name": "Script Toolbox Development",
                "html_url": "https://example.invalid/dev",
                "published_at": "2026-09-30T00:00:00Z",
                "body": "",
                "assets": [
                    {
                        "name": "script-toolbox-standalone-dev.zip",
                        "browser_download_url": (
                            "https://example.invalid/standalone.zip"
                        ),
                    },
                    {
                        "name": "script-toolbox-standalone-dev.zip.sha256",
                        "browser_download_url": (
                            "https://example.invalid/standalone.zip.sha256"
                        ),
                    },
                    {
                        "name": "dev-manifest.json",
                        "browser_download_url": manifest_url,
                    },
                ],
            }

        assert url == manifest_url
        return {
            "channel": "development",
            "version": "1.0.1-dev.403",
            "build_number": 403,
            "commit": "abcdef0",
        }

    monkeypatch.setattr(
        update_channels.updater,
        "_read_json",
        fake_read_json
    )

    release = update_channels.development_release()

    assert release["package_kind"] == "standalone"
    assert release["asset_name"] == "script-toolbox-standalone-dev.zip"
    assert release["build_number"] == 403


def test_standalone_missing_build_marker_requires_portable_update(monkeypatch):
    monkeypatch.setattr(
        update_channels,
        "_is_standalone",
        lambda: True
    )
    monkeypatch.setattr(
        update_channels,
        "standalone_build_info",
        lambda: {}
    )
    monkeypatch.setattr(
        update_channels,
        "development_release",
        lambda **kwargs: dict(
            _fake_dev_release(403),
            package_kind="standalone",
            asset_name="script-toolbox-standalone-dev.zip"
        )
    )

    result = update_channels.check_for_update(
        channel="development",
        current_version="1.0.1-dev.403",
        current_build_channel="development",
        current_build_number=403
    )

    assert result["available"] is True


def test_standalone_matching_portable_build_is_current(monkeypatch):
    monkeypatch.setattr(
        update_channels,
        "_is_standalone",
        lambda: True
    )
    monkeypatch.setattr(
        update_channels,
        "standalone_build_info",
        lambda: {
            "channel": "development",
            "version": "1.0.1-dev.403",
            "build_number": 403,
        }
    )
    monkeypatch.setattr(
        update_channels,
        "development_release",
        lambda **kwargs: dict(
            _fake_dev_release(403),
            package_kind="standalone",
            asset_name="script-toolbox-standalone-dev.zip"
        )
    )

    result = update_channels.check_for_update(
        channel="development",
        current_version="1.0.1-dev.403",
        current_build_channel="development",
        current_build_number=403
    )

    assert result["available"] is False
