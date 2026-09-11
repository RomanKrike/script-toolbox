# -*- coding: utf-8 -*-

import hashlib
import os
import zipfile

import pytest

from script_toolbox.core import updater
from script_toolbox.core.updater import UpdateError
from script_toolbox.core.updater import _read_checksum
from script_toolbox.core.updater import _safe_extract
from script_toolbox.core.updater import _sha256_file
from script_toolbox.core.updater import _verify_checksum
from script_toolbox.core.updater import is_newer_version
from script_toolbox.core.updater import latest_release


def test_stable_release_is_newer_than_same_dev_version():
    assert is_newer_version(
        "0.2.0",
        "0.2.0-dev"
    )


def test_older_release_is_not_newer():
    assert not is_newer_version(
        "0.1.9",
        "0.2.0-dev"
    )


def test_v_prefix_is_supported():
    assert is_newer_version(
        "v1.0.0",
        "0.9.9"
    )


def test_same_version_is_not_newer():
    assert not is_newer_version(
        "1.2.3",
        "1.2.3"
    )


def test_patch_release_is_newer():
    assert is_newer_version(
        "1.2.4",
        "1.2.3"
    )


def test_latest_release_prefers_packaged_asset(monkeypatch):
    def fake_read_json(url, token=None, timeout=8):
        return {
            "tag_name": "v1.2.3",
            "name": "Script Toolbox v1.2.3",
            "html_url": "https://example.invalid/release",
            "zipball_url": "https://example.invalid/source.zip",
            "published_at": "2026-09-03T00:00:00Z",
            "body": "notes",
            "assets": [
                {
                    "name": "script-toolbox-1.2.3.zip",
                    "url": "https://api.example.invalid/package",
                    "browser_download_url": "https://example.invalid/package.zip",
                },
                {
                    "name": "script-toolbox-1.2.3.zip.sha256",
                    "url": "https://api.example.invalid/checksum",
                    "browser_download_url": "https://example.invalid/package.zip.sha256",
                },
            ],
        }

    monkeypatch.setattr(
        updater,
        "_read_json",
        fake_read_json
    )

    release = latest_release(
        repository="RomanKrike/script-toolbox"
    )

    assert release["version"] == "1.2.3"
    assert release["download_url"] == (
        "https://example.invalid/package.zip"
    )
    assert release["checksum_url"] == (
        "https://example.invalid/package.zip.sha256"
    )
    assert release["asset_name"] == (
        "script-toolbox-1.2.3.zip"
    )
    assert release["source_archive_url"] == (
        "https://example.invalid/source.zip"
    )


def test_latest_release_keeps_source_archive_metadata_only(monkeypatch):
    def fake_read_json(url, token=None, timeout=8):
        return {
            "tag_name": "v1.0.0",
            "zipball_url": "https://example.invalid/source.zip",
            "assets": [],
        }

    monkeypatch.setattr(
        updater,
        "_read_json",
        fake_read_json
    )

    release = latest_release(
        repository="RomanKrike/script-toolbox"
    )

    assert release["download_url"] == ""
    assert release["checksum_url"] == ""
    assert release["asset_name"] == ""
    assert release["source_archive_url"] == (
        "https://example.invalid/source.zip"
    )


def test_check_for_update_does_not_offer_unverified_newer_release(
    monkeypatch
):
    monkeypatch.setattr(
        updater,
        "latest_release",
        lambda **kwargs: {
            "version": "9.9.9",
            "asset_name": "script-toolbox-9.9.9.zip",
            "download_url": "https://example.invalid/package.zip",
            "checksum_url": "",
        }
    )

    result = updater.check_for_update(
        current_version="1.0.0"
    )

    assert result["available"] is False
    assert "checksum" in result["error"].lower()


def test_latest_release_requires_tag(monkeypatch):
    monkeypatch.setattr(
        updater,
        "_read_json",
        lambda *args, **kwargs: {
            "tag_name": "",
        }
    )

    with pytest.raises(
        UpdateError
    ):
        latest_release()


def test_sha256_helpers(tmp_path):
    archive = tmp_path / "package.zip"
    archive.write_bytes(
        b"script-toolbox-test"
    )

    expected = hashlib.sha256(
        b"script-toolbox-test"
    ).hexdigest()

    checksum = tmp_path / "package.zip.sha256"
    checksum.write_text(
        expected + "  package.zip\n"
    )

    assert _sha256_file(
        str(archive)
    ) == expected
    assert _read_checksum(
        str(checksum)
    ) == expected
    assert _verify_checksum(
        str(archive),
        str(checksum)
    ) is True


def test_checksum_mismatch_is_rejected(tmp_path):
    archive = tmp_path / "package.zip"
    archive.write_bytes(
        b"actual"
    )

    checksum = tmp_path / "package.zip.sha256"
    checksum.write_text(
        hashlib.sha256(
            b"different"
        ).hexdigest()
    )

    with pytest.raises(
        UpdateError
    ):
        _verify_checksum(
            str(archive),
            str(checksum)
        )


def test_invalid_checksum_text_is_rejected(tmp_path):
    checksum = tmp_path / "package.zip.sha256"
    checksum.write_text(
        "not-a-sha256"
    )

    with pytest.raises(
        UpdateError
    ):
        _read_checksum(
            str(checksum)
        )


def test_safe_extract_rejects_path_traversal(tmp_path):
    archive_path = tmp_path / "bad.zip"

    with zipfile.ZipFile(
        str(archive_path),
        "w"
    ) as archive:
        archive.writestr(
            "../outside.txt",
            "bad"
        )

    destination = tmp_path / "extract"
    destination.mkdir()

    with zipfile.ZipFile(
        str(archive_path),
        "r"
    ) as archive:
        with pytest.raises(
            UpdateError
        ):
            _safe_extract(
                archive,
                str(destination)
            )


def test_safe_extract_allows_normal_archive(tmp_path):
    archive_path = tmp_path / "good.zip"

    with zipfile.ZipFile(
        str(archive_path),
        "w"
    ) as archive:
        archive.writestr(
            "root/scripts/script_toolbox/__init__.py",
            "# ok"
        )

    destination = tmp_path / "extract"
    destination.mkdir()

    with zipfile.ZipFile(
        str(archive_path),
        "r"
    ) as archive:
        _safe_extract(
            archive,
            str(destination)
        )

    assert os.path.isfile(
        str(
            destination /
            "root" /
            "scripts" /
            "script_toolbox" /
            "__init__.py"
        )
    )


def test_read_json_uses_powershell_fallback_on_windows(
    monkeypatch,
    tmp_path
):
    from script_toolbox.core.updater import _read_json

    monkeypatch.setattr(
        updater,
        "_is_windows",
        lambda: True
    )

    def fail_request(*args, **kwargs):
        raise updater.URLError(
            "timed out"
        )

    monkeypatch.setattr(
        updater,
        "_request",
        fail_request
    )

    def fake_download(
        url,
        destination,
        token=None,
        timeout=30,
        accept="application/octet-stream"
    ):
        with open(
            destination,
            "wb"
        ) as handle:
            handle.write(
                b'{"tag_name": "v9.9.9"}'
            )

        return destination

    monkeypatch.setattr(
        updater,
        "_download_with_powershell",
        fake_download
    )

    result = _read_json(
        "https://example.invalid/releases/latest"
    )

    assert result["tag_name"] == "v9.9.9"


def test_binary_download_uses_powershell_fallback_on_windows(
    monkeypatch,
    tmp_path
):
    destination = str(
        tmp_path / "download.bin"
    )

    monkeypatch.setattr(
        updater,
        "_is_windows",
        lambda: True
    )

    monkeypatch.setattr(
        updater,
        "_request",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            updater.URLError(
                "timed out"
            )
        )
    )

    def fake_download(
        url,
        destination,
        token=None,
        timeout=30,
        accept="application/octet-stream"
    ):
        with open(
            destination,
            "wb"
        ) as handle:
            handle.write(
                b"ok"
            )

        return destination

    monkeypatch.setattr(
        updater,
        "_download_with_powershell",
        fake_download
    )

    result = updater._download_file(
        "https://example.invalid/file.zip",
        destination
    )

    assert result == destination
    assert open(
        destination,
        "rb"
    ).read() == b"ok"


def test_non_windows_request_failure_is_not_hidden(
    monkeypatch,
    tmp_path
):
    destination = str(
        tmp_path / "download.bin"
    )

    monkeypatch.setattr(
        updater,
        "_is_windows",
        lambda: False
    )

    monkeypatch.setattr(
        updater,
        "_request",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            updater.URLError(
                "timed out"
            )
        )
    )

    with pytest.raises(
        updater.URLError
    ):
        updater._download_file(
            "https://example.invalid/file.zip",
            destination
        )


def test_hidden_process_kwargs_use_create_no_window_on_windows(
    monkeypatch
):
    monkeypatch.setattr(
        updater,
        "_is_windows",
        lambda: True
    )

    kwargs = updater._hidden_process_kwargs()

    assert kwargs[
        "creationflags"
    ] == 0x08000000


def test_hidden_process_kwargs_are_empty_off_windows(
    monkeypatch
):
    monkeypatch.setattr(
        updater,
        "_is_windows",
        lambda: False
    )

    assert updater._hidden_process_kwargs() == {}


def test_install_release_forwards_to_transaction_v2(monkeypatch):
    from script_toolbox.core import update_transaction

    captured = {}

    def fake_install(release, token=None, timeout=30):
        captured["release"] = release
        captured["token"] = token
        captured["timeout"] = timeout
        return {
            "installed": True,
            "transaction_version": 2,
        }

    monkeypatch.setattr(
        update_transaction,
        "install_release",
        fake_install
    )

    release = {
        "version": "9.9.9",
    }
    result = updater.install_release(
        release,
        token="token",
        timeout=17
    )

    assert result["transaction_version"] == 2
    assert captured["release"] is release
    assert captured["token"] == "token"
    assert captured["timeout"] == 17


def test_powershell_token_is_passed_via_environment(
    tmp_path,
    monkeypatch
):
    destination = tmp_path / "download.bin"
    destination.write_bytes(b"ok")
    captured = {}

    class FakeProcess(object):
        returncode = 0

        def communicate(self):
            return b"", b""

    def fake_popen(args, stdout=None, stderr=None, env=None, **kwargs):
        captured["args"] = args
        captured["env"] = env
        return FakeProcess()

    monkeypatch.setattr(
        updater,
        "_powershell_executable",
        lambda: "powershell.exe"
    )
    monkeypatch.setattr(
        updater.subprocess,
        "Popen",
        fake_popen
    )

    secret = "do-not-put-me-on-the-command-line"
    updater._download_with_powershell(
        "https://example.invalid/file.zip",
        str(destination),
        token=secret
    )

    command_line = " ".join(captured["args"])
    assert secret not in command_line
    assert captured["env"]["SCRIPT_TOOLBOX_UPDATE_TOKEN"] == secret
