from checks import http, dns, tcp
import unittest
from parameterized import parameterized
from cli import parse_args, get_commands_and_config_from_args

class CliTests(unittest.TestCase):
    @parameterized.expand([
        (['--http', 'https://httpstat.us/200'], [{ 'type':'http', 'url': 'https://httpstat.us/200' }]),
        (['--tcp', '8.8.8.8:53'], [{ 'type': 'tcp', 'host': '8.8.8.8', 'port': 53 }]),
        (['--dns', 'one.one.one.one=1.1.1.1,1.0.0.1'], [{ 'type': 'dns', 'name': 'one.one.one.one', 'ips': ['1.1.1.1', '1.0.0.1'] }]),
        (['--ping', '8.8.8.8'], [{ 'type': 'ping', 'host': '8.8.8.8' }]),
        (['--ping', '8.8.8.8', '1.1.1.1'], [{ 'type': 'ping', 'host': '8.8.8.8' },{ 'type': 'ping', 'host': '1.1.1.1' }]),
        ([
            '--http', 'https://httpstat.us/200',
            '--tcp', '8.8.8.8:53',
            '--dns', 'one.one.one.one=1.1.1.1,1.0.0.1'
        ], [
            ({ "type": "http", 'url': 'https://httpstat.us/200' }),
            ({ "type": "tcp", 'host': '8.8.8.8', 'port': 53 }),
            ({ "type": "dns", 'name': 'one.one.one.one', 'ips': ['1.1.1.1', '1.0.0.1'] })
        ]),
    ])
    def test_cli(self, params, expected_commands):
        args = parse_args(params)
        (commands, _) = list(get_commands_and_config_from_args(args))
        for i in range(0, len(expected_commands)):
            self.assertTrue(expected_commands[i].items() <= commands[i].items())

if __name__ == '__main__':
    unittest.main()