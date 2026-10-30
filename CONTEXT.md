# Dockable panels context

Branch: `feature/dcc-dockable-panels` from `origin/dev` `55235bb`. Parent Issue: #151. Stages: #152–#156.

Current design: `ui/debounced_main_window.py` owns the one active main window. The existing Runtime, ConfigStore, Item and Preset code remains shared. `ui/panel_container.py` is the QWidget passed to host APIs. It creates one child Runtime or an inert conflict message. Mode changes close the old Runtime after flushing pending data; no Qt widget is reparented between modes. A host-owned container is never directly deleted by the lifecycle controller.

Host entry points: Maya `integrations/maya_dock.py`; Houdini Package XML and `.pypanel` from `integrations/houdini.py`, with `houdini_integration.open_pane_tab`; Nuke `nuke_integration.register_panel` with stable Pane ID. `bootstrap.hot_reload_toolbox` reuses a live panel container.

Known limits: real DCC acceptance is NOT RUN in this workspace. Need validate Maya 2015/2017/2024/2025, Houdini 19.5/20/21, and Nuke 12 directly. Verify workspace/Desktop restoration, Reload Scripts, and install/repair/uninstall in host before merge. Qt lifecycle tests passed in CI on Linux and Windows at `50c7307`. Local full suite: 891 passed, 71 skipped, 8 failed on Windows due to host permissions and process policies; the CI suite passed.

Next step: run the manual smoke checklist in `docs/DCC_DOCKABLE_PANELS.md` in each available DCC and record results in #153–#156. Keep draft PR #157 open and do not merge until acceptance is complete.
