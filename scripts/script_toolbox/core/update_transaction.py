# -*- coding: utf-8 -*-
from __future__ import print_function

import json
import os
import re
import shutil
import tempfile
import zipfile

from ..hosts import HOST
from ..pycompat import text_type
from .updater import UpdateError
from .updater import _download_file
from .updater import _find_release_root
from .updater import _safe_extract
from .updater import _validate_installable_release
from .updater import _verify_checksum
from .updater import package_directory
from .updater import repository_root


TRANSACTION_VERSION = 2

_REQUIRED_PACKAGE_FILES = (
    "__init__.py",
    "constants.py",
    os.path.join("core", "updater.py"),
    os.path.join("model", "items.py"),
    os.path.join("hosts", "__init__.py"),
    os.path.join("ui", "main_window.py"),
)

_VERSION_PATTERN = re.compile(
    r'^PLUGIN_VERSION\s*=\s*["\']([^"\']+)["\']',
    re.M
)


class UpdateTransaction(object):
    """Crash-recoverable filesystem transaction for one package update.

    The replacement package is copied and validated at a sibling staging path
    before the live package is touched. Activation then uses same-filesystem
    renames and keeps the previous package until the new tree passes a second
    validation after activation.
    """

    def __init__(
        self,
        destination_package,
        destination_root,
        host_key=None
    ):
        self.destination_package = os.path.normpath(
            destination_package
        )
        self.destination_root = os.path.normpath(
            destination_root
        )
        self.host_key = text_type(
            host_key or ""
        )

        self.stage_path = (
            self.destination_package +
            ".update_staged"
        )
        self.backup_path = (
            self.destination_package +
            ".update_backup"
        )
        self.journal_path = (
            self.destination_package +
            ".update_transaction.json"
        )

        self.destination_mod = os.path.join(
            self.destination_root,
            "MayaScriptToolbox.mod"
        )
        self.mod_stage_path = (
            self.destination_mod +
            ".update_staged"
        )
        self.mod_backup_path = (
            self.destination_mod +
            ".update_backup"
        )

    # ------------------------------------------------------------------
    # Journal
    # ------------------------------------------------------------------

    def _journal(self):
        if not os.path.isfile(
            self.journal_path
        ):
            return None

        try:
            with open(
                self.journal_path,
                "rb"
            ) as handle:
                payload = handle.read()

            if not isinstance(
                payload,
                text_type
            ):
                payload = payload.decode(
                    "utf-8"
                )

            data = json.loads(
                payload
            )
        except Exception as exc:
            raise UpdateError(
                "Update transaction journal is unreadable: {0}".format(
                    text_type(exc)
                )
            )

        if not isinstance(
            data,
            dict
        ):
            raise UpdateError(
                "Update transaction journal has an invalid format."
            )

        return data

    def _write_journal(
        self,
        phase,
        version="",
        mod_had_original=False
    ):
        data = {
            "transaction_version": TRANSACTION_VERSION,
            "phase": text_type(phase),
            "version": text_type(version or ""),
            "mod_had_original": bool(mod_had_original),
        }
        temp_path = (
            self.journal_path +
            ".tmp"
        )

        with open(
            temp_path,
            "wb"
        ) as handle:
            payload = json.dumps(
                data,
                sort_keys=True
            ).encode(
                "utf-8"
            )
            handle.write(
                payload
            )
            handle.flush()
            try:
                os.fsync(
                    handle.fileno()
                )
            except Exception:
                pass

        if os.path.exists(
            self.journal_path
        ):
            os.remove(
                self.journal_path
            )

        os.rename(
            temp_path,
            self.journal_path
        )
        return data

    def _remove_journal(self):
        for path in (
            self.journal_path + ".tmp",
            self.journal_path,
        ):
            if os.path.exists(
                path
            ):
                os.remove(
                    path
                )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_package(
        self,
        package_path,
        expected_version=None
    ):
        package_path = os.path.normpath(
            package_path
        )

        if not os.path.isdir(
            package_path
        ):
            raise UpdateError(
                "Staged Script Toolbox package is missing."
            )

        for relative_path in _REQUIRED_PACKAGE_FILES:
            path = os.path.join(
                package_path,
                relative_path
            )
            if not os.path.isfile(
                path
            ):
                raise UpdateError(
                    "Staged package is missing required file: {0}".format(
                        relative_path.replace(
                            os.sep,
                            "/"
                        )
                    )
                )

        for current_root, directories, filenames in os.walk(
            package_path
        ):
            if os.path.islink(
                current_root
            ):
                raise UpdateError(
                    "Staged package contains a symbolic-link directory."
                )

            for directory in directories:
                if os.path.islink(
                    os.path.join(
                        current_root,
                        directory
                    )
                ):
                    raise UpdateError(
                        "Staged package contains a symbolic-link directory."
                    )

            for filename in filenames:
                path = os.path.join(
                    current_root,
                    filename
                )

                if os.path.islink(
                    path
                ):
                    raise UpdateError(
                        "Staged package contains a symbolic-link file."
                    )

                if not filename.endswith(
                    ".py"
                ):
                    continue

                try:
                    with open(
                        path,
                        "rb"
                    ) as handle:
                        source = handle.read()

                    compile(
                        source,
                        path,
                        "exec"
                    )
                except Exception as exc:
                    relative = os.path.relpath(
                        path,
                        package_path
                    )
                    raise UpdateError(
                        "Staged Python source does not compile ({0}): {1}".format(
                            relative.replace(
                                os.sep,
                                "/"
                            ),
                            text_type(exc)
                        )
                    )

        version = self._read_staged_version(
            package_path
        )

        if expected_version:
            expected = text_type(
                expected_version
            ).strip()
            if expected.lower().startswith(
                "v"
            ):
                expected = expected[1:]

            if version != expected:
                raise UpdateError(
                    "Release version mismatch: metadata says {0}, staged package says {1}.".format(
                        expected,
                        version
                    )
                )

        return version

    def _read_staged_version(
        self,
        package_path
    ):
        constants_path = os.path.join(
            package_path,
            "constants.py"
        )

        with open(
            constants_path,
            "rb"
        ) as handle:
            content = handle.read()

        if not isinstance(
            content,
            text_type
        ):
            content = content.decode(
                "utf-8"
            )

        match = _VERSION_PATTERN.search(
            content
        )

        if not match:
            raise UpdateError(
                "Staged constants.py does not define PLUGIN_VERSION."
            )

        return text_type(
            match.group(1)
        ).strip()

    def validate_maya_module(
        self,
        path
    ):
        if not os.path.isfile(
            path
        ):
            raise UpdateError(
                "Staged Maya module file is missing."
            )

        with open(
            path,
            "rb"
        ) as handle:
            content = handle.read()

        if not isinstance(
            content,
            text_type
        ):
            content = content.decode(
                "utf-8"
            )

        if "PYTHONPATH +:= scripts" not in content:
            raise UpdateError(
                "Staged Maya module file does not expose the scripts path."
            )

        return True

    # ------------------------------------------------------------------
    # Recovery / cleanup
    # ------------------------------------------------------------------

    def _remove_path(
        self,
        path
    ):
        if os.path.isdir(
            path
        ) and not os.path.islink(
            path
        ):
            shutil.rmtree(
                path
            )
        elif os.path.exists(
            path
        ):
            os.remove(
                path
            )

    def _cleanup_staging(self):
        self._remove_path(
            self.stage_path
        )
        self._remove_path(
            self.mod_stage_path
        )

    def _cleanup_backups(self):
        self._remove_path(
            self.backup_path
        )
        self._remove_path(
            self.mod_backup_path
        )

    def recover(self):
        """Recover artifacts left by a previously interrupted transaction."""
        journal = self._journal()

        if journal is not None:
            phase = text_type(
                journal.get(
                    "phase",
                    ""
                )
            )

            if phase == "committed":
                try:
                    self.validate_package(
                        self.destination_package,
                        expected_version=journal.get(
                            "version"
                        ) or None
                    )
                except Exception:
                    self._rollback(
                        journal
                    )
                    return True

                self._cleanup_staging()
                self._cleanup_backups()
                self._remove_journal()
                return True

            self._rollback(
                journal
            )
            return True

        recovered = False

        # Compatibility recovery for artifacts produced by the legacy updater
        # before transaction journals existed.
        if (
            not os.path.exists(
                self.destination_package
            ) and
            os.path.isdir(
                self.backup_path
            )
        ):
            os.rename(
                self.backup_path,
                self.destination_package
            )
            recovered = True

        elif (
            os.path.isdir(
                self.destination_package
            ) and
            os.path.isdir(
                self.backup_path
            )
        ):
            # Keep a valid active tree; otherwise restore the known backup.
            try:
                self.validate_package(
                    self.destination_package
                )
                self._remove_path(
                    self.backup_path
                )
            except Exception:
                self._remove_path(
                    self.destination_package
                )
                os.rename(
                    self.backup_path,
                    self.destination_package
                )
            recovered = True

        if os.path.exists(
            self.stage_path
        ):
            self._remove_path(
                self.stage_path
            )
            recovered = True

        if os.path.exists(
            self.mod_stage_path
        ):
            self._remove_path(
                self.mod_stage_path
            )
            recovered = True

        return recovered

    def _rollback(
        self,
        journal
    ):
        rollback_errors = []

        try:
            if os.path.isdir(
                self.backup_path
            ):
                if os.path.exists(
                    self.destination_package
                ):
                    self._remove_path(
                        self.destination_package
                    )
                os.rename(
                    self.backup_path,
                    self.destination_package
                )
        except Exception as exc:
            rollback_errors.append(
                "package: {0}".format(
                    text_type(exc)
                )
            )

        try:
            mod_had_original = bool(
                journal.get(
                    "mod_had_original",
                    False
                )
            )

            if os.path.isfile(
                self.mod_backup_path
            ):
                if os.path.exists(
                    self.destination_mod
                ):
                    self._remove_path(
                        self.destination_mod
                    )
                os.rename(
                    self.mod_backup_path,
                    self.destination_mod
                )
            elif (
                self.host_key == "maya" and
                not mod_had_original and
                journal.get("phase") in (
                    "activated",
                    "committed",
                ) and
                os.path.exists(
                    self.destination_mod
                )
            ):
                self._remove_path(
                    self.destination_mod
                )
        except Exception as exc:
            rollback_errors.append(
                "Maya module: {0}".format(
                    text_type(exc)
                )
            )

        try:
            self._cleanup_staging()
        except Exception as exc:
            rollback_errors.append(
                "staging cleanup: {0}".format(
                    text_type(exc)
                )
            )

        if rollback_errors:
            raise UpdateError(
                "Update rollback is incomplete ({0}). Recovery artifacts were preserved at {1}.".format(
                    "; ".join(
                        rollback_errors
                    ),
                    self.journal_path
                )
            )

        self._remove_journal()
        return True

    # ------------------------------------------------------------------
    # Prepare / activate
    # ------------------------------------------------------------------

    def prepare(
        self,
        source_package,
        source_mod=None,
        expected_version=None
    ):
        self.recover()
        self._cleanup_staging()

        if os.path.exists(
            self.backup_path
        ):
            raise UpdateError(
                "Updater backup path is still occupied after recovery."
            )

        shutil.copytree(
            source_package,
            self.stage_path
        )

        version = self.validate_package(
            self.stage_path,
            expected_version=expected_version
        )

        if (
            self.host_key == "maya" and
            source_mod and
            os.path.isfile(
                source_mod
            )
        ):
            shutil.copy2(
                source_mod,
                self.mod_stage_path
            )
            self.validate_maya_module(
                self.mod_stage_path
            )

        return version

    def activate(
        self,
        version
    ):
        if not os.path.isdir(
            self.stage_path
        ):
            raise UpdateError(
                "Update transaction has no validated staged package."
            )

        mod_had_original = (
            self.host_key == "maya" and
            os.path.isfile(
                self.destination_mod
            )
        )

        journal = self._write_journal(
            "prepared",
            version=version,
            mod_had_original=mod_had_original
        )

        try:
            os.rename(
                self.destination_package,
                self.backup_path
            )

            journal = self._write_journal(
                "backup_moved",
                version=version,
                mod_had_original=mod_had_original
            )

            os.rename(
                self.stage_path,
                self.destination_package
            )

            if (
                self.host_key == "maya" and
                os.path.isfile(
                    self.mod_stage_path
                )
            ):
                if mod_had_original:
                    os.rename(
                        self.destination_mod,
                        self.mod_backup_path
                    )
                os.rename(
                    self.mod_stage_path,
                    self.destination_mod
                )

            journal = self._write_journal(
                "activated",
                version=version,
                mod_had_original=mod_had_original
            )

            self.validate_package(
                self.destination_package,
                expected_version=version
            )

            if (
                self.host_key == "maya" and
                os.path.exists(
                    self.destination_mod
                )
            ):
                self.validate_maya_module(
                    self.destination_mod
                )

            self._write_journal(
                "committed",
                version=version,
                mod_had_original=mod_had_original
            )

        except Exception as install_exc:
            try:
                self._rollback(
                    journal
                )
            except Exception as rollback_exc:
                raise UpdateError(
                    "Update failed ({0}); rollback also failed ({1}).".format(
                        text_type(install_exc),
                        text_type(rollback_exc)
                    )
                )

            if isinstance(
                install_exc,
                UpdateError
            ):
                raise

            raise UpdateError(
                text_type(
                    install_exc
                )
            )

        self._cleanup_backups()
        self._cleanup_staging()
        self._remove_journal()
        return True


def install_release(
    release,
    token=None,
    timeout=30
):
    """Install a verified release with the transaction-v2 pipeline."""
    install_metadata = _validate_installable_release(
        release
    )

    destination_package = package_directory()
    destination_root = repository_root()
    transaction = UpdateTransaction(
        destination_package,
        destination_root,
        host_key=HOST.key
    )
    recovered = False

    work_directory = tempfile.mkdtemp(
        prefix="script_toolbox_update_v2_"
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

    try:
        _download_file(
            install_metadata[
                "download_url"
            ],
            archive_path,
            token=token,
            timeout=timeout
        )
        _download_file(
            install_metadata[
                "checksum_url"
            ],
            checksum_path,
            token=token,
            timeout=timeout
        )
        _verify_checksum(
            archive_path,
            checksum_path
        )

        # Verification must complete before recovery, staging or activation can
        # touch any live update artifacts.
        recovered = transaction.recover()

        if not os.path.isdir(
            destination_package
        ):
            raise UpdateError(
                "Cannot find the installed Script Toolbox package."
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

        version = transaction.prepare(
            source_package,
            source_mod=source_mod,
            expected_version=install_metadata[
                "version"
            ] or None
        )
        transaction.activate(
            version
        )

        return {
            "installed": True,
            "version": install_metadata[
                "version"
            ] or version,
            "restart_required": False,
            "hot_reload_supported": True,
            "transaction_version": TRANSACTION_VERSION,
            "recovered_previous_transaction": bool(
                recovered
            ),
        }

    except Exception as exc:
        if isinstance(
            exc,
            UpdateError
        ):
            raise
        raise UpdateError(
            text_type(exc)
        )

    finally:
        try:
            shutil.rmtree(
                work_directory
            )
        except Exception:
            pass


__all__ = [
    "TRANSACTION_VERSION",
    "UpdateTransaction",
    "install_release",
]
