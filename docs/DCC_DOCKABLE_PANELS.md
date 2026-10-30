# Native dockable panels: implementation and acceptance

## Scope and impact

The shared `ScriptToolbox` QMainWindow still renders the Runtime, Editor entry points, Settings and status. The lifecycle in `ui/debounced_main_window.py` creates it as an ordinary window or as a child of a host-owned `ScriptToolboxPanel` QWidget. A mode change saves pending values and creates a fresh child; repeated opening in one mode activates the existing instance. A duplicate host container never builds a second Runtime. The previous Nuke dock implementation registered the QMainWindow class directly and had no lifecycle coordination; commit `68f69fb` removed it. This implementation registers the container instead.

Affected surfaces: Maya top menu and `workspaceControl`/legacy `dockControl`; Houdini Package resources (`python_panels/script_toolbox.pypanel`, `PaneTabTypeMenu.xml`, `MainMenuCommon.xml`); Nuke Pane and Script Toolbox menus; update reload; ConfigStore flush and host callbacks. The ordinary config schema and Item/Presets model are unchanged.

Risks: host restoration order, QObject deletion by each host, editor changes pending during a mode change, callbacks after host disposal, version-specific Qt and menu APIs. A transition stops if Editor has unapplied changes or persistence fails. Workspaces and user startup files are not rewritten by panel callbacks.

## Stages and checks

| Stage | Files | Acceptance evidence |
| --- | --- | --- |
| A, #152 | `ui/debounced_main_window.py`, `ui/panel_container.py`, `bootstrap.py` | Real Qt lifecycle test; pending value and view state retained; extra container inert |
| B, #153 | `integrations/maya_dock.py`, `integrations/maya_runtime.py` | Maya menu and stable control; Maya 2015/2017/2024/2025 smoke |
| C, #154 | `integrations/houdini.py`, `houdini_integration.py`, `ui/main_window.py` | XML/package contract; `+` menu, Desktop, collapsible row smoke |
| D, #155 | `nuke_integration.py`, `ui/panel_container.py` | Pane registration contract; Nuke 12 Workspace and Reload smoke |
| E, #156 | `bootstrap.py`, documentation, CI | Full tests, Python 2.7 syntax, review, install/repair/uninstall and narrow pane smoke |

The lifecycle refactor is necessary because the former `show()` destroyed every existing window before reopening and Nuke's removed panel registered the QMainWindow class directly. The host adapters need one shared ownership boundary so they can restore panes without constructing a second Runtime. No config migration is required. Recovery is to close the pane, reopen the ordinary window, and use the existing config backup/recovery flow if persistence reports an error; the feature branch can be reverted before merge without changing user schema.

## Manual smoke checklist

Run separately in Maya 2015, 2017, 2024, 2025; Houdini 19.5, 20.x, 21; Nuke 12 and available newer versions. Record PASS/FAIL/NOT RUN with host build, OS and Qt binding in Issues #153–#156.

1. Install or Repair twice; verify one menu entry and that other plugins' files are untouched.
2. Open ordinary ScriptToolbox twice; verify the second call activates the same window and current Item value remains.
3. Open Pane Tab; verify a native movable/dockable panel, same Item value, and no second active Runtime.
4. Open another panel through the host's own menu; verify the extra container shows a conflict message and does not run callbacks.
5. Switch window ↔ pane, close and reopen, and try with pending Item values and unapplied Editor changes.
6. Dock, undock, save Workspace/Desktop, restart host, and restore. Verify one active Runtime and saved values.
7. Reload Scripts while pane is docked; verify the container stays in place and Editor, Settings, callbacks and Presets still work.
8. Test Button, Slider, Checkbox, Color, Field, Folder and Table in a narrow pane; verify controls remain usable.
9. Update, Repair and Uninstall; verify idempotence, no orphan menu entries after restart and no foreign file changes.

Maya: verify first pane opens floating; Maya 2015 uses legacy dockControl and newer versions restore Workspace Control. Houdini: verify `+ → New Pane Tab Type → ScriptToolbox`, top menu Open Pane Tab, Desktop restore and the `▼ Editor Settings Help` row collapsing to `▶` and persisting. Nuke: verify native Pane menu alongside Viewer/Node Graph/Properties, stable layout restoration and Nuke 12 PySide2 behavior.

Automated tests and mocks are contract evidence only. A green CI run does not replace these DCC checks.
