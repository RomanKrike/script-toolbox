# -*- coding: utf-8 -*-
"""Read-only entry point for isolated DCC filesystem discovery."""
from __future__ import print_function

import json
import os
import sys


def main():
    os.environ["SCRIPT_TOOLBOX_DISCOVERY_WORKER"] = "1"
    scripts = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, scripts)
    from script_toolbox.integrations.manager import DccIntegrationManager
    from script_toolbox.integrations.discovery_process import encode_snapshot
    with open(sys.argv[1], "rb") as handle:
        request = json.loads(handle.read().decode("utf-8"))
    manager = DccIntegrationManager.from_discovery_request(request)
    snapshot = encode_snapshot(manager.scan_details())
    with open(sys.argv[2], "w") as handle:
        json.dump(snapshot, handle)
    return 0


if __name__ == "__main__":
    sys.exit(main())
