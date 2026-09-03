# -*- coding: utf-8 -*-

# Keep this package initializer intentionally light.
# Some core modules (for example updater.py) are Maya-independent and are
# exercised by CI outside Maya. Import Maya integration modules explicitly:
#
#     from script_toolbox.core.config import load_config
#     from script_toolbox.core.executor import execute_script
