import json
import os
import sys
import threading
import time

import pytest

from script_toolbox.integrations.discovery_process import (
    DiscoveryError, decode_snapshot, encode_snapshot, scan_in_process)
from script_toolbox.integrations.base import DccInstallation, IntegrationStatus
from script_toolbox.integrations.manager import DccIntegrationManager
from script_toolbox.integrations.maya import MayaAdapter


def test_isolated_scan_roundtrip_preserves_profiles_and_status(tmp_path):
    root = tmp_path / 'maya'
    (root / '2025').mkdir(parents=True)
    adapter = MayaAdapter(user_root=str(root), program_files=str(tmp_path / 'absent'),
                          config_path=str(tmp_path / 'settings.json'))
    manager = DccIntegrationManager(adapters=[adapter])
    expected = encode_snapshot(manager.scan_details())
    actual = scan_in_process(manager.discovery_request(), command=[sys.executable], timeout=5)
    assert encode_snapshot(actual) == expected
    assert actual['installations']['maya'][0].profile_id == 'default'


def test_snapshot_preserves_custom_profile_and_options():
    target = DccInstallation('maya', 'Maya', '2025', profile_id='custom',
                             profile_label='Project', profile_root='/profiles/project')
    target.scanned_status = IntegrationStatus('partial', shelf=True, message='needs menu')
    target.scanned_options = {'shelf': True, 'main_menu': False}
    snapshot = {'roots': {'maya': [{'id': 'custom'}]}, 'installations': {'maya': [target]}}
    decoded = decode_snapshot(encode_snapshot(snapshot))['installations']['maya'][0]
    assert decoded.profile_id == 'custom'
    assert decoded.scanned_status.shelf
    assert decoded.scanned_status.message == 'needs menu'
    assert decoded.scanned_options == target.scanned_options


def sleeping_worker(tmp_path):
    path = tmp_path / 'blocked.py'
    path.write_text('import time\ntime.sleep(30)\n')
    return str(path)


def test_discovery_timeout_kills_blocked_process(tmp_path):
    start = time.monotonic()
    with pytest.raises(DiscoveryError, match='timed out'):
        scan_in_process({}, command=[sys.executable], worker_path=sleeping_worker(tmp_path), timeout=0.2)
    assert time.monotonic() - start < 3


def test_discovery_cancellation_kills_blocked_process(tmp_path):
    event = threading.Event()
    timer = threading.Timer(0.1, event.set)
    timer.start()
    start = time.monotonic()
    try:
        with pytest.raises(DiscoveryError, match='cancelled'):
            scan_in_process({}, command=[sys.executable], worker_path=sleeping_worker(tmp_path),
                            cancel_event=event, timeout=5)
    finally:
        timer.join()
    assert time.monotonic() - start < 3


def test_worker_never_imports_host_apis(tmp_path):
    import subprocess
    scripts = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts')
    env = dict(os.environ, PYTHONPATH=scripts, SCRIPT_TOOLBOX_DISCOVERY_WORKER='1')
    code = '''
import sys
import script_toolbox
assert script_toolbox.__host__ == "standalone"
from script_toolbox.integrations.manager import DccIntegrationManager
assert not any(name in sys.modules for name in ("maya.cmds", "nuke", "hou", "PySide", "PySide2", "PySide6"))
'''
    result = subprocess.run([sys.executable, '-c', code], env=env, capture_output=True, timeout=5)
    assert result.returncode == 0, result.stderr


def test_discovery_nonzero_exit_is_reported(tmp_path):
    path = tmp_path / 'failed.py'
    path.write_text('raise RuntimeError("unreadable profile")')
    with pytest.raises(DiscoveryError, match='unreadable profile'):
        scan_in_process({}, command=[sys.executable], worker_path=str(path), timeout=5)


def test_all_default_adapters_can_be_serialized():
    manager = DccIntegrationManager()
    restored = DccIntegrationManager.from_discovery_request(json.loads(json.dumps(manager.discovery_request())))
    assert [a.key for a in restored.adapters()] == [a.key for a in manager.adapters()]
