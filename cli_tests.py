from checks import http, dns, tcp
import unittest
from parameterized import parameterized
from cli import parse_args, gen_commands_from_args

class CliTests(unittest.TestCase):
    @parameterized.expand([
        (['--http', 'https://httpstat.us/200'], [(http, { 'url': 'https://httpstat.us/200' })]),
        (['--tcp', '8.8.8.8:53'], [(tcp, { 'host': '8.8.8.8', 'port': 53 })]),
        (['--dns', 'one.one.one.one=1.1.1.1,1.0.0.1'], [(dns, { 'name': 'one.one.one.one', 'ips': ['1.1.1.1', '1.0.0.1'] })]),
        ([
            '--http', 'https://httpstat.us/200',
            '--tcp', '8.8.8.8:53',
            '--dns', 'one.one.one.one=1.1.1.1,1.0.0.1'
        ], [
            (http, { 'url': 'https://httpstat.us/200' }),
            (tcp, { 'host': '8.8.8.8', 'port': 53 }),
            (dns, { 'name': 'one.one.one.one', 'ips': ['1.1.1.1', '1.0.0.1'] })
        ]),
    ])
    def test_cli(self, params, expected_commands):
        args = parse_args(params)
        commands = list(gen_commands_from_args(args))
        for i in range(0, len(expected_commands)):
            self.assertEqual(commands[i][0].__name__, expected_commands[i][0].__name__)
            self.assertTrue(expected_commands[i][1].items() <= commands[i][1].items())

if __name__ == '__main__':
    unittest.main()