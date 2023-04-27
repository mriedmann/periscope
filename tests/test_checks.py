import unittest
from typing import Type

from parameterized import parameterized

from pipecheck.api import Err, Ok
from pipecheck.checks.icmp import PingProbe
from pipecheck.checks.tcp import TcpProbe
from pipecheck.checks.mysql import MysqlProbe


class CheckTests(unittest.TestCase):
    @parameterized.expand([("127.0.0.1", Ok), ("127.255.255.255", Err)])
    def test_ping(self, target, return_type: Type):
        result = PingProbe(host=target, ping_count=1)()
        self.assertIsInstance(result, return_type, result.msg)

    @parameterized.expand([("8.8.8.8", 53, Ok), ("127.255.255.255", 53, Err), ("google.com", 80, Ok), ("nodomain", 80, Err)])
    def test_tcp(self, target, port, return_type: Type):
        result = TcpProbe(host=target, port=port, tcp_timeout=1.0)()
        self.assertIsInstance(result, return_type, result.msg)

    @parameterized.expand([
        ("db4free.net", 3306, "pipecheck", "x9$9nvKL9Y6jCem", Ok),
        ("db4free.net", 33300, "pipecheck", "x9$9nvKL9Y6jCem", Err),
        ("localhost", 3306, "pipecheck", "x9$9nvKL9Y6jCem", Err),
        ("db4free.net", 3306, "pipecheck_err", "x9$9nvKL9Y6jCem", Err),
        ("db4free.net", 3306, "pipecheck", "WRONGPW", Err),
    ])
    def test_mysql(self, target, port, user, password, return_type: Type):
        result = MysqlProbe(host=target, port=port, user=user, password=password)()
        self.assertIsInstance(result, return_type, result.msg)


if __name__ == "__main__":
    unittest.main()
