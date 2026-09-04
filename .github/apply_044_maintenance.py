from pathlib import Path
import re


def read(path):
    return Path(path).read_text(encoding="utf-8")


def write(path, text):
    Path(path).write_text(text, encoding="utf-8")


# ----------------------------------------------------------------------
# core/config.py: visible load failures + atomic replacement.
# ----------------------------------------------------------------------
config_path = "scripts/script_toolbox/core/config.py"
write(config_path, '''# -*- coding: utf-8 -*-
from __future__ import print_function

import io
import json
import os
import tempfile
import warnings

from ..hosts import HOST
from ..pycompat import text_type
from ..constants import CONFIG_FILENAME
from ..constants import CONFIG_PATH_ENV
from ..model import normalize_document


def config_path():
    override = os.environ.get(
        CONFIG_PATH_ENV,
        ""
    ).strip()

    if override:
        return os.path.normpath(
            override
        )

    try:
        folder = HOST.user_config_dir()
    except Exception:
        folder = os.path.expanduser("~")

    try:
        filename = HOST.config_filename()
    except Exception:
        filename = CONFIG_FILENAME

    return os.path.normpath(
        os.path.join(
            folder,
            filename
        )
    )


def load_config(path=None):
    path = path or config_path()

    if not os.path.isfile(path):
        return normalize_document({})

    try:
        with io.open(
            path,
            "r",
            encoding="utf-8"
        ) as handle:
            return normalize_document(
                json.load(handle)
            )
    except Exception as exc:
        warnings.warn(
            "Script Toolbox: failed to load config at {0!r}: {1}. "
            "Falling back to the default configuration.".format(
                path,
                exc
            ),
            RuntimeWarning,
            stacklevel=2
        )
        return normalize_document({})


def _replace_file_windows(source, destination):
    # Maya 2015 ships Python 2.7, where os.replace() is unavailable.
    # MoveFileExW provides replace-existing semantics without deleting the
    # destination first, so a failed replacement never creates a deliberate
    # no-config window.
    import ctypes

    move_file_ex = ctypes.windll.kernel32.MoveFileExW
    flags = 0x00000001 | 0x00000008  # REPLACE_EXISTING | WRITE_THROUGH

    result = move_file_ex(
        text_type(os.path.abspath(source)),
        text_type(os.path.abspath(destination)),
        flags
    )

    if not result:
        raise ctypes.WinError()


def _replace_file(source, destination):
    replace = getattr(
        os,
        "replace",
        None
    )

    if replace is not None:
        replace(
            source,
            destination
        )
        return

    if os.name == "nt":
        _replace_file_windows(
            source,
            destination
        )
        return

    # POSIX rename replaces an existing destination atomically.
    os.rename(
        source,
        destination
    )


def save_config(document, path=None):
    path = path or config_path()
    document = normalize_document(document)

    folder = os.path.dirname(path)

    if folder and not os.path.isdir(folder):
        os.makedirs(folder)

    descriptor, temp_path = tempfile.mkstemp(
        prefix=".script_toolbox_config_",
        suffix=".tmp",
        dir=(folder or ".")
    )

    try:
        with io.open(
            descriptor,
            "w",
            encoding="utf-8"
        ) as handle:
            handle.write(
                text_type(
                    json.dumps(
                        document,
                        ensure_ascii=False,
                        indent=2
                    )
                )
            )
            handle.flush()
            os.fsync(
                handle.fileno()
            )

        _replace_file(
            temp_path,
            path
        )

    except Exception:
        try:
            os.remove(
                temp_path
            )
        except OSError:
            pass

        raise

    return path


def export_config(document, path):
    return save_config(
        document,
        path=path
    )


def import_config(path):
    return load_config(
        path=path
    )
''')


# ----------------------------------------------------------------------
# Small lint cleanups.
# ----------------------------------------------------------------------
path = "scripts/script_toolbox/ui/properties/basic.py"
text = read(path)
text = text.replace("from ...model.items import safe_float\n", "")
text = text.replace("from ...model.items import safe_int\n", "")
write(path, text)

path = "scripts/script_toolbox/ui/interface_tree.py"
text = read(path)
text = text.replace("        current = self.currentItem()\n\n", "", 1)
write(path, text)

path = "scripts/script_toolbox/ui/interface_editor.py"
text = read(path)
text = text.replace(
    "    def paste_selected(self):\n        global _EDITOR_CLIPBOARD\n\n",
    "    def paste_selected(self):\n",
    1
)
write(path, text)


# ----------------------------------------------------------------------
# updater.py: keep token out of process command line and protect .mod swap.
# ----------------------------------------------------------------------
path = "scripts/script_toolbox/core/updater.py"
text = read(path)

new_ps = '''def _download_with_powershell(
    url,
    destination,
    token=None,
    timeout=30,
    accept="application/octet-stream"
):
    executable = _powershell_executable()

    if not executable:
        raise UpdateError(
            "PowerShell fallback is not available."
        )

    timeout_ms = max(
        1000,
        int(
            float(timeout) *
            1000.0
        )
    )

    token = _github_token(
        token
    )
    child_env = os.environ.copy()
    token_env = "SCRIPT_TOOLBOX_UPDATE_TOKEN"
    child_env.pop(
        token_env,
        None
    )

    script = [
        "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12",
        "$request = [System.Net.HttpWebRequest]::Create('{0}')".format(
            _powershell_quote(
                url
            )
        ),
        "$request.UserAgent = '{0}'".format(
            _powershell_quote(
                USER_AGENT
            )
        ),
        "$request.Accept = '{0}'".format(
            _powershell_quote(
                accept
            )
        ),
        "$request.Timeout = {0}".format(
            timeout_ms
        ),
        "$request.ReadWriteTimeout = {0}".format(
            timeout_ms
        ),
    ]

    if token:
        child_env[
            token_env
        ] = token
        script.extend([
            "$token = $env:{0}".format(
                token_env
            ),
            "if ($token) { $request.Headers['Authorization'] = 'token ' + $token }",
        ])

    script.extend([
        "$response = $request.GetResponse()",
        "$input = $response.GetResponseStream()",
        "$output = [System.IO.File]::Open('{0}', [System.IO.FileMode]::Create)".format(
            _powershell_quote(
                destination
            )
        ),
        "try { $input.CopyTo($output) } finally { $output.Close(); $input.Close(); $response.Close() }",
    ])

    command = "; ".join(
        script
    )

    process_kwargs = _hidden_process_kwargs()

    process = subprocess.Popen(
        [
            executable,
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            command,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=child_env,
        **process_kwargs
    )

    stdout_value, stderr_value = process.communicate()

    if process.returncode != 0:
        try:
            error_text = stderr_value.decode(
                "utf-8",
                "replace"
            )
        except Exception:
            error_text = text_type(
                stderr_value
            )

        raise UpdateError(
            "PowerShell download failed: {0}".format(
                error_text.strip() or
                "exit code {0}".format(
                    process.returncode
                )
            )
        )

    if not os.path.isfile(
        destination
    ):
        raise UpdateError(
            "PowerShell download did not create the destination file."
        )

    return destination
'''
text, count = re.subn(
    r'def _download_with_powershell\(.*?\n\ndef _request\(',
    new_ps + '\n\ndef _request(',
    text,
    count=1,
    flags=re.S,
)
if count != 1:
    raise RuntimeError("Could not replace _download_with_powershell")

new_install = '''def install_release(
    release,
    token=None,
    timeout=30
):
    if not isinstance(
        release,
        dict
    ):
        raise UpdateError(
            "Invalid release metadata."
        )

    download_url = text_type(
        release.get(
            "download_url",
            ""
        )
    ).strip()

    if not download_url:
        raise UpdateError(
            "The release has no download URL."
        )

    destination_package = package_directory()
    destination_root = repository_root()

    if not os.path.isdir(
        destination_package
    ):
        raise UpdateError(
            "Cannot find the installed Script Toolbox package."
        )

    work_directory = tempfile.mkdtemp(
        prefix="script_toolbox_update_"
    )
    archive_path = os.path.join(
        work_directory,
        "release.zip"
    )
    checksum_path = os.path.join(
        work_directory,
        "release.zip.sha256"
    )
    extracted_path = os.path.join(
        work_directory,
        "extracted"
    )

    backup_path = (
        destination_package +
        ".update_backup"
    )
    destination_mod = None
    mod_backup_path = None
    mod_had_original = False

    try:
        _download_file(
            download_url,
            archive_path,
            token=token,
            timeout=timeout
        )

        checksum_url = text_type(
            release.get(
                "checksum_url",
                ""
            )
        ).strip()

        if checksum_url:
            _download_file(
                checksum_url,
                checksum_path,
                token=token,
                timeout=timeout
            )
            _verify_checksum(
                archive_path,
                checksum_path
            )

        os.makedirs(
            extracted_path
        )

        archive = zipfile.ZipFile(
            archive_path,
            "r"
        )

        try:
            _safe_extract(
                archive,
                extracted_path
            )
        finally:
            archive.close()

        source_root = _find_release_root(
            extracted_path
        )
        source_package = os.path.join(
            source_root,
            "scripts",
            "script_toolbox"
        )
        source_mod = os.path.join(
            source_root,
            "MayaScriptToolbox.mod"
        )

        if (
            HOST.key == "maya" and
            os.path.isfile(
                source_mod
            )
        ):
            destination_mod = os.path.join(
                destination_root,
                "MayaScriptToolbox.mod"
            )
            mod_backup_path = (
                destination_mod +
                ".update_backup"
            )

            if os.path.exists(
                mod_backup_path
            ):
                os.remove(
                    mod_backup_path
                )

            if os.path.isfile(
                destination_mod
            ):
                try:
                    shutil.copy2(
                        destination_mod,
                        mod_backup_path
                    )
                except Exception:
                    try:
                        if os.path.exists(
                            mod_backup_path
                        ):
                            os.remove(
                                mod_backup_path
                            )
                    except Exception:
                        pass
                    raise

                mod_had_original = True

        if os.path.exists(
            backup_path
        ):
            shutil.rmtree(
                backup_path
            )

        os.rename(
            destination_package,
            backup_path
        )

        try:
            shutil.copytree(
                source_package,
                destination_package
            )

            if destination_mod is not None:
                shutil.copy2(
                    source_mod,
                    destination_mod
                )

        except Exception as install_exc:
            rollback_error = None

            try:
                if os.path.isdir(
                    destination_package
                ):
                    shutil.rmtree(
                        destination_package
                    )

                os.rename(
                    backup_path,
                    destination_package
                )
            except Exception as exc:
                rollback_error = exc

            if destination_mod is not None:
                try:
                    if (
                        mod_had_original and
                        os.path.isfile(
                            mod_backup_path
                        )
                    ):
                        shutil.copy2(
                            mod_backup_path,
                            destination_mod
                        )
                        os.remove(
                            mod_backup_path
                        )
                    elif (
                        not mod_had_original and
                        os.path.exists(
                            destination_mod
                        )
                    ):
                        os.remove(
                            destination_mod
                        )
                except Exception as exc:
                    if rollback_error is None:
                        rollback_error = exc

            if rollback_error is not None:
                raise UpdateError(
                    "Update failed ({0}); rollback also failed ({1}).".format(
                        text_type(
                            install_exc
                        ),
                        text_type(
                            rollback_error
                        )
                    )
                )

            raise

        if os.path.isdir(
            backup_path
        ):
            shutil.rmtree(
                backup_path
            )

        if (
            mod_backup_path and
            os.path.isfile(
                mod_backup_path
            )
        ):
            os.remove(
                mod_backup_path
            )

        return {
            "installed": True,
            "version": release.get(
                "version"
            ),
            "restart_required": False,
            "hot_reload_supported": True,
        }

    except Exception as exc:
        if isinstance(
            exc,
            UpdateError
        ):
            raise

        raise UpdateError(
            text_type(
                exc
            )
        )

    finally:
        try:
            shutil.rmtree(
                work_directory
            )
        except Exception:
            pass
'''
text, count = re.subn(
    r'def install_release\(.*?\n\n__all__ = \[',
    new_install + '\n\n__all__ = [',
    text,
    count=1,
    flags=re.S,
)
if count != 1:
    raise RuntimeError("Could not replace install_release")
write(path, text)


# ----------------------------------------------------------------------
# Config tests.
# ----------------------------------------------------------------------
write("tests/test_config.py", '''# -*- coding: utf-8 -*-

import io
import json
import os
import warnings

import pytest

from script_toolbox.constants import CONFIG_VERSION
from script_toolbox.core import config


def _config_path(tmp_path):
    return str(
        tmp_path /
        "toolbox.json"
    )


def test_load_config_missing_file_returns_default(tmp_path):
    document = config.load_config(
        path=_config_path(tmp_path)
    )

    assert document["version"] == CONFIG_VERSION
    assert document["sections"]


def test_save_then_load_round_trip(tmp_path):
    path = _config_path(tmp_path)

    original = config.load_config(path=path)
    original["sections"][0]["name"] = "Renamed"

    written_path = config.save_config(
        original,
        path=path
    )

    assert written_path == path
    assert os.path.isfile(path)

    reloaded = config.load_config(path=path)
    assert reloaded["sections"][0]["name"] == "Renamed"


def test_save_config_creates_missing_parent_directory(tmp_path):
    path = str(
        tmp_path /
        "nested" /
        "deeper" /
        "toolbox.json"
    )

    config.save_config(
        {},
        path=path
    )

    assert os.path.isfile(path)


def test_save_config_leaves_no_temp_file_behind(tmp_path):
    path = _config_path(tmp_path)

    config.save_config(
        {},
        path=path
    )

    leftovers = [
        name
        for name in os.listdir(str(tmp_path))
        if name != os.path.basename(path)
    ]

    assert leftovers == []


def test_save_config_does_not_destroy_original_on_write_failure(
    tmp_path,
    monkeypatch
):
    path = _config_path(tmp_path)
    config.save_config({}, path=path)

    with io.open(
        path,
        "r",
        encoding="utf-8"
    ) as handle:
        original_text = handle.read()

    def _boom(*args, **kwargs):
        raise RuntimeError("disk full")

    monkeypatch.setattr(
        json,
        "dumps",
        _boom
    )

    with pytest.raises(RuntimeError):
        config.save_config({}, path=path)

    with io.open(
        path,
        "r",
        encoding="utf-8"
    ) as handle:
        assert handle.read() == original_text


def test_save_config_preserves_original_on_replace_failure(
    tmp_path,
    monkeypatch
):
    path = _config_path(tmp_path)
    config.save_config({}, path=path)

    with io.open(
        path,
        "r",
        encoding="utf-8"
    ) as handle:
        original_text = handle.read()

    def _boom(source, destination):
        raise OSError("replace failed")

    monkeypatch.setattr(
        config,
        "_replace_file",
        _boom
    )

    with pytest.raises(OSError):
        config.save_config({}, path=path)

    with io.open(
        path,
        "r",
        encoding="utf-8"
    ) as handle:
        assert handle.read() == original_text

    assert sorted(os.listdir(str(tmp_path))) == [
        os.path.basename(path)
    ]


def test_python2_windows_replace_path_never_removes_target(monkeypatch):
    calls = []

    monkeypatch.setattr(
        config.os,
        "replace",
        None
    )
    monkeypatch.setattr(
        config.os,
        "name",
        "nt"
    )
    monkeypatch.setattr(
        config,
        "_replace_file_windows",
        lambda source, destination: calls.append(
            (source, destination)
        )
    )
    monkeypatch.setattr(
        config.os,
        "remove",
        lambda *args: pytest.fail(
            "Windows replacement must not delete the destination first"
        )
    )

    config._replace_file(
        "source.tmp",
        "toolbox.json"
    )

    assert calls == [
        ("source.tmp", "toolbox.json")
    ]


def test_load_config_warns_and_falls_back_on_corrupt_file(tmp_path):
    path = _config_path(tmp_path)

    with io.open(
        path,
        "w",
        encoding="utf-8"
    ) as handle:
        handle.write(u"{not valid json")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        document = config.load_config(path=path)

    assert document["version"] == CONFIG_VERSION
    assert document["sections"]
    assert any(
        "failed to load config" in str(item.message)
        for item in caught
    )


def test_export_import_round_trip(tmp_path):
    path = _config_path(tmp_path)

    config.export_config(
        {
            "sections": [
                {
                    "kind": "folder",
                    "name": "Exported",
                }
            ],
        },
        path
    )

    document = config.import_config(path)
    assert document["sections"][0]["name"] == "Exported"
''')

write("tests/python2_config_smoke.py", '''# -*- coding: utf-8 -*-
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
''')


# ----------------------------------------------------------------------
# Updater tests: filesystem transaction, module rollback and token secrecy.
# ----------------------------------------------------------------------
path = "tests/test_updater.py"
text = read(path)
append = r'''

# ---------------------------------------------------------------------
# install_release() filesystem transaction tests
# ---------------------------------------------------------------------


def _build_release_zip(
    zip_path,
    version="9.9.9",
    include_package=True
):
    root_name = "script-toolbox-{0}".format(version)

    with zipfile.ZipFile(zip_path, "w") as archive:
        if include_package:
            archive.writestr(
                "{0}/scripts/script_toolbox/__init__.py".format(root_name),
                u"__version__ = '{0}'\n".format(version)
            )
            archive.writestr(
                "{0}/scripts/script_toolbox/marker.py".format(root_name),
                u"MARKER = '{0}'\n".format(version)
            )
        else:
            archive.writestr(
                "{0}/README.md".format(root_name),
                u"no package in this archive"
            )

        archive.writestr(
            "{0}/MayaScriptToolbox.mod".format(root_name),
            u"+ MayaScriptToolbox {0} .\n".format(version)
        )

    return zip_path


def _fake_installed_package(tmp_path):
    repository_root = tmp_path / "repo"
    package_dir = repository_root / "scripts" / "script_toolbox"
    package_dir.mkdir(parents=True)

    (package_dir / "__init__.py").write_text(
        u"__version__ = '0.1.0'\n",
        encoding="utf-8"
    )
    (package_dir / "old_module.py").write_text(
        u"OLD = True\n",
        encoding="utf-8"
    )

    return repository_root, package_dir


def _patch_install_locations(monkeypatch, repository_root, package_dir):
    monkeypatch.setattr(
        updater,
        "package_directory",
        lambda: str(package_dir)
    )
    monkeypatch.setattr(
        updater,
        "repository_root",
        lambda: str(repository_root)
    )


def test_install_release_replaces_package_and_cleans_up(
    tmp_path,
    monkeypatch
):
    repository_root, package_dir = _fake_installed_package(tmp_path)
    _patch_install_locations(monkeypatch, repository_root, package_dir)

    def fake_download_file(url, destination, token=None, timeout=30):
        return _build_release_zip(destination)

    monkeypatch.setattr(
        updater,
        "_download_file",
        fake_download_file
    )

    result = updater.install_release({
        "download_url": "https://example.invalid/release.zip",
        "version": "9.9.9",
    })

    assert result["installed"] is True
    assert result["version"] == "9.9.9"
    assert (package_dir / "marker.py").is_file()
    assert not (package_dir / "old_module.py").exists()
    assert not os.path.isdir(str(package_dir) + ".update_backup")


def test_install_release_rolls_back_on_copy_failure(
    tmp_path,
    monkeypatch
):
    repository_root, package_dir = _fake_installed_package(tmp_path)
    _patch_install_locations(monkeypatch, repository_root, package_dir)

    def fake_download_file(url, destination, token=None, timeout=30):
        return _build_release_zip(destination)

    monkeypatch.setattr(
        updater,
        "_download_file",
        fake_download_file
    )

    def broken_copytree(*args, **kwargs):
        raise OSError("disk full mid-copy")

    monkeypatch.setattr(
        updater.shutil,
        "copytree",
        broken_copytree
    )

    with pytest.raises(UpdateError):
        updater.install_release({
            "download_url": "https://example.invalid/release.zip",
            "version": "9.9.9",
        })

    assert (package_dir / "old_module.py").is_file()
    assert not (package_dir / "marker.py").exists()
    assert not os.path.isdir(str(package_dir) + ".update_backup")


def test_install_release_rolls_back_maya_module_on_copy_failure(
    tmp_path,
    monkeypatch
):
    repository_root, package_dir = _fake_installed_package(tmp_path)
    _patch_install_locations(monkeypatch, repository_root, package_dir)

    module_path = repository_root / "MayaScriptToolbox.mod"
    module_path.write_text(
        u"OLD MODULE\n",
        encoding="utf-8"
    )

    class MayaHost(object):
        key = "maya"

    monkeypatch.setattr(
        updater,
        "HOST",
        MayaHost()
    )

    def fake_download_file(url, destination, token=None, timeout=30):
        return _build_release_zip(destination)

    monkeypatch.setattr(
        updater,
        "_download_file",
        fake_download_file
    )

    original_copy2 = updater.shutil.copy2

    def fail_release_module_copy(source, destination, *args, **kwargs):
        if (
            os.path.basename(source) == "MayaScriptToolbox.mod" and
            not source.endswith(".update_backup") and
            destination == str(module_path)
        ):
            with open(destination, "w") as handle:
                handle.write("PARTIAL")
            raise OSError("module copy failed")

        return original_copy2(
            source,
            destination,
            *args,
            **kwargs
        )

    monkeypatch.setattr(
        updater.shutil,
        "copy2",
        fail_release_module_copy
    )

    with pytest.raises(UpdateError):
        updater.install_release({
            "download_url": "https://example.invalid/release.zip",
            "version": "9.9.9",
        })

    assert (package_dir / "old_module.py").is_file()
    assert module_path.read_text(encoding="utf-8") == "OLD MODULE\n"
    assert not os.path.exists(str(module_path) + ".update_backup")


def test_install_release_rejects_archive_without_package(
    tmp_path,
    monkeypatch
):
    repository_root, package_dir = _fake_installed_package(tmp_path)
    _patch_install_locations(monkeypatch, repository_root, package_dir)

    def fake_download_file(url, destination, token=None, timeout=30):
        return _build_release_zip(
            destination,
            include_package=False
        )

    monkeypatch.setattr(
        updater,
        "_download_file",
        fake_download_file
    )

    with pytest.raises(UpdateError):
        updater.install_release({
            "download_url": "https://example.invalid/release.zip",
            "version": "9.9.9",
        })

    assert (package_dir / "old_module.py").is_file()


def test_install_release_requires_download_url():
    with pytest.raises(UpdateError):
        updater.install_release({
            "version": "9.9.9",
        })


def test_install_release_requires_dict_metadata():
    with pytest.raises(UpdateError):
        updater.install_release("9.9.9")


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
'''
if "def _build_release_zip(" in text:
    raise RuntimeError("Updater install tests already present")
text += append
write(path, text)


# ----------------------------------------------------------------------
# CI: flake8, config coverage and Python 2 config smoke.
# ----------------------------------------------------------------------
path = ".github/workflows/python-checks.yml"
text = read(path)
text = text.replace(
    "run: python -m pip install --upgrade pip pytest pytest-cov",
    "run: python -m pip install --upgrade pip pytest pytest-cov flake8",
    1
)
marker = "      - name: Compile modular package\n        run: python -m compileall -q scripts/script_toolbox\n"
replacement = '''      - name: Flake8
        run: python -m flake8 scripts tests

''' + marker
if marker not in text:
    raise RuntimeError("Compile step not found")
text = text.replace(marker, replacement, 1)
text = text.replace(
    "          --cov=script_toolbox.core.updater\n",
    "          --cov=script_toolbox.core.updater\n          --cov=script_toolbox.core.config\n",
    1
)
marker = '''      - name: Nuke host import smoke with Python 2.7
        run: >
          docker run --rm
          -v "$PWD:/work"
          -w /work
          python:2.7.18-slim-buster
          python tests/python2_nuke_host_smoke.py
'''
replacement = marker + '''
      - name: Config save/load smoke with Python 2.7
        run: >
          docker run --rm
          -v "$PWD:/work"
          -w /work
          python:2.7.18-slim-buster
          python tests/python2_config_smoke.py
'''
if marker not in text:
    raise RuntimeError("Python2 Nuke smoke step not found")
text = text.replace(marker, replacement, 1)
write(path, text)


# ----------------------------------------------------------------------
# Release metadata.
# ----------------------------------------------------------------------
path = "scripts/script_toolbox/constants.py"
text = read(path)
text = text.replace(
    'PLUGIN_VERSION = "0.4.3"',
    'PLUGIN_VERSION = "0.4.4"',
    1
)
write(path, text)

path = "MayaScriptToolbox.mod"
text = read(path)
text = text.replace(
    "+ MayaScriptToolbox 0.4.3 .",
    "+ MayaScriptToolbox 0.4.4 .",
    1
)
write(path, text)

path = "CHANGELOG.md"
text = read(path)
entry = '''# Changelog

## 0.4.4

Configuration and updater safety maintenance release.

### Fixed

- Save toolbox configuration through a same-directory temporary file and atomic replacement.
- Use Windows MoveFileExW replacement for Maya 2015 / Python 2.7 instead of delete-then-rename semantics.
- Warn when an existing configuration cannot be read or parsed instead of silently hiding the failure.
- Keep updater authentication tokens out of the PowerShell command line by passing them through the child environment.
- Back up and restore MayaScriptToolbox.mod together with the Python package when an update fails.
- Remove stale unused imports and editor locals reported by flake8.

### Tests

- Add direct config load/save, corruption, write-failure and replacement-failure tests.
- Add install_release filesystem, rollback, archive-validation and Maya module rollback tests.
- Add flake8 to CI, config coverage, and a Python 2.7 config save/load smoke test.

'''
if not text.startswith("# Changelog\n\n"):
    raise RuntimeError("Unexpected changelog header")
text = text.replace("# Changelog\n\n", entry, 1)
write(path, text)
