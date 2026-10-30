import sys
import types



def test_legacy_nuke_startup_registers_native_panel(monkeypatch):
    calls = []
    panel = object()
    runtime = types.ModuleType('script_toolbox.nuke_integration')
    def register_panel():
        calls.append('panel')
        return panel
    runtime.register_panel = register_panel
    monkeypatch.setitem(sys.modules, 'script_toolbox.nuke_integration', runtime)
    namespace = {}
    exec('import script_toolbox\nresult = script_toolbox.register_nuke_panel()', namespace)
    assert namespace['result'] is panel
    assert calls == ['panel']
