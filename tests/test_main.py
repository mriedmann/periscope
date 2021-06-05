import io
import unittest
import unittest.mock

from parameterized import parameterized

from pipecheck.__main__ import gen_call, print_result, run
from pipecheck.checks import Err, Ok, Warn, dns, http, ping, tcp

CRED = "\33[31m"
CGREEN = "\33[32m"
CYELLOW = "\33[33m"


class MainTests(unittest.TestCase):
    @parameterized.expand(
        [
            (Ok("Test Result"), CGREEN, ["OK", "Test Result"]),
            (Warn("Test Result"), CYELLOW, ["WARN", "Test Result"]),
            (Err("Test Result"), CRED, ["ERR", "Test Result"]),
        ]
    )
    @unittest.mock.patch("sys.stdout", new_callable=io.StringIO)
    def test_print_result(self, result, color, snippets, mock_stdout):
        print_result(result)
        print_text = mock_stdout.getvalue()
        self.assertIn(color, print_text)
        for text in snippets:
            self.assertIn(text, print_text)

    @parameterized.expand(
        [
            ({"type": "http", "url": "https://httpstat.us/200"}, {}, (http, {"url": "https://httpstat.us/200"})),
            ({"host": "8.8.8.8", "port": 53, "type": "tcp"}, {}, (tcp, {"host": "8.8.8.8", "port": 53})),
            (
                {"host": "1.1.1.1", "port": 53, "tcp_timeout": 0.1, "type": "tcp"},
                {},
                (tcp, {"host": "1.1.1.1", "port": 53, "tcp_timeout": 0.1}),
            ),
            ({"type": "ping", "host": "8.8.8.8"}, {}, (ping, {"host": "8.8.8.8"})),
            (
                {"ips": ["8.8.8.8", "8.8.4.4"], "name": "dns.google", "type": "dns"},
                {},
                (dns, {"ips": ["8.8.8.8", "8.8.4.4"], "name": "dns.google"}),
            ),
        ]
    )
    def test_gen_call(self, command, config, expected_call):
        call = gen_call(command, config)
        self.assertEqual(call[0].__name__, expected_call[0].__name__)
        self.assertDictEqual(call[1], expected_call[1])

    def test_run_success(self):
        exit_code = run([(http, {"url": "https://httpstat.us/200"})])
        self.assertEqual(exit_code, 0)

    def test_run_fail(self):
        exit_code = run([(http, {"url": "https://httpstat.us/500"})])
        self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
