import unittest
import importlib
import periscope
from parameterized import parameterized

class PeriscopeTests(unittest.TestCase):
    def setUp(self) -> None:
        importlib.reload(periscope)
        periscope.quiet = True
        return super().setUp()

    @parameterized.expand([
        ("8.8.8.8", 0),
        ("127.255.255.255", 1)
    ])
    def test_ping(self, target, ret_code):
        periscope.ping(target, ping_count=1)
        self.assertEqual(periscope.ret_code, ret_code)

    @parameterized.expand([
        ("8.8.8.8:53", 0),
        ("127.255.255.255:53", 1),
        ("google.com:80", 0),
        ("nodomain:80", 1)
    ])
    def test_tcp_ok(self, target, ret_code):
        periscope.tcp(target, tcp_timeout=1.0)
        self.assertEqual(periscope.ret_code, ret_code)
    
    @parameterized.expand([
        ("https://httpstat.us/200", 0),
        ("https://httpstat.us/301", 0),
        ("https://httpstat.us/404", 1),
        ("https://httpstat.us/500", 1)
    ])
    def test_tcp_ok(self, target, ret_code):
        periscope.http(target, ca_certs=None, http_method='HEAD')
        self.assertEqual(periscope.ret_code, ret_code)


if __name__ == '__main__':
    unittest.main()