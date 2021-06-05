import unittest
from typing import Type

from parameterized import parameterized

from pipecheck.checks import Err, Ok, Warn, dns, http, ping, tcp


class CheckTests(unittest.TestCase):
    @parameterized.expand([("127.0.0.1", Ok), ("127.255.255.255", Err)])
    def test_ping(self, target, return_type: Type):
        result = ping(target, ping_count=1)
        self.assertIsInstance(result, return_type, result.msg)

    @parameterized.expand([("8.8.8.8", 53, Ok), ("127.255.255.255", 53, Err), ("google.com", 80, Ok), ("nodomain", 80, Err)])
    def test_tcp(self, target, port, return_type: Type):
        result = tcp(target, port, tcp_timeout=1.0)
        self.assertIsInstance(result, return_type, result.msg)

    @parameterized.expand(
        [
            ("https://httpstat.us/200", Ok),
            ("https://httpstat.us/301", Ok),
            ("https://httpstat.us/404", Err),
            ("https://httpstat.us/500", Err),
            ("https://self-signed.badssl.com/", Warn),
        ]
    )
    def test_http_nocert(self, target, return_type: Type):
        result = http(target, insecure=True)
        self.assertIsInstance(result, return_type, result.msg)

    @parameterized.expand(
        [
            ("https://httpstat.us/200", Ok),
            ("https://httpstat.us/500", Err),
            ("https://self-signed.badssl.com/", Err),
        ]
    )
    def test_http_certcheck(self, target, return_type: Type):
        result = http(target)
        self.assertIsInstance(result, return_type, result.msg)

    @parameterized.expand(
        [
            ("https://httpstat.us/200", [200], Ok),
            ("https://httpstat.us/300", [200, 301], Err),
            ("https://httpstat.us/400", [200, 400], Ok),
        ]
    )
    def test_http_status(self, target, status, return_type: Type):
        result = http(target, status)
        self.assertIsInstance(result, return_type, result.msg)

    @parameterized.expand(
        [
            ("dns.google", ["8.8.8.8", "8.8.4.4"], Ok),
            ("dns.google", ["8.8.0.0/16"], Ok),
            ("dns.google", ["8.0.0.0/8", "8.8.0.0/8"], Ok),
            ("one.one.one.one", ["1.1.1.1", "1.0.0.1"], Ok),
            ("one.one.one.one", ["1.1.1.0/24", "1.0.0.1"], Ok),
            ("one.one.one.one", ["1.1.1.2"], Err),
            ("dns.google", ["7.0.0.0/8", "9.9.9.0/24"], Err),
            ("notexisting.example", None, Err),
            ("Invalid$%&Name", None, Err),
        ]
    )
    def test_dns(self, target, ips, return_type: Type):
        result = dns(target, ips)
        self.assertIsInstance(result, return_type, result.msg)


if __name__ == "__main__":
    unittest.main()
