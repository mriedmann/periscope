import unittest
from typing import Type

from parameterized import parameterized

from pipecheck.api import Err, Ok
from pipecheck.checks import ping, tcp


class CheckTests(unittest.TestCase):
    @parameterized.expand([("127.0.0.1", Ok), ("127.255.255.255", Err)])
    def test_ping(self, target, return_type: Type):
        result = ping(target, ping_count=1)
        self.assertIsInstance(result, return_type, result.msg)

    @parameterized.expand([("8.8.8.8", 53, Ok), ("127.255.255.255", 53, Err), ("google.com", 80, Ok), ("nodomain", 80, Err)])
    def test_tcp(self, target, port, return_type: Type):
        result = tcp(target, port, tcp_timeout=1.0)
        self.assertIsInstance(result, return_type, result.msg)


if __name__ == "__main__":
    unittest.main()
