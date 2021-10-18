import sys
import unittest
from io import StringIO

import yaml

from pipecheck.cmdfile import get_config_from_yamlfile


def stub_stdin(testcase_inst, inputs):
    stdin = sys.stdin

    def cleanup():
        sys.stdin = stdin

    testcase_inst.addCleanup(cleanup)
    sys.stdin = StringIO(inputs)


class CmdfileTests(unittest.TestCase):
    def setUp(self) -> None:
        with open("example.yaml", "r") as yaml_file:
            self.test_data = yaml.load(yaml_file, Loader=yaml.FullLoader)
        return super().setUp()

    def test_getconfig_file(self):
        data = get_config_from_yamlfile("example.yaml")
        self.assertEqual(self.test_data, data)

    def test_getconfig_stdio(self):
        with open("example.yaml", "r") as yaml_file:
            stub_stdin(self, yaml_file.read())
        data = get_config_from_yamlfile("-")
        self.assertEqual(self.test_data, data)
