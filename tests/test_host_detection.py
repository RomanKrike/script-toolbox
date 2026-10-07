# -*- coding: utf-8 -*-
"""Run the real host import graph in fresh Python 2.7/3.x interpreters."""
from __future__ import print_function

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")


class HostDetectionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp(prefix="stb_host_detection_")

    def tearDown(self):
        shutil.rmtree(self.directory)

    def write(self, relative, content):
        path = os.path.join(self.directory, *relative.split("/"))
        folder = os.path.dirname(path)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        with open(path, "w") as handle:
            handle.write(content)

    def run_python(self, code):
        environment = dict(os.environ)
        environment.pop("SCRIPT_TOOLBOX_DISCOVERY_WORKER", None)
        environment["PYTHONPATH"] = os.pathsep.join([self.directory, SCRIPTS])
        process = subprocess.Popen([sys.executable, "-c", code], cwd=self.directory,
                                   env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        return process.returncode, output.decode("utf-8", "replace"), error.decode("utf-8", "replace")

    def assert_import_failure(self, message):
        code, output, error = self.run_python("import script_toolbox")
        self.assertNotEqual(code, 0, output)
        self.assertIn(message, error)

    def test_absent_host_returns_none(self):
        code, output, error = self.run_python(
            "from script_toolbox.hosts import _import_host_module; "
            "assert _import_host_module('_stb_missing_host_27941') is None")
        self.assertEqual(code, 0, output + error)

    def test_maya_initializer_dependency_error_propagates(self):
        self.write("maya/__init__.py", "import _stb_missing_maya_dependency_27941\n")
        self.assert_import_failure("_stb_missing_maya_dependency_27941")

    def test_maya_commands_dependency_error_propagates(self):
        self.write("maya/__init__.py", "")
        self.write("maya/cmds.py", "import _stb_missing_commands_dependency_27941\n")
        self.assert_import_failure("_stb_missing_commands_dependency_27941")

    def test_present_maya_without_commands_is_an_error(self):
        self.write("maya/__init__.py", "")
        self.assert_import_failure("cmds")

    def test_nuke_dependency_error_propagates(self):
        self.write("nuke.py", "import _stb_missing_nuke_dependency_27941\n")
        self.assert_import_failure("_stb_missing_nuke_dependency_27941")

    def test_houdini_native_load_error_propagates(self):
        self.write("hou.py", "raise ImportError('Houdini native library could not load')\n")
        self.assert_import_failure("Houdini native library could not load")

    def test_present_adapter_failure_propagates(self):
        self.write("maya/__init__.py", "")
        self.write("maya/cmds.py", "")
        self.write("maya/mel.py", "raise ImportError('Maya adapter dependency failed')\n")
        self.assert_import_failure("Maya adapter dependency failed")

    def test_discovery_worker_does_not_import_broken_hosts(self):
        self.write("maya/__init__.py", "raise RuntimeError('must not import host')\n")
        code, output, error = self.run_python(
            "import os; os.environ['SCRIPT_TOOLBOX_DISCOVERY_WORKER']='1'; "
            "import script_toolbox; assert script_toolbox.__host__ == 'standalone'")
        self.assertEqual(code, 0, output + error)


if __name__ == "__main__":
    unittest.main()
