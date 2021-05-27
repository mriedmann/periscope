import io
from periscope.cli import parse_args
import unittest
import unittest.mock
from parameterized import parameterized
from periscope.checks import Ok, Warn, Err, http, tcp, dns, ping
from periscope.__main__ import print_results, gen_calls, run

CRED = '\33[31m'
CGREEN = '\33[32m'
CYELLOW = '\33[33m'

class MainTests(unittest.TestCase):

    @parameterized.expand([
        (Ok("Test Result"), CGREEN, ["OK", "Test Result"]),
        (Warn("Test Result"), CYELLOW, ["WARN", "Test Result"]),
        (Err("Test Result"), CRED, ["ERR", "Test Result"]),
    ])
    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    def test_print_results(self, result, color, snippets, mock_stdout):
        print_results([result])
        print_text = mock_stdout.getvalue()
        self.assertIn(color, print_text)
        for text in snippets:
            self.assertIn(text, print_text)

    @parameterized.expand([
        ([
            {'type': 'http', 'url': 'https://httpstat.us/200'}
        ], {}, [
            (http, {'url': 'https://httpstat.us/200'})
        ]), ([
            {'host': '8.8.8.8', 'port': 53, 'type': 'tcp'},
            {'host': '1.1.1.1', 'port': 53, 'tcp_timeout': 0.1, 'type': 'tcp'},
            {'type': 'ping', 'host': '8.8.8.8'},
            {'ips': ['8.8.8.8', '8.8.4.4'], 'name': 'dns.google', 'type': 'dns'},
        ], {}, [
            (tcp, {'host': '8.8.8.8', 'port': 53}),
            (tcp, {'host': '1.1.1.1', 'port': 53, 'tcp_timeout': 0.1}),
            (ping, {'host': '8.8.8.8'}),
            (dns, {'ips': ['8.8.8.8', '8.8.4.4'], 'name': 'dns.google'}),
        ])
    ])
    def test_gen_calls(self, commands, config, expected_calls):
        calls = list(gen_calls(commands, config))
        for i in range(0, len(calls)):
            self.assertEqual(calls[i][0].__name__, expected_calls[i][0].__name__)
            self.assertDictEqual(calls[i][1], expected_calls[i][1])

    def test_run_example(self):
        exit_code = run(parse_args(['-f', 'example.yaml']))
        self.assertEqual(exit_code, 0)

    def test_run_fail(self):
        exit_code = run(parse_args(['--http', 'https://httpstat.us/500']))
        self.assertEqual(exit_code, 1)


if __name__ == '__main__':
    unittest.main()
