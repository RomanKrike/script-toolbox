"""Exercise public installers in competing processes with real HTTP packages."""
import functools
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

import pytest

from script_toolbox.core import update_transaction
from test_update_transaction import _build_release_zip, _make_transaction


def worker():
    root, metadata, phase, ready, resume = sys.argv[2:]
    update_transaction.repository_root = lambda: root
    update_transaction.package_directory = lambda: os.path.join(root, "scripts", "script_toolbox")
    if phase != "none":
        original = update_transaction.UpdateTransaction._write_journal

        def write_and_pause(self, current_phase, *args, **kwargs):
            result = original(self, current_phase, *args, **kwargs)
            if current_phase == phase:
                Path(ready).write_text("ready")
                deadline = time.monotonic() + 90
                while not Path(resume).exists():
                    if time.monotonic() > deadline:
                        raise RuntimeError("Test controller did not release installer")
                    time.sleep(0.02)
            return result

        update_transaction.UpdateTransaction._write_journal = write_and_pause
    try:
        result = update_transaction.install_release(json.loads(Path(metadata).read_text()), timeout=10)
    except update_transaction.UpdateError as exc:
        print(json.dumps({"error": str(exc)}), flush=True)
        return 2
    print(json.dumps(result), flush=True)
    return 0


@pytest.mark.parametrize("phase,crash", [
    ("prepared", False),
    ("backup_moved", False),
    ("backup_moved", True),
])
def test_competing_public_installers_preserve_active_transaction(tmp_path, phase, crash):
    transaction, root, package = _make_transaction(tmp_path)
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    archive = _build_release_zip(downloads / "script-toolbox-2.0.0.zip", version="2.0.0")
    (downloads / (archive.name + ".sha256")).write_text(
        hashlib.sha256(archive.read_bytes()).hexdigest() + "  " + archive.name + "\n")
    requests = []

    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            return super().do_GET()

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0),
                                 functools.partial(Handler, directory=str(downloads)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = "http://127.0.0.1:{0}/".format(server.server_port)
    metadata = tmp_path / "release.json"
    metadata.write_text(json.dumps({
        "version": "2.0.0", "asset_name": archive.name,
        "download_url": base_url + archive.name,
        "checksum_url": base_url + archive.name + ".sha256",
    }))
    ready, resume = tmp_path / "ready", tmp_path / "resume"
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "scripts")
    environment["NO_PROXY"] = "*"
    environment["no_proxy"] = "*"

    def command(pause):
        return [sys.executable, str(Path(__file__).resolve()), "worker", str(root),
                str(metadata), pause, str(ready), str(resume)]

    first = None
    try:
        first = subprocess.Popen(command(phase), env=environment,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        deadline = time.monotonic() + 30
        while not ready.exists() and first.poll() is None and time.monotonic() < deadline:
            time.sleep(0.02)
        if not ready.exists():
            first.kill()
            output, error = first.communicate()
            pytest.fail("Installer did not reach barrier: " + repr((output, error)))

        journal_before = Path(transaction.journal_path).read_bytes()
        staged_before = (Path(transaction.stage_path) / "marker.py").read_bytes()
        live_before = package.exists()
        backup_before = Path(transaction.backup_path).exists()
        assert len(requests) == 2
        second = subprocess.run(command("none"), env=environment, capture_output=True, timeout=30)
        assert second.returncode == 2, (second.stdout, second.stderr)
        assert "already running" in json.loads(second.stdout)["error"]
        assert len(requests) == 2  # Rejected before download or recovery.
        assert Path(transaction.journal_path).read_bytes() == journal_before
        assert (Path(transaction.stage_path) / "marker.py").read_bytes() == staged_before
        assert package.exists() == live_before
        assert Path(transaction.backup_path).exists() == backup_before

        if crash:
            first.kill()
            first.communicate(timeout=10)
            recovered = subprocess.run(command("none"), env=environment,
                                       capture_output=True, timeout=30)
            assert recovered.returncode == 0, (recovered.stdout, recovered.stderr)
            result = json.loads(recovered.stdout)
            assert result["recovered_previous_transaction"] is True
            assert len(requests) == 4
        else:
            resume.write_text("continue")
            output, error = first.communicate(timeout=30)
            assert first.returncode == 0, (output, error)
            result = json.loads(output)
        assert result["installed"] is True
        assert result["version"] == "2.0.0"
        assert (package / "marker.py").read_text() == "MARKER = '2.0.0'\n"
        assert not (package / "old_only.py").exists()
        assert not Path(transaction.stage_path).exists()
        assert not Path(transaction.backup_path).exists()
        assert not Path(transaction.journal_path).exists()
    finally:
        if first is not None and first.poll() is None:
            first.kill()
            first.communicate(timeout=10)
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


if __name__ == "__main__":
    sys.exit(worker())
