# Configuration backup and recovery

Script Toolbox keeps the primary DCC configuration separate from the installed plugin package. Configuration writes are atomic and now also maintain a small rolling recovery history.

## Files

For a primary config such as:

```text
maya_script_toolbox.json
```

Script Toolbox may keep:

```text
maya_script_toolbox.json.bak1
maya_script_toolbox.json.bak2
maya_script_toolbox.json.bak3
```

`bak1` is the newest previous valid configuration and `bak3` is the oldest retained configuration.

Only the current primary config is copied during a save. Existing backup generations are moved to their next slot, which avoids multiplying the current frequent runtime-save I/O by three full file copies.

## Save safety

Before replacing an existing primary config, Script Toolbox reads, migrates and normalizes that existing file. If it cannot be read safely, the save is rejected with `ConfigRecoveryRequired` and the damaged primary file is not overwritten.

A valid primary config is rotated into the backup history before the new temporary file atomically replaces it.

Configs created by a newer unsupported schema remain protected by the migration layer and are never down-converted into backups or overwritten.

## Automatic recovery

If the primary config cannot be parsed or read and at least one valid backup exists:

1. backup generations are checked from newest to oldest;
2. the newest valid backup is selected;
3. the damaged primary file is copied to `*.corrupt` (or `*.corrupt.2`, etc. when needed);
4. the selected backup is validated again from the exact restore temp file;
5. the restore temp file atomically replaces the primary config;
6. the recovered document is returned to the runtime.

A damaged `bak1` is skipped automatically when a valid older generation exists.

If no valid backup exists, Script Toolbox raises `ConfigRecoveryRequired`. It does not substitute an empty default configuration, so normal runtime saves cannot silently destroy the damaged user file.

## Public core helpers

```python
from script_toolbox.core.config import backup_path
from script_toolbox.core.config import restore_config_backup
from script_toolbox.core.config import valid_backup_paths
```

These helpers are primarily intended for diagnostics and recovery tooling. Normal users do not need to call them during healthy operation.
