import sys
import types
import warnings

import script_toolbox


def test_legacy_nuke_startup_registers_normal_menu(monkeypatch):
    calls = []
    menu = object()
    runtime = types.ModuleType('script_toolbox.nuke_integration')
    def register_menu():
        calls.append('menu')
        return menu
    runtime.register_menu = register_menu
    monkeypatch.setitem(sys.modules, 'script_toolbox.nuke_integration', runtime)
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter('always')
        # Execute an existing user's startup line, not a private helper.
        namespace = {}
        exec('import script_toolbox\nresult = script_toolbox.register_nuke_panel()', namespace)
    assert namespace['result'] is menu
    assert calls == ['menu']
    assert len(captured) == 1
    assert captured[0].category is DeprecationWarning
    assert 'register_nuke_menu()' in str(captured[0].message)
