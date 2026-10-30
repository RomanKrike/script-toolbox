# Dockable panels context

Branch: `dev` at `ea3833c` after PRs #157–#159. Parent Issue: #151. Stages: #152–#156 remain open for DCC acceptance.

Current design: `ui/debounced_main_window.py` owns the one active main window. The existing Runtime, ConfigStore, Item and Preset code remains shared. `ui/panel_container.py` is the QWidget passed to host APIs. It creates one child Runtime or an inert conflict message. Mode changes close the old Runtime after flushing pending data; no Qt widget is reparented between modes. A host-owned container is never directly deleted by the lifecycle controller.

Host entry points: Maya `integrations/maya_dock.py`; Houdini Package XML and `.pypanel` from `integrations/houdini.py`, with `houdini_integration.open_pane_tab`; Nuke `nuke_integration.register_panel` with stable Pane ID. `bootstrap.hot_reload_toolbox` reuses a live panel container.

Observed DCC feedback before PR #159: Maya, Nuke and Houdini panes were blank while ordinary windows loaded Item; Houdini showed the compact menu in a detached window and once crashed opening a pane. Root cause for the blank panes: `QMainWindow` sets `Qt.Window` even with a parent. PR #159 sets `Qt.Widget` in panel mode and asserts child ownership in real Qt tests. PR #158 fixed reopening a retained container and pinned the Houdini 20.5 Qt binding. Its crash has no log and remains unverified. All PR #159 checks passed on Linux and Windows; manual DCC retest is pending.

Next step: restart each DCC with current `dev`, open the ordinary window and Pane, switch modes, and verify Item and menu placement. Then test Workspace/Desktop restore and Reload Scripts. Record host versions and PASS/FAIL in #153–#156; investigate any Houdini crash from host logs.
