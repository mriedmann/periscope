from io import StringIO
import unittest
from parameterized import parameterized
import yaml
from periscope.cmdfile import get_commands_from_config, get_config_from_yamlfile
import sys

def stub_stdin(testcase_inst, inputs):
    stdin = sys.stdin

    def cleanup():
        sys.stdin = stdin

    testcase_inst.addCleanup(cleanup)
    sys.stdin = StringIO(inputs)

class CmdfileTests(unittest.TestCase):
    def setUp(self) -> None:
        with open("example.yaml", 'r') as yaml_file:
            self.test_data = yaml.load(yaml_file, Loader=yaml.FullLoader)
        return super().setUp()

    def test_getconfig_file(self):
        data = get_config_from_yamlfile("example.yaml")
        self.assertEqual(self.test_data, data)

    def test_getconfig_stdio(self):
        with open("example.yaml", 'r') as yaml_file:
            stub_stdin(self, yaml_file.read())
        data = get_config_from_yamlfile("-")
        self.assertEqual(self.test_data, data)

    @parameterized.expand([
        ({"type": "ping", "host": "8.8.8.8"}, [{"type": "ping", "host": "8.8.8.8"}]),
        ({"a": {"type": "ping", "host": "8.8.8.8"}, "b": {"type": "tcp", "host": "8.8.8.8", "port": 53}},
         [{"type": "ping", "host": "8.8.8.8"}, {"type": "tcp", "host": "8.8.8.8", "port": 53}]),
        ({"a": {"b": {"c": {"type": "ping", "host": "8.8.8.8"}}}}, [{"type": "ping", "host": "8.8.8.8"}]),
        ({"a": {"type": "ping", "host": "8.8.8.8", "b": {"type": "tcp", "host": "8.8.8.8", "port": 53}}},
         [{"type": "ping", "host": "8.8.8.8"}]),
    ])
    def test_getcommands(self, config, expected_commands):
        commands = get_commands_from_config(config)
        for i in range(0, len(expected_commands)):
            self.assertEqual(commands[i], expected_commands[i])
