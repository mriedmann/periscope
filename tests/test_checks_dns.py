import unittest
from typing import Type

from parameterized import parameterized

from pipecheck.api import Err, Ok
from pipecheck.checks import dns


class CheckDnsTests(unittest.TestCase):

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
