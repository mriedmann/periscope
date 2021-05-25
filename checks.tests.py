from typing import Type
import unittest
from checks import Ok, Err, ping, dns, http, tcp
from parameterized import parameterized

class PeriscopeTests(unittest.TestCase):
    @parameterized.expand([
        ("8.8.8.8", Ok),
        ("127.255.255.255", Err)
    ])
    def test_ping(self, target, return_type:Type):
        result = ping(target, ping_count=1)
        self.assertIsInstance(result, return_type)

    @parameterized.expand([
        ("8.8.8.8:53", Ok),
        ("127.255.255.255:53", Err),
        ("google.com:80", Ok),
        ("nodomain:80", Err)
    ])
    def test_tcp_ok(self, target, return_type:Type):
        result = tcp(target, tcp_timeout=1.0)
        self.assertIsInstance(result, return_type)
    
    @parameterized.expand([
        ("https://httpstat.us/200", Ok),
        ("https://httpstat.us/301", Ok),
        ("https://httpstat.us/404", Err),
        ("https://httpstat.us/500", Err)
    ])
    def test_tcp_ok(self, target, return_type:Type):
        result = http(target, ca_certs=None, http_method='HEAD')
        self.assertIsInstance(result, return_type)

    @parameterized.expand([
        ("dns.google=8.8.8.8,8.8.4.4", Ok),
        ("one.one.one.one=1.1.1.1,1.0.0.1", Ok),
        ("one.one.one.one=1.1.1.2", Err),
        ("notexisting.example", Err),
        ("Invalid$%&Name", Err)
    ])
    def test_dns(self, target, return_type:Type):
        result = dns(target)
        self.assertIsInstance(result, return_type)


if __name__ == '__main__':
    unittest.main()