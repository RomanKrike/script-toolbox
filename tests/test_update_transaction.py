# -*- coding: utf-8 -*-

import hashlib
import os
import shutil
import zipfile

import pytest

from script_toolbox.core import update_transaction
from script_toolbox.core.update_transaction import TRANSACTION_VERSION
from script_toolbox.core.update_transaction import UpdateTransaction
from script_toolbox.core.updater import UpdateError


_REQUIRED_CONTENT = {
    "__init__.py": "# package\n",
    "constants.py": 'PLUGIN_VERSION = "{version}"\n',
    "core/updater.py": "VALUE = 1\n",
    "model/items.py": "VALUE = 1\n",
    "hosts/__init__.py": "VALUE = 1\n",
    "ui/main_window.py": "VALUE = 1\n",
}


def _write_package(path, version="9.9.9", bad_python=False):
    for relative, content in _REQUIRED_CONTENT.items():
        target = path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        value = content.format(version=version)
        if bad_python and relative == "ui/main_window.py":
            value = "if :\n    pass\n"
        target.write_text(value, encoding="utf-8")

    marker = path / "marker.py"
    marker.write_text(
        "MARKER = {!r}\n".format(version),
        encoding="utf-8"
    )
    return path


def _write_module(path, version="9.9.9"):
    path.write_text(
        "+ MayaScriptToolbox {0} .\nPYTHONPATH +:= scripts\n".format(
            version
        ),
        encoding="utf-8"
    )
    return path


def _make_transaction(tmp_path, host_key="standalone"):
    root = tmp_path / "repo"
    package = root / "scripts" / "script_toolbox"
    package.mkdir(parents=True)
    _write_package(package, version="1.0.0")
    (package / "old_only.py").write_text(
        "OLD = True\n",
        encoding="utf-8"
    )

    return UpdateTransaction(
        str(package),
        str(root),
        host_key=host_key
    ), root, package


def _build_release_zip(path, version="9.9.9", bad_python=False):
    source_root = path.parent / "source"
    package = source_root / "scripts" / "script_toolbox"
    package.mkdir(parents=True)
    _write_package(
        package,
        version=version,
        bad_python=bad_python
    )
    _write_module(
        source_root / "MayaScriptToolbox.mod",
        version=version
    )

    with zipfile.ZipFile(str(path), "w") as archive:
        for current_root, _, files in os.walk(str(source_root)):
            for filename in files:
                source = os.path.join(current_root, filename)
                relative = os.path.relpath(source, str(source_root))
                archive.write(
                    source,
                    "script-toolbox-{0}/{1}".format(
                        version,
                        relative.replace(os.sep, "/")
                    )
                )

    shutil.rmtree(str(source_root))
    return path


def _release_metadata(version="9.9.9"):
    return {
        "download_url": "https://example.invalid/release.zip",
        "checksum_url": "https://example.invalid/release.zip.sha256",
        "asset_name": "script-toolbox-{0}.zip".format(version),
        "version": version,
    }


def _patch_install_locations(monkeypatch, root, package):
    monkeypatch.setattr(
        update_transaction,
        "package_directory",
        lambda: str(package)
    )
    monkeypatch.setattr(
        update_transaction,
        "repository_root",
        lambda: str(root)
    )


def _verified_download(archive, checksum_value=None):
    expected = checksum_value
    if expected is None:
        expected = hashlib.sha256(
            archive.read_bytes()
        ).hexdigest()

    def fake_download(url, destination, token=None, timeout=30):
        if url.endswith(".sha256"):
            with open(destination, "w") as handle:
                handle.write(
                    expected + "  release.zip\n"
                )
        else:
            shutil.copy2(
                str(archive),
                destination
            )
        return destination

    return fake_download


def test_validate_package_rejects_version_mismatch(tmp_path):
    transaction, _, _ = _make_transaction(tmp_path)
    staged = tmp_path / "staged"
    staged.mkdir()
    _write_package(staged, version="2.0.0")

    with pytest.raises(UpdateError) as exc_info:
        transaction.validate_package(
            str(staged),
            expected_version="2.0.1"
        )

    assert "version mismatch" in str(exc_info.value).lower()


def test_validate_package_rejects_python_syntax_error(tmp_path):
    transaction, _, _ = _make_transaction(tmp_path)
    staged = tmp_path / "staged"
    staged.mkdir()
    _write_package(
        staged,
        version="2.0.0",
        bad_python=True
    )

    with pytest.raises(UpdateError) as exc_info:
        transaction.validate_package(str(staged))

    assert "does not compile" in str(exc_info.value)


def test_prepare_validates_before_live_package_is_touched(tmp_path):
    transaction, _, package = _make_transaction(tmp_path)
    source = tmp_path / "source_package"
    source.mkdir()
    _write_package(
        source,
        version="2.0.0",
        bad_python=True
    )

    with pytest.raises(UpdateError):
        transaction.prepare(
            str(source),
            expected_version="2.0.0"
        )

    assert (package / "old_only.py").is_file()
    assert not os.path.exists(transaction.backup_path)


def test_activate_swaps_validated_stage_and_cleans_artifacts(tmp_path):
    transaction, _, package = _make_transaction(tmp_path)
    source = tmp_path / "source_package"
    source.mkdir()
    _write_package(source, version="2.0.0")

    version = transaction.prepare(
        str(source),
        expected_version="2.0.0"
    )
    assert version == "2.0.0"

    transaction.activate(version)

    assert (package / "marker.py").read_text(encoding="utf-8") == (
        "MARKER = '2.0.0'\n"
    )
    assert not (package / "old_only.py").exists()
    assert not os.path.exists(transaction.stage_path)
    assert not os.path.exists(transaction.backup_path)
    assert not os.path.exists(transaction.journal_path)


def test_post_activation_validation_failure_rolls_back(tmp_path, monkeypatch):
    transaction, _, package = _make_transaction(tmp_path)
    source = tmp_path / "source_package"
    source.mkdir()
    _write_package(source, version="2.0.0")

    version = transaction.prepare(
        str(source),
        expected_version="2.0.0"
    )
    original_validate = transaction.validate_package

    def fail_live_validation(path, expected_version=None):
        if os.path.normpath(path) == os.path.normpath(str(package)):
            raise UpdateError("post-swap validation failed")
        return original_validate(
            path,
            expected_version=expected_version
        )

    monkeypatch.setattr(
        transaction,
        "validate_package",
        fail_live_validation
    )

    with pytest.raises(UpdateError):
        transaction.activate(version)

    assert (package / "old_only.py").is_file()
    assert (package / "marker.py").read_text(encoding="utf-8") == (
        "MARKER = '1.0.0'\n"
    )
    assert not os.path.exists(transaction.backup_path)
    assert not os.path.exists(transaction.journal_path)


def test_recover_restores_backup_when_activation_was_interrupted(tmp_path):
    transaction, _, package = _make_transaction(tmp_path)
    source = tmp_path / "source_package"
    source.mkdir()
    _write_package(source, version="2.0.0")

    transaction.prepare(
        str(source),
        expected_version="2.0.0"
    )
    transaction._write_journal(
        "prepared",
        version="2.0.0"
    )
    os.rename(
        str(package),
        transaction.backup_path
    )
    transaction._write_journal(
        "backup_moved",
        version="2.0.0"
    )

    assert not package.exists()
    assert transaction.recover() is True

    assert (package / "old_only.py").is_file()
    assert not os.path.exists(transaction.backup_path)
    assert not os.path.exists(transaction.stage_path)
    assert not os.path.exists(transaction.journal_path)


def test_recover_committed_transaction_keeps_valid_new_tree(tmp_path):
    transaction, _, package = _make_transaction(tmp_path)
    source = tmp_path / "source_package"
    source.mkdir()
    _write_package(source, version="2.0.0")

    transaction.prepare(
        str(source),
        expected_version="2.0.0"
    )
    os.rename(
        str(package),
        transaction.backup_path
    )
    os.rename(
        transaction.stage_path,
        str(package)
    )
    transaction._write_journal(
        "committed",
        version="2.0.0"
    )

    assert transaction.recover() is True

    assert (package / "marker.py").is_file()
    assert not (package / "old_only.py").exists()
    assert not os.path.exists(transaction.backup_path)
    assert not os.path.exists(transaction.journal_path)


def test_maya_module_activation_failure_rolls_back_package_and_module(
    tmp_path,
    monkeypatch
):
    transaction, root, package = _make_transaction(
        tmp_path,
        host_key="maya"
    )
    old_module = root / "MayaScriptToolbox.mod"
    _write_module(old_module, version="1.0.0")

    source = tmp_path / "source_package"
    source.mkdir()
    _write_package(source, version="2.0.0")
    source_module = tmp_path / "MayaScriptToolbox.mod"
    _write_module(source_module, version="2.0.0")

    version = transaction.prepare(
        str(source),
        source_mod=str(source_module),
        expected_version="2.0.0"
    )

    real_rename = update_transaction.os.rename

    def fail_module_activation(source_path, destination_path):
        if (
            os.path.normpath(source_path) ==
            os.path.normpath(transaction.mod_stage_path)
        ):
            raise OSError("module activation failed")
        return real_rename(source_path, destination_path)

    monkeypatch.setattr(
        update_transaction.os,
        "rename",
        fail_module_activation
    )

    with pytest.raises(UpdateError):
        transaction.activate(version)

    assert (package / "old_only.py").is_file()
    assert "1.0.0" in old_module.read_text(encoding="utf-8")


def test_install_release_uses_verified_transaction_v2(tmp_path, monkeypatch):
    _, root, package = _make_transaction(tmp_path)
    archive = tmp_path / "release.zip"
    _build_release_zip(
        archive,
        version="9.9.9"
    )
    _patch_install_locations(
        monkeypatch,
        root,
        package
    )
    monkeypatch.setattr(
        update_transaction,
        "_download_file",
        _verified_download(archive)
    )

    result = update_transaction.install_release(
        _release_metadata()
    )

    assert result["installed"] is True
    assert result["transaction_version"] == TRANSACTION_VERSION
    assert (package / "marker.py").is_file()
    assert not (package / "old_only.py").exists()


def test_install_release_rejects_missing_checksum_without_touching_package(
    tmp_path,
    monkeypatch
):
    _, root, package = _make_transaction(tmp_path)
    _patch_install_locations(
        monkeypatch,
        root,
        package
    )
    release = _release_metadata()
    release["checksum_url"] = ""

    with pytest.raises(UpdateError) as exc_info:
        update_transaction.install_release(
            release
        )

    assert "checksum" in str(exc_info.value).lower()
    assert (package / "old_only.py").is_file()
    assert (package / "marker.py").read_text(encoding="utf-8") == (
        "MARKER = '1.0.0'\n"
    )
    assert not os.path.exists(str(package) + ".update_backup")
    assert not os.path.exists(str(package) + ".update_staged")


def test_install_release_rejects_checksum_mismatch_before_recovery(
    tmp_path,
    monkeypatch
):
    _, root, package = _make_transaction(tmp_path)
    archive = tmp_path / "release.zip"
    _build_release_zip(
        archive,
        version="9.9.9"
    )
    _patch_install_locations(
        monkeypatch,
        root,
        package
    )
    monkeypatch.setattr(
        update_transaction,
        "_download_file",
        _verified_download(
            archive,
            checksum_value=("0" * 64)
        )
    )
    recover_calls = []

    def record_recover(self):
        recover_calls.append(True)
        return False

    monkeypatch.setattr(
        UpdateTransaction,
        "recover",
        record_recover
    )

    with pytest.raises(UpdateError) as exc_info:
        update_transaction.install_release(
            _release_metadata()
        )

    assert "checksum verification failed" in str(exc_info.value).lower()
    assert recover_calls == []
    assert (package / "old_only.py").is_file()
    assert (package / "marker.py").read_text(encoding="utf-8") == (
        "MARKER = '1.0.0'\n"
    )


def test_install_release_rejects_missing_official_package(
    tmp_path,
    monkeypatch
):
    _, root, package = _make_transaction(tmp_path)
    _patch_install_locations(
        monkeypatch,
        root,
        package
    )
    release = _release_metadata()
    release["asset_name"] = ""
    release["download_url"] = ""
    release["source_archive_url"] = (
        "https://example.invalid/source.zip"
    )
    download_calls = []

    def unexpected_download(*args, **kwargs):
        download_calls.append(True)
        raise AssertionError("download should not start")

    monkeypatch.setattr(
        update_transaction,
        "_download_file",
        unexpected_download
    )

    with pytest.raises(UpdateError) as exc_info:
        update_transaction.install_release(
            release
        )

    assert "official script toolbox package" in str(exc_info.value).lower()
    assert download_calls == []
    assert (package / "old_only.py").is_file()


def test_runtime_update_thread_routes_to_transaction_v2():
    root = os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
    path = os.path.join(
        root,
        "scripts",
        "script_toolbox",
        "ui",
        "update_ui.py"
    )
    source = open(path, "r").read()

    assert "from ..core.update_transaction import install_release" in source
