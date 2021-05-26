from periscope import gen_commands
from checks import http, dns, tcp
from typing import Type
import unittest
from parameterized import parameterized
from cli import parse_args

class CliTests(unittest.TestCase):
    @parameterized.expand([
        (['--http', 'https://httpstat.us/200'], [(http, 'https://httpstat.us/200', {})]),
        (['--tcp', '8.8.8.8:53'], [(tcp, '8.8.8.8:53', {})]),
        (['--dns', 'one.one.one.one=1.1.1.1,1.0.0.1'], [(dns, 'one.one.one.one=1.1.1.1,1.0.0.1', {})]),
        ([
            '--http', 'https://httpstat.us/200',
            '--tcp', '8.8.8.8:53',
            '--dns', 'one.one.one.one=1.1.1.1,1.0.0.1'
        ], [
            (http, 'https://httpstat.us/200', {}),
            (tcp, '8.8.8.8:53', {}),
            (dns, 'one.one.one.one=1.1.1.1,1.0.0.1', {})
        ]),
    ])
    def test_cli(self, params, expected_commands):
        args = parse_args(params)
        commands = list(gen_commands(args))
        for i in range(0, len(expected_commands)):
            self.assertEqual(commands[i][0].__name__, expected_commands[i][0].__name__)
            self.assertEqual(commands[i][1], expected_commands[i][1])
            self.assertDictContainsSubset(expected_commands[i][2], commands[i][2])

if __name__ == '__main__':
    unittest.main()