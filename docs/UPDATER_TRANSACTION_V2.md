# Updater Transaction v2

STEP 12 replaces the active update-install path with a staged, validated,
journaled filesystem transaction. Update discovery/download/checksum/archive
helpers remain in `core.updater`; the single production install engine lives in
`core.update_transaction`.

## Why v2 exists

The legacy installer backed up the live `script_toolbox` directory and then
copied the replacement directly into the live path. Ordinary exceptions were
rolled back, but a partial copy could exist between the backup rename and the
end of `copytree()`.

Transaction v2 minimizes the mutation window:

1. validate that release metadata names the official Script Toolbox package and a matching checksum asset;
2. download the package and checksum;
3. verify the package SHA-256;
4. only after verification, recover artifacts from an earlier interrupted transaction;
5. safely extract the archive;
6. copy the candidate package to a sibling `.update_staged` directory;
7. validate the staged tree completely;
8. write a transaction journal;
9. rename the live package to `.update_backup`;
10. rename the already-complete staged tree into the live path;
11. activate the staged Maya module file when applicable;
12. validate the live tree again after activation;
13. mark the journal committed;
14. remove backup/staging/journal artifacts.

Checksum verification deliberately precedes transaction recovery and staging. A
missing official package, missing checksum, failed checksum download, or digest
mismatch therefore cannot modify the live package or its recovery artifacts.
GitHub's generated source zipball is not an installation fallback.

The staging and live package directories are siblings. This keeps activation
renames on the same filesystem and avoids copying package files into the live
directory during the activation phase.

## Validation contract

Before the live tree is touched, the staged package must:

- come from the expected official package asset for the selected update channel;
- pass the required SHA-256 verification;
- contain the required modular package files;
- expose `PLUGIN_VERSION` from `constants.py`;
- match the version advertised by release metadata when one is supplied;
- compile every `.py` file with the Python interpreter running the DCC;
- contain no symbolic-link files or directories.

For Maya, a staged `MayaScriptToolbox.mod` is also validated before activation
and must expose `PYTHONPATH +:= scripts`.

This is intentionally stronger than importing the staged package. Importing
would execute arbitrary package initialization during validation and can also
pull modules into `sys.modules` before the transaction commits.

## Journal and recovery

The sibling journal is:

`script_toolbox.update_transaction.json`

It records transaction version, phase, release version and whether Maya had an
existing module file. Important phases are:

- `prepared` — staging is validated; live package is still intact;
- `backup_moved` — previous package is retained at `.update_backup`;
- `activated` — staged package/module are active but post-validation is not yet
  committed;
- `committed` — post-activation validation succeeded; remaining artifacts are
  cleanup-only.

An uncommitted journal is recovered conservatively by restoring the backup.
A committed journal keeps the new package if it still validates and only
cleans stale transaction artifacts. Legacy `.update_backup` artifacts created
before journals existed are also recognized.

If rollback itself cannot complete, v2 does not erase the remaining recovery
artifacts. The raised `UpdateError` identifies the journal path so the failed
transaction remains diagnosable/recoverable rather than silently discarding
the last known-good copy.

## Compatibility

The active `UpdateInstallThread` imports `install_release` from
`core.update_transaction`. `core.updater.install_release` remains only as a thin
compatibility wrapper that delegates to the same transaction-v2 installer; no
second public filesystem installation flow remains. Update checks and release
metadata continue to use `core.updater`.

The transaction implementation keeps Python 2.7 syntax and is exercised by a
dedicated Python 2.7 filesystem smoke test for Maya 2015 compatibility.

No config schema, runtime renderer, Links/reference-remapping, editor-history,
or host-callback semantics are changed by STEP 12.
